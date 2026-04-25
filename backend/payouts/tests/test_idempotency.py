"""
Idempotency tests.

Verifies:
1. Two calls with the same Idempotency-Key return identical responses.
2. Only one Payout is created, not two.
3. Keys are scoped per merchant (same key for different merchants = different records).
4. Keys expire after 24 hours.
"""
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from payouts.models import Merchant, LedgerEntry, Payout, IdempotencyKey
from payouts.services import create_payout


class IdempotencyServiceTest(TestCase):
    """Test idempotency at the service layer via the DB unique constraint."""

    def setUp(self):
        self.merchant = Merchant.objects.create(name='Idem Merchant', email='idem@test.io')
        LedgerEntry.objects.create(
            merchant=self.merchant,
            entry_type=LedgerEntry.EntryType.CREDIT,
            amount_paise=100_000,
            description='Seed credit',
        )

    def test_same_idempotency_key_creates_one_payout(self):
        """Calling create_payout twice with the same key must produce exactly 1 payout."""
        key = str(uuid.uuid4())

        payout1 = create_payout(
            merchant_id=self.merchant.id,
            amount_paise=5_000,
            bank_account_id='BA_001',
            idempotency_key=key,
        )

        # Second call with same key should raise IntegrityError (unique constraint)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            create_payout(
                merchant_id=self.merchant.id,
                amount_paise=5_000,
                bank_account_id='BA_001',
                idempotency_key=key,
            )

        # Only one payout exists
        self.assertEqual(Payout.objects.filter(merchant=self.merchant).count(), 1)

    def test_different_keys_create_separate_payouts(self):
        """Different idempotency keys must create separate payouts."""
        create_payout(self.merchant.id, 5_000, 'BA_001', str(uuid.uuid4()))
        create_payout(self.merchant.id, 5_000, 'BA_001', str(uuid.uuid4()))
        self.assertEqual(Payout.objects.filter(merchant=self.merchant).count(), 2)


class IdempotencyAPITest(TestCase):
    """Test idempotency end-to-end through the HTTP API + middleware."""

    def setUp(self):
        self.client = Client()
        self.merchant = Merchant.objects.create(name='API Merchant', email='api@test.io')
        LedgerEntry.objects.create(
            merchant=self.merchant,
            entry_type=LedgerEntry.EntryType.CREDIT,
            amount_paise=500_000,
            description='Seed credit',
        )

    def _post_payout(self, idem_key, amount=10_000):
        return self.client.post(
            '/api/v1/payouts/',
            data={
                'merchant': str(self.merchant.id),
                'amount_paise': amount,
                'bank_account_id': 'BA_TEST',
            },
            content_type='application/json',
            HTTP_IDEMPOTENCY_KEY=idem_key,
        )

    def test_duplicate_request_returns_same_response(self):
        """The second request with the same key must return HTTP 201 with identical body."""
        key = str(uuid.uuid4())

        r1 = self._post_payout(key)
        self.assertEqual(r1.status_code, 201)

        r2 = self._post_payout(key)
        self.assertEqual(r2.status_code, 201)

        # Response bodies must be identical
        self.assertEqual(r1.json(), r2.json())

        # Only one payout created
        self.assertEqual(Payout.objects.filter(merchant=self.merchant).count(), 1)

    def test_expired_key_allows_new_payout(self):
        """An idempotency key older than 24h must NOT block a new request."""
        key = str(uuid.uuid4())

        # Manually create an expired idempotency record
        IdempotencyKey.objects.create(
            merchant=self.merchant,
            key=key,
            response_status=201,
            response_body={'id': str(uuid.uuid4()), 'status': 'completed'},
        )
        # Backdate it so it's older than 24 hours
        IdempotencyKey.objects.filter(merchant=self.merchant, key=key).update(
            created_at=timezone.now() - timedelta(hours=25)
        )

        # Now POST with the same key — should create a new payout, NOT return the stale cache
        r = self._post_payout(key)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Payout.objects.filter(merchant=self.merchant).count(), 1)

    def test_key_scoped_per_merchant(self):
        """The same idempotency key used by two different merchants must produce two payouts."""
        merchant2 = Merchant.objects.create(name='Second Merchant', email='second@test.io')
        LedgerEntry.objects.create(
            merchant=merchant2,
            entry_type=LedgerEntry.EntryType.CREDIT,
            amount_paise=500_000,
            description='Seed credit',
        )

        key = str(uuid.uuid4())

        r1 = self._post_payout(key)
        self.assertEqual(r1.status_code, 201)

        r2 = self.client.post(
            '/api/v1/payouts/',
            data={
                'merchant': str(merchant2.id),
                'amount_paise': 10_000,
                'bank_account_id': 'BA_TEST',
            },
            content_type='application/json',
            HTTP_IDEMPOTENCY_KEY=key,
        )
        self.assertEqual(r2.status_code, 201)

        # Two different payouts — one per merchant
        self.assertEqual(Payout.objects.count(), 2)
        self.assertNotEqual(r1.json()['id'], r2.json()['id'])

    def test_missing_idempotency_key_still_works(self):
        """Requests without Idempotency-Key should still succeed (no middleware interference)."""
        r = self.client.post(
            '/api/v1/payouts/',
            data={
                'merchant': str(self.merchant.id),
                'amount_paise': 10_000,
                'bank_account_id': 'BA_TEST',
            },
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 201)
