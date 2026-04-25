import uuid
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Case, When, Value, BigIntegerField, F
from .models import Merchant, LedgerEntry, Payout, IdempotencyKey
from .state_machine import transition_payout


def get_available_balance(merchant_id):
    """Return the available balance (paise) for a merchant using a single DB query.
    Available = SUM(CREDIT + RELEASE) - SUM(DEBIT + HOLD).
    """
    agg = LedgerEntry.objects.filter(merchant_id=merchant_id).aggregate(
        credit_release=Sum(Case(
            When(entry_type__in=[LedgerEntry.EntryType.CREDIT, LedgerEntry.EntryType.RELEASE], then=F('amount_paise')),
            default=Value(0), output_field=BigIntegerField()
        )),
        debit_hold=Sum(Case(
            When(entry_type__in=[LedgerEntry.EntryType.DEBIT, LedgerEntry.EntryType.HOLD], then=F('amount_paise')),
            default=Value(0), output_field=BigIntegerField()
        ))
    )
    credit_release = agg['credit_release'] or 0
    debit_hold = agg['debit_hold'] or 0
    return credit_release - debit_hold


def create_payout(merchant_id: uuid.UUID, amount_paise: int, bank_account_id: str, idempotency_key: str):
    """Create a payout atomically, ensuring:
    * Concurrency safety via SELECT FOR UPDATE on the merchant row
    * Balance check and hold entry creation in the same transaction
    * Idempotency handling (raises IntegrityError if duplicate key)
    """
    with transaction.atomic():
        # Lock the merchant row to serialize balance checks for this merchant
        merchant = Merchant.objects.select_for_update().get(id=merchant_id)

        # Compute available balance at DB level
        available = get_available_balance(merchant_id)
        if amount_paise > available:
            raise ValueError(f'Insufficient balance: available {available}, requested {amount_paise}')

        # Create payout record (unique constraint on (merchant, idempotency_key) ensures idempotency)
        payout = Payout.objects.create(
            merchant=merchant,
            amount_paise=amount_paise,
            bank_account_id=bank_account_id,
            idempotency_key=idempotency_key,
            status=Payout.Status.PENDING,
        )

        # Record the hold – funds are reserved
        LedgerEntry.objects.create(
            merchant=merchant,
            entry_type=LedgerEntry.EntryType.HOLD,
            amount_paise=amount_paise,
            payout=payout,
            description=f'Hold for payout {payout.id}'
        )
        return payout
