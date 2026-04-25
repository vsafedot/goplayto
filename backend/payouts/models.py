from django.db import models
import uuid
from django.utils import timezone

class Merchant(models.Model):
    """Merchant who receives payouts. No balance field – balance derived from ledger entries."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Merchant"
        verbose_name_plural = "Merchants"

    def __str__(self):
        return self.name

class LedgerEntry(models.Model):
    """Immutable record of every credit, debit, hold, or release for a merchant."""
    class EntryType(models.TextChoices):
        CREDIT = 'credit', 'Credit'
        DEBIT = 'debit', 'Debit'
        HOLD = 'hold', 'Hold'
        RELEASE = 'release', 'Release'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(Merchant, on_delete=models.PROTECT, related_name='ledger_entries')
    entry_type = models.CharField(max_length=10, choices=EntryType.choices)
    amount_paise = models.BigIntegerField(help_text='Always stored as a positive integer (paise).')
    payout = models.ForeignKey('Payout', null=True, blank=True, on_delete=models.SET_NULL, related_name='ledger_entries')
    description = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['merchant', 'entry_type'])]

    def __str__(self):
        return f"{self.get_entry_type_display()} {self.amount_paise} for {self.merchant.name}"

class Payout(models.Model):
    """Payout request created by a merchant. State machine enforced via code."""
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(Merchant, on_delete=models.PROTECT, related_name='payouts')
    amount_paise = models.BigIntegerField()
    bank_account_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    idempotency_key = models.CharField(max_length=100)
    attempts = models.IntegerField(default=0)
    last_attempted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['merchant', 'idempotency_key'], name='unique_idempotency_per_merchant')
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Payout {self.id} ({self.amount_paise} paise) for {self.merchant.name}"

class IdempotencyKey(models.Model):
    """Store response of a payout request to guarantee idempotency within 24 h."""
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='idempotency_keys')
    key = models.CharField(max_length=100)
    response_status = models.IntegerField()
    response_body = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['merchant', 'key'], name='unique_key_per_merchant')
        ]
        indexes = [models.Index(fields=['merchant', 'key'])]

    def __str__(self):
        return f"Idempotency {self.key} for {self.merchant.name}"
