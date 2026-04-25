from django.contrib import admin
from .models import Merchant, LedgerEntry, Payout, IdempotencyKey

@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'created_at')
    search_fields = ('name', 'email')

@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'merchant', 'entry_type', 'amount_paise', 'created_at')
    list_filter = ('entry_type', 'merchant')
    search_fields = ('merchant__name', 'description')

@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'merchant', 'amount_paise', 'bank_account_id', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'merchant')
    search_fields = ('merchant__name', 'bank_account_id')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    list_display = ('key', 'merchant', 'response_status', 'created_at')
    search_fields = ('key', 'merchant__name')
    readonly_fields = ('created_at',)
