"""
Concurrency test: two simultaneous 60 INR payout requests on a 100 INR balance.

Exactly ONE must succeed; the other must be rejected with a balance error.

Uses TransactionTestCase (not TestCase) so each thread gets its own real DB
transaction — TestCase wraps everything in a single transaction that never commits,
which would make SELECT FOR UPDATE useless.

Requires PostgreSQL (SELECT FOR UPDATE semantics).
"""
import threading
from django.test import TransactionTestCase
from payouts.models import Merchant, LedgerEntry, Payout
from payouts.services import create_payout


class ConcurrencyTest(TransactionTestCase):

    def setUp(self):
        # Create merchant with 100 INR = 10000 paise
        self.merchant = Merchant.objects.create(
            name='Test Merchant',
            email='test@concurrent.io',
        )
        LedgerEntry.objects.create(
            merchant=self.merchant,
            entry_type=LedgerEntry.EntryType.CREDIT,
            amount_paise=10_000,   # ₹100
            description='Initial credit',
        )

    def test_concurrent_payouts_only_one_succeeds(self):
        """
        Two threads each try to withdraw ₹60 from a ₹100 balance simultaneously.
        Exactly one must succeed, the other must fail with ValueError (insufficient funds).
        """
        results = []
        errors  = []

        def attempt_payout(key_suffix):
            try:
                payout = create_payout(
                    merchant_id=self.merchant.id,
                    amount_paise=6_000,       # ₹60
                    bank_account_id='BA_TEST',
                    idempotency_key=f'test-key-{key_suffix}',
                )
                results.append(('success', payout.id))
            except ValueError as e:
                results.append(('failed', str(e)))
            except Exception as e:
                errors.append(str(e))

        t1 = threading.Thread(target=attempt_payout, args=('a',))
        t2 = threading.Thread(target=attempt_payout, args=('b',))

        t1.start(); t2.start()
        t1.join();  t2.join()

        self.assertEqual(len(errors), 0, f'Unexpected errors: {errors}')
        self.assertEqual(len(results), 2)

        successes = [r for r in results if r[0] == 'success']
        failures  = [r for r in results if r[0] == 'failed']

        self.assertEqual(len(successes), 1, f'Expected exactly 1 success, got: {results}')
        self.assertEqual(len(failures),  1, f'Expected exactly 1 failure, got: {results}')

        # Verify DB state: only 1 payout created, balance correctly held
        self.assertEqual(Payout.objects.filter(merchant=self.merchant).count(), 1)
        payout = Payout.objects.get(merchant=self.merchant)
        self.assertEqual(payout.status, Payout.Status.PENDING)

        # Ledger: 1 credit + 1 hold
        credits = LedgerEntry.objects.filter(merchant=self.merchant, entry_type=LedgerEntry.EntryType.CREDIT)
        holds   = LedgerEntry.objects.filter(merchant=self.merchant, entry_type=LedgerEntry.EntryType.HOLD)
        self.assertEqual(credits.count(), 1)
        self.assertEqual(holds.count(),   1)
        self.assertEqual(holds.first().amount_paise, 6_000)

    def test_exact_balance_exhaustion(self):
        """A payout for exactly the full balance must succeed."""
        payout = create_payout(
            merchant_id=self.merchant.id,
            amount_paise=10_000,   # ₹100 — exact balance
            bank_account_id='BA_TEST',
            idempotency_key='full-balance-key',
        )
        self.assertEqual(payout.amount_paise, 10_000)
        self.assertEqual(payout.status, Payout.Status.PENDING)

    def test_overdraft_rejected(self):
        """A payout exceeding the balance must always be rejected."""
        with self.assertRaises(ValueError):
            create_payout(
                merchant_id=self.merchant.id,
                amount_paise=10_001,   # 1 paise over
                bank_account_id='BA_TEST',
                idempotency_key='overdraft-key',
            )
