# Playto — Production-Grade Payout Engine

A full-stack payout engine built for financial integrity, concurrency safety, and real-time observability. Merchants can create payouts, track ledger movements, and monitor balances through a polished React dashboard backed by a Django REST API with Celery-powered async processing.

---

## Architecture

```
┌──────────────┐      REST API       ┌──────────────┐
│   React +    │ ◄──────────────────► │  Django DRF  │
│   Vite UI    │   (JSON over HTTP)  │  Backend     │
└──────────────┘                     └──────┬───────┘
       │                                    │
       │ Nginx (prod)                       │ ORM + SELECT FOR UPDATE
       ▼                                    ▼
  Static Assets                      ┌──────────────┐
                                     │  PostgreSQL  │
                                     └──────────────┘
                                            │
                          ┌─────────────────┼─────────────────┐
                          ▼                 ▼                 ▼
                   ┌────────────┐   ┌────────────┐   ┌────────────┐
                   │   Celery   │   │   Celery   │   │   Redis    │
                   │   Worker   │   │   Beat     │   │   Broker   │
                   └────────────┘   └────────────┘   └────────────┘
```

## Tech Stack

| Layer          | Technology                                  |
| -------------- | ------------------------------------------- |
| **Frontend**   | React 19, Vite, Tailwind CSS, Lucide Icons  |
| **Backend**    | Django 5, Django REST Framework              |
| **Task Queue** | Celery 5 + Redis                            |
| **Database**   | PostgreSQL 16 (SQLite fallback for dev)      |
| **Deployment** | Docker Compose, Gunicorn, WhiteNoise, Nginx  |

## Key Features

- **Ledger-Based Accounting** — No mutable balance field; every credit, debit, hold, and release is an immutable ledger entry derived via aggregation.
- **Payout State Machine** — `PENDING → PROCESSING → COMPLETED / FAILED` with strict transition enforcement.
- **Idempotency Middleware** — Deduplicates payout requests using merchant-scoped idempotency keys (24 h TTL).
- **Concurrency Safety** — `SELECT FOR UPDATE` row-level locking prevents double-spend and race conditions.
- **Async Processing** — Celery workers pick up pending payouts; Celery Beat retries stuck ones automatically.
- **Full Observability** — Real-time dashboard with balance cards, ledger table, payout history, and toast notifications.

## Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended), or
- Python 3.11+, Node 18+, PostgreSQL 16, Redis 7

### One-Command Launch (Docker)

```bash
docker compose up --build
```

| Service   | URL                    |
| --------- | ---------------------- |
| Frontend  | http://localhost:3000   |
| Backend   | http://localhost:8000   |

The backend will automatically run migrations and seed sample data on first boot.

### Local Development (Without Docker)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # edit values as needed
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

#### Celery (requires Redis)

```bash
celery -A playto worker --loglevel=info
celery -A playto beat --loglevel=info
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Reference

All endpoints are prefixed with `/api/`.

| Method | Endpoint                             | Description                       |
| ------ | ------------------------------------ | --------------------------------- |
| GET    | `/api/merchants/`                    | List all merchants                |
| GET    | `/api/merchants/{id}/`               | Merchant details                  |
| GET    | `/api/merchants/{id}/balance/`       | Computed balance from ledger      |
| GET    | `/api/merchants/{id}/ledger/`        | Paginated ledger entries          |
| POST   | `/api/merchants/{id}/credit/`        | Credit merchant account           |
| POST   | `/api/payouts/`                      | Create a payout (idempotent)      |
| GET    | `/api/payouts/`                      | List all payouts                  |
| GET    | `/api/payouts/{id}/`                 | Payout details                    |

### Idempotency

Include the `Idempotency-Key` header on `POST /api/payouts/` requests. Duplicate keys within 24 hours return the cached response without side effects.

## Environment Variables

| Variable             | Default                | Description                  |
| -------------------- | ---------------------- | ---------------------------- |
| `DJANGO_SECRET_KEY`  | dev fallback           | Django secret key            |
| `DJANGO_DEBUG`       | `True`                 | Debug mode toggle            |
| `ALLOWED_HOSTS`      | `*`                    | Comma-separated host list    |
| `POSTGRES_DB`        | `playto`               | Database name                |
| `POSTGRES_USER`      | `playto`               | Database user                |
| `POSTGRES_PASSWORD`  | `playto`               | Database password            |
| `POSTGRES_HOST`      | `db`                   | Database host                |
| `POSTGRES_PORT`      | `5432`                 | Database port                |
| `REDIS_URL`          | `redis://redis:6379/0` | Celery broker / result backend |
| `USE_SQLITE`         | `False`                | Use SQLite instead of Postgres |

## Project Structure

```
playto/
├── backend/
│   ├── payouts/            # Django app — models, views, tasks, middleware
│   │   ├── models.py       # Merchant, LedgerEntry, Payout, IdempotencyKey
│   │   ├── views.py        # DRF ViewSets & custom actions
│   │   ├── tasks.py        # Celery tasks (process, retry, simulate)
│   │   ├── middleware.py   # Idempotency middleware
│   │   ├── services.py     # Business logic layer
│   │   ├── state_machine.py
│   │   └── serializers.py
│   ├── playto/             # Django project config
│   │   ├── settings.py
│   │   ├── celery.py
│   │   └── urls.py
│   ├── Dockerfile
│   ├── Procfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # Dashboard, PayoutForm, LedgerTable, etc.
│   │   ├── api/            # Axios API client
│   │   └── hooks/          # Custom React hooks
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
└── .gitignore
```

## License

This project is part of a founding-engineer assessment and is not licensed for redistribution.
