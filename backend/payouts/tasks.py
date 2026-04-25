import random
import time
import logging

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import Payout, LedgerEntry
from .state_machine import transition_payout

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
#  Simulation helper
# ──────────────────────────────────────────────

def _simulate_bank(payout_id: str) -> str:
    """
    Simulates a bank settlement call.
    Returns: 'success' (70%), 'failed' (20%), 'hang' (10%)
    """
    r = random.random()
    if r < 0.70:
        return 'success'
    elif r < 0.90:
        return 'failed'
    else:
        # Simulate a hung call — just sleep briefly, then return nothing
        logger.info(f'Payout {payout_id}: bank call hanging')
        time.sleep(0.5)
        return 'hang'


# ──────────────────────────────────────────────
#  Task: process a single payout
# ──────────────────────────────────────────────

@shared_task(bind=True, max_retries=0, name='payouts.tasks.process_single_payout')
def process_single_payout(self, payout_id: str):
    """
    Moves one payout through the lifecycle.

    State transitions:
        pending     → processing
        processing  → completed   (70% chance)
        processing  → failed      (20% chance)
        processing  → stays hung  (10% chance, retried later by retry_stuck_payouts)

    Atomicity guarantee:
        The final state transition and its balancing ledger entry (debit or release)
        happen inside a single DB transaction with SELECT FOR UPDATE on the payout row.
        This prevents double-processing if two workers somehow pick the same payout.
    """
    logger.info(f'Processing payout {payout_id}')

    # ── Step 1: transition pending → processing ──
    with transaction.atomic():
        try:
            payout = Payout.objects.select_for_update().get(id=payout_id)
        except Payout.DoesNotExist:
            logger.error(f'Payout {payout_id} not found')
            return

        # Guard: only process pending payouts here
        if payout.status == Payout.Status.PENDING:
            transition_payout(payout, 'processing')

        elif payout.status == Payout.Status.PROCESSING:
            # Already in processing (retry path); fall through
            pass

        else:
            # completed or failed — skip
            logger.info(f'Payout {payout_id} already terminal ({payout.status}), skipping')
            return

        payout.attempts += 1
        payout.last_attempted_at = timezone.now()
        payout.save(update_fields=['attempts', 'last_attempted_at'])

    # ── Step 2: call the (simulated) bank ── (outside transaction — don't hold DB lock during I/O)
    result = _simulate_bank(payout_id)
    logger.info(f'Payout {payout_id}: bank returned {result}')

    # ── Step 3: record outcome atomically ──
    with transaction.atomic():
        payout = Payout.objects.select_for_update().get(id=payout_id)

        # Re-check: another worker may have already finished this
        if payout.status not in (Payout.Status.PROCESSING,):
            logger.info(f'Payout {payout_id} status changed to {payout.status} by another worker, skipping')
            return

        if result == 'success':
            transition_payout(payout, 'completed')
            # Replace the HOLD with a permanent DEBIT
            LedgerEntry.objects.filter(
                payout=payout, entry_type=LedgerEntry.EntryType.HOLD
            ).delete()
            LedgerEntry.objects.create(
                merchant=payout.merchant,
                entry_type=LedgerEntry.EntryType.DEBIT,
                amount_paise=payout.amount_paise,
                payout=payout,
                description=f'Payout {payout.id} settled successfully',
            )
            logger.info(f'Payout {payout_id}: completed')

        elif result == 'failed':
            _fail_and_release(payout)

        else:
            # 'hang' — leave in processing; retry_stuck_payouts will re-queue
            logger.info(f'Payout {payout_id}: hung, will retry later')


def _fail_and_release(payout):
    """
    Transition to failed and atomically release the held funds back to the merchant.
    Called inside an existing transaction with the payout row already locked.
    """
    if payout.status == Payout.Status.FAILED:
        return  # already done

    transition_payout(payout, 'failed')

    # Release the held amount back to available balance
    LedgerEntry.objects.create(
        merchant=payout.merchant,
        entry_type=LedgerEntry.EntryType.RELEASE,
        amount_paise=payout.amount_paise,
        payout=payout,
        description=f'Payout {payout.id} failed — funds released',
    )
    logger.info(f'Payout {payout.id}: failed and funds released')


# ──────────────────────────────────────────────
#  Task: pick up all pending payouts
# ──────────────────────────────────────────────

@shared_task(name='payouts.tasks.process_pending_payouts')
def process_pending_payouts():
    """Scheduled every 10 s. Queues a worker task for each PENDING payout."""
    ids = list(
        Payout.objects.filter(status=Payout.Status.PENDING).values_list('id', flat=True)
    )
    logger.info(f'Dispatching {len(ids)} pending payout(s)')
    for pid in ids:
        process_single_payout.delay(str(pid))


# ──────────────────────────────────────────────
#  Task: retry payouts stuck in processing
# ──────────────────────────────────────────────

@shared_task(name='payouts.tasks.retry_stuck_payouts')
def retry_stuck_payouts():
    """
    Runs every 15 s.

    Payouts stuck in PROCESSING for > 30 s are retried (up to 3 attempts total).
    After 3 failed attempts, the payout is marked FAILED and funds are released.
    """
    threshold = timezone.now() - timedelta(seconds=30)

    # Retry payouts that are stuck but still under the attempt limit
    stuck_ids = list(
        Payout.objects.filter(
            status=Payout.Status.PROCESSING,
            last_attempted_at__lt=threshold,
            attempts__lt=3,
        ).values_list('id', flat=True)
    )
    logger.info(f'Retrying {len(stuck_ids)} stuck payout(s)')
    for pid in stuck_ids:
        process_single_payout.delay(str(pid))

    # Exhaust limit — fail them and release funds
    exhausted = Payout.objects.filter(
        status=Payout.Status.PROCESSING,
        last_attempted_at__lt=threshold,
        attempts__gte=3,
    )
    for payout in exhausted:
        with transaction.atomic():
            payout = Payout.objects.select_for_update().get(id=payout.id)
            if payout.status == Payout.Status.PROCESSING:
                _fail_and_release(payout)
                logger.info(f'Payout {payout.id}: max retries exceeded, marked failed')
