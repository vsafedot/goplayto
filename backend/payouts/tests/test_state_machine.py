"""
State machine tests — verifies all legal and illegal transitions.
"""
from django.test import TestCase
from payouts.models import Merchant, LedgerEntry, Payout
from payouts.state_machine import transition_payout


def _make_payout(merchant, status):
    p = Payout.objects.create(
        merchant=merchant,
        amount_paise=1_000,
        bank_account_id='BA_TEST',
        idempotency_key=f'key-{status}',
        status=status,
    )
    return p


class StateMachineTest(TestCase):
    def setUp(self):
        self.merchant = Merchant.objects.create(name='SM Merchant', email='sm@test.io')

    # ── Legal transitions ──────────────────────

    def test_pending_to_processing(self):
        p = _make_payout(self.merchant, 'pending')
        transition_payout(p, 'processing')
        p.refresh_from_db()
        self.assertEqual(p.status, 'processing')

    def test_processing_to_completed(self):
        p = _make_payout(self.merchant, 'processing')
        transition_payout(p, 'completed')
        p.refresh_from_db()
        self.assertEqual(p.status, 'completed')

    def test_processing_to_failed(self):
        p = _make_payout(self.merchant, 'processing')
        transition_payout(p, 'failed')
        p.refresh_from_db()
        self.assertEqual(p.status, 'failed')

    # ── Illegal transitions ────────────────────

    def test_completed_to_pending_blocked(self):
        p = _make_payout(self.merchant, 'completed')
        with self.assertRaises(ValueError):
            transition_payout(p, 'pending')

    def test_completed_to_failed_blocked(self):
        p = _make_payout(self.merchant, 'completed')
        with self.assertRaises(ValueError):
            transition_payout(p, 'failed')

    def test_failed_to_completed_blocked(self):
        """The specific check the challenge asks for: failed → completed must be blocked."""
        p = _make_payout(self.merchant, 'failed')
        with self.assertRaises(ValueError):
            transition_payout(p, 'completed')

    def test_failed_to_processing_blocked(self):
        p = _make_payout(self.merchant, 'failed')
        with self.assertRaises(ValueError):
            transition_payout(p, 'processing')

    def test_pending_to_completed_blocked(self):
        """Skipping processing is illegal."""
        p = _make_payout(self.merchant, 'pending')
        with self.assertRaises(ValueError):
            transition_payout(p, 'completed')

    def test_pending_to_failed_blocked(self):
        p = _make_payout(self.merchant, 'pending')
        with self.assertRaises(ValueError):
            transition_payout(p, 'failed')
