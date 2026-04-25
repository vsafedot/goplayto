# Playto Payout Engine - Architecture & Explainer

## Overview
This repository contains a full-stack, production-grade Payout Engine. It is designed to handle merchant payouts reliably, ensuring financial integrity even under high concurrent loads or unstable network conditions.

The system is split into two parts:
- **Backend**: Django REST Framework, PostgreSQL, Celery, and Redis.
- **Frontend**: React, Vite, and custom CSS.

---

## 1. Concurrency & Financial Integrity (Handling Race Conditions)
A core challenge of any payout engine is ensuring that a merchant cannot withdraw more funds than they have, even if two payout requests arrive at the exact same millisecond. 

We solved this using **Database-Level Row Locking (`SELECT FOR UPDATE`)**.
In our `create_payout` service, before checking the balance and creating a ledger entry, we lock the specific merchant row within an atomic database transaction.
```python
with transaction.atomic():
    merchant = Merchant.objects.select_for_update().get(id=merchant_id)
    # Balance check and deduction happen securely here
```
This forces simultaneous requests for the same merchant to be processed sequentially by the PostgreSQL database, completely eliminating the possibility of negative balances or double-spending.

## 2. Network Failure & Retries (Idempotency)
If a client experiences a network timeout after sending a payout request, they might safely retry the exact same request without accidentally creating two identical payouts.

We implemented an **Idempotency Middleware** using the `Idempotency-Key` HTTP header:
- Every payout request must include a unique UUID as an idempotency key.
- The middleware checks if this key has already been processed successfully.
- If it has, the middleware intercepts the request and instantly returns the *cached HTTP response* from the first successful attempt.
- This ensures clients can aggressively retry failed network calls with zero risk of duplicate payouts.

## 3. Background Processing (Celery & Redis)
Payouts in the real world involve communicating with third-party banking APIs, which can be slow or unreliable. 

Instead of blocking the HTTP API request, our API immediately returns a `201 Created` with a `PENDING` status. The actual processing is deferred to a background worker:
- **Celery Worker**: Picks up the pending payout from the **Redis** message broker.
- **Celery Beat (Scheduler)**: We run a periodic task every 10 seconds to sweep the database for any `PENDING` payouts that might have gotten stuck due to sudden worker crashes.
- The worker executes the simulated banking logic and transitions the payout to `COMPLETED` or `FAILED`.

## 4. Deployment Architecture
To maintain a robust infrastructure, the system is deployed using:
- **Vercel**: Hosts the React frontend, configured via `VITE_API_URL` to point to the live backend.
- **Render**: Hosts the Django Backend API and PostgreSQL database.
- **Upstash**: Provides a serverless Redis cluster used as the Celery broker.

*(Note: To fit within Render's free tier limitations, the Celery worker and Gunicorn API are booted simultaneously in the same web container).*

---

### Local Development
If you are evaluating this locally:
1. The backend automatically falls back to `SQLite` and an `In-Memory Broker` for Celery if `USE_SQLITE=True` and `USE_MEMORY_BROKER=True` are set in the `.env` file. This means you can evaluate the logic locally without needing to install Postgres or Redis.
2. The frontend proxy automatically routes `/api/v1` to `localhost:8000` during local development (`npm run dev`).

---

**Signed,**  
*Siddharth Nain*
