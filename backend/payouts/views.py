import logging
from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Merchant, LedgerEntry, Payout, IdempotencyKey
from .serializers import MerchantSerializer, LedgerEntrySerializer, PayoutSerializer
from .services import create_payout

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
#  Merchants
# ──────────────────────────────────────────────

@api_view(['GET'])
def merchant_list(request):
    """GET /api/v1/merchants/ — list all merchants with their computed balances."""
    merchants = Merchant.objects.all().order_by('name')
    return Response(MerchantSerializer(merchants, many=True).data)


@api_view(['GET'])
def merchant_detail(request, merchant_id):
    """GET /api/v1/merchants/<id>/ — single merchant with balances."""
    try:
        merchant = Merchant.objects.get(id=merchant_id)
    except Merchant.DoesNotExist:
        return Response({'error': 'Merchant not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response(MerchantSerializer(merchant).data)


@api_view(['GET'])
def merchant_ledger(request, merchant_id):
    """GET /api/v1/merchants/<id>/ledger/ — ledger entries (most recent first, max 50)."""
    try:
        Merchant.objects.get(id=merchant_id)
    except Merchant.DoesNotExist:
        return Response({'error': 'Merchant not found'}, status=status.HTTP_404_NOT_FOUND)

    entries = LedgerEntry.objects.filter(merchant_id=merchant_id).order_by('-created_at')[:50]
    return Response(LedgerEntrySerializer(entries, many=True).data)


@api_view(['GET'])
def merchant_payouts(request, merchant_id):
    """GET /api/v1/merchants/<id>/payouts/ — payout history (most recent first)."""
    try:
        Merchant.objects.get(id=merchant_id)
    except Merchant.DoesNotExist:
        return Response({'error': 'Merchant not found'}, status=status.HTTP_404_NOT_FOUND)

    payouts = Payout.objects.filter(merchant_id=merchant_id).order_by('-created_at')
    return Response(PayoutSerializer(payouts, many=True).data)


# ──────────────────────────────────────────────
#  Payouts
# ──────────────────────────────────────────────

@api_view(['POST'])
def create_payout_view(request):
    """
    POST /api/v1/payouts/

    Required header: Idempotency-Key: <uuid>
    Body: { merchant, amount_paise, bank_account_id }

    Idempotency:
        The middleware already returns cached responses for repeated keys.
        If the middleware let it through, we process it fresh.
        After success, we store the response in IdempotencyKey for future repeats.

    Concurrency:
        create_payout() uses SELECT FOR UPDATE on the merchant row.
        Two simultaneous 60 INR requests on a 100 INR balance: exactly one wins.
    """
    merchant_id  = request.data.get('merchant')
    amount_paise = request.data.get('amount_paise')
    bank_account = request.data.get('bank_account_id', '').strip()
    idem_key     = getattr(request, '_idempotency_key', request.headers.get('Idempotency-Key', '').strip())

    # ── Validate input ──
    if not merchant_id:
        return Response({'error': 'merchant is required'}, status=status.HTTP_400_BAD_REQUEST)

    if not idem_key:
        return Response({'error': 'Idempotency-Key header is required'}, status=status.HTTP_400_BAD_REQUEST)

    if amount_paise is None:
        return Response({'error': 'amount_paise is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        amount_paise = int(amount_paise)
    except (ValueError, TypeError):
        return Response({'error': 'amount_paise must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

    if amount_paise <= 0:
        return Response({'error': 'amount_paise must be positive'}, status=status.HTTP_400_BAD_REQUEST)

    if not bank_account:
        return Response({'error': 'bank_account_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        Merchant.objects.get(id=merchant_id)
    except Merchant.DoesNotExist:
        return Response({'error': 'Merchant not found'}, status=status.HTTP_404_NOT_FOUND)

    # ── Create payout (atomic, concurrency-safe) ──
    try:
        payout = create_payout(
            merchant_id=merchant_id,
            amount_paise=amount_paise,
            bank_account_id=bank_account,
            idempotency_key=idem_key,
        )
    except ValueError as e:
        # Insufficient balance
        err_body = {'error': str(e)}
        _store_idempotency(idem_key, merchant_id, 400, err_body)
        return Response(err_body, status=status.HTTP_400_BAD_REQUEST)
    except IntegrityError:
        # Race condition: duplicate (merchant, idempotency_key) — treat as already processed
        try:
            existing_payout = Payout.objects.get(merchant_id=merchant_id, idempotency_key=idem_key)
            return Response(PayoutSerializer(existing_payout).data, status=status.HTTP_201_CREATED)
        except Payout.DoesNotExist:
            return Response({'error': 'Duplicate request'}, status=status.HTTP_409_CONFLICT)

    # ── Enqueue background processing ──
    try:
        from .tasks import process_single_payout
        process_single_payout.delay(str(payout.id))
    except Exception:
        logger.exception('Failed to enqueue payout task — will be picked up by scheduler')

    response_body = PayoutSerializer(payout).data
    _store_idempotency(idem_key, merchant_id, 201, response_body)
    return Response(response_body, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def payout_detail(request, payout_id):
    """GET /api/v1/payouts/<id>/ — single payout status."""
    try:
        payout = Payout.objects.get(id=payout_id)
    except Payout.DoesNotExist:
        return Response({'error': 'Payout not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(PayoutSerializer(payout).data)


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────

def _store_idempotency(key: str, merchant_id: str, http_status: int, body: dict):
    """Persist idempotency response so the middleware can return it on repeat calls."""
    if not key or not merchant_id:
        return
    try:
        IdempotencyKey.objects.get_or_create(
            merchant_id=merchant_id,
            key=key,
            defaults={'response_status': http_status, 'response_body': body},
        )
    except Exception:
        logger.exception('Failed to store idempotency key')
