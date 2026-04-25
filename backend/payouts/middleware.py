from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import json


class IdempotencyMiddleware:
    """
    Handles idempotency for POST /api/v1/payouts/ only.

    On first request: stores the response body + status in IdempotencyKey.
    On repeat request within 24h with same key: returns the stored response immediately.
    On in-flight duplicate: the DB unique constraint on (merchant, key) inside the view
    will raise IntegrityError — caught and turned into a 409.

    Key scoping: per merchant (extracted from the request body).
    """

    PAYOUT_PATH = '/api/v1/payouts/'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only intercept POST to payout endpoint
        if request.method != 'POST' or request.path != self.PAYOUT_PATH:
            return self.get_response(request)

        idem_key = request.headers.get('Idempotency-Key', '').strip()
        if not idem_key:
            return self.get_response(request)

        # Parse merchant id from body to scope the key
        try:
            body = json.loads(request.body)
            merchant_id = body.get('merchant')
        except (json.JSONDecodeError, AttributeError):
            return self.get_response(request)

        if not merchant_id:
            return self.get_response(request)

        # Lazy import to avoid app-registry issues at module load time
        from payouts.models import IdempotencyKey

        cutoff = timezone.now() - timedelta(hours=24)
        existing = IdempotencyKey.objects.filter(
            merchant_id=merchant_id,
            key=idem_key,
            created_at__gte=cutoff,
        ).first()

        if existing:
            return JsonResponse(existing.response_body, status=existing.response_status)

        # Let the request through; the view will save the IdempotencyKey
        request._idempotency_key = idem_key
        request._idempotency_merchant_id = merchant_id
        return self.get_response(request)
