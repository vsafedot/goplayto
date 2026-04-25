from rest_framework import serializers
from django.db.models import Sum
from .models import Merchant, LedgerEntry, Payout

class MerchantSerializer(serializers.ModelSerializer):
    available_balance = serializers.SerializerMethodField()
    held_balance = serializers.SerializerMethodField()

    class Meta:
        model = Merchant
        fields = ('id', 'name', 'email', 'available_balance', 'held_balance')
        read_only_fields = ('id', 'available_balance', 'held_balance')

    def get_available_balance(self, obj):
        from .services import get_available_balance
        return get_available_balance(obj.id)

    def get_held_balance(self, obj):
        held = LedgerEntry.objects.filter(
            merchant=obj, entry_type=LedgerEntry.EntryType.HOLD
        ).aggregate(total=Sum('amount_paise'))['total'] or 0
        released = LedgerEntry.objects.filter(
            merchant=obj, entry_type=LedgerEntry.EntryType.RELEASE
        ).aggregate(total=Sum('amount_paise'))['total'] or 0
        return held - released

class LedgerEntrySerializer(serializers.ModelSerializer):
    entry_type_display = serializers.CharField(source='get_entry_type_display', read_only=True)

    class Meta:
        model = LedgerEntry
        fields = ('id', 'merchant', 'entry_type', 'entry_type_display', 'amount_paise', 'description', 'created_at')
        read_only_fields = ('id', 'created_at')

class PayoutCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = ('id', 'merchant', 'amount_paise', 'bank_account_id')
        read_only_fields = ('id',)

    def validate(self, attrs):
        if attrs['amount_paise'] <= 0:
            raise serializers.ValidationError('Amount must be positive')
        return attrs

class PayoutSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Payout
        fields = ('id', 'merchant', 'amount_paise', 'bank_account_id', 'status', 'status_display', 'created_at', 'updated_at')
        read_only_fields = ('id', 'status', 'created_at', 'updated_at')
