# SmartCart AI — project instructions

## What this is
US grocery and household price-intelligence platform. Flutter client (iOS and Android), FastAPI modular monolith, PostgreSQL, Redis and Celery workers. The initial price source is user-confirmed receipts. Do not scrape retailers, do not invent prices, and do not add retailer integrations without an authorized API or licensed feed.

Live status lives in `docs/implementation-progress.md`. Update it at every milestone. Design decisions live in `docs/architecture.md`.

## Layout
- `backend/` — FastAPI app. `app/core` (config, DB engine, errors, logging, middleware), `app/api` (health and `/api/v1` router), `app/modules` and `app/integrations` (not yet created), `tests/`.
- `frontend/flutter_app/` — Flutter client (not yet created).
- `ai/` — pure-Python receipt parsing, product matching, price intelligence, forecasting, evaluation sets and prompts. No database access in `ai/`.
- `docs/` — design documents.
- `infrastructure/`, `scripts/` — not yet created.

## Commands
- `make install` — create `backend/.venv` and install dev dependencies. Package installs need confirmation first (see Policy below).
- `make lint` — ruff check, ruff format check, mypy.
- `make test` — pytest.
- `make run` — uvicorn with reload on 127.0.0.1:8000.
- `make up` / `make down` — Postgres and Redis via docker compose.

## Conventions
- Python 3.12+, full type hints, mypy strict on `app/`.
- Business logic lives in `modules/<name>/service.py`, not in routers or Flutter widgets.
- Pydantic API schemas are separate from SQLAlchemy models.
- Money uses `Decimal` / `NUMERIC`. Never `float`. Store the currency code explicitly.
- Timestamps are timezone-aware UTC. Purchase dates also keep the local date and timezone.
- Primary keys are UUIDs.
- Ownership comes from the authenticated identity, never from a user ID in a request body.
- Raise `AppError` subclasses from `app/core/errors.py`. No bare `except`, no swallowed exceptions.
- Do not log passwords, tokens, or receipt contents. Log exception types, not secret-bearing messages.
- Add a dependency in the phase that first uses it. Constrain versions in `pyproject.toml`.
- Match the surrounding code's comment density, naming, and idiom.

## Security and compliance (organization policy)
- Receipts can contain payment card data. Never paste a PAN, CVV, or full cardholder data into prompts, fixtures, logs, or tests. Test receipts are synthetic and marked as test data. The pipeline must mask card numbers before any OCR or LLM call and before persisting extracted text.
- Secrets belong in Vault or the secret manager. Never commit secrets, API keys, or credentials. `.env` is gitignored. Only `.env.example` (placeholders) is committed.
- Changes under `/payments` or `/billing` require security review before merge.
- Every commit must pass `make lint` and the pre-commit hook chain. Run the test suite and confirm it passes before committing.
- Production changes require a change ticket. Do not run `terraform apply`, `kubectl apply`, or database migrations against production.
- Plugin and MCP server installs require security review.
- Before any package install (npm, brew, pip, yarn), list the exact packages and get the user's confirmation.
- Do not deploy, publish mobile apps, or create paid cloud resources without explicit authorization.
