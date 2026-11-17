# SmartCart AI — Architecture and Decisions

Status: Accepted for Phase 1. Revisit when a decision's stated trigger occurs.

## System overview

```
Flutter app (iOS, Android)
    │  HTTPS, JSON, bearer tokens
    ▼
FastAPI modular monolith  ──►  PostgreSQL 17 (system of record)
    │        │
    │        └──►  Redis (cache, rate limits, Celery broker)
    ▼
Celery worker (same codebase) ──► OCR provider · LLM provider · S3-compatible private storage
```

## Decisions

### ADR-001 Modular monolith
One deployable backend split into modules (`auth`, `receipts`, `products`, …). Modules talk through their service layer, not each other's tables. Microservices are rejected until there is a measured scaling or team-boundary reason.
Trigger to revisit: a module needs independent scaling or release cadence.

### ADR-002 Synchronous SQLAlchemy 2.x with psycopg 3
Route handlers are plain `def`, so FastAPI runs them in its threadpool. Celery workers use the same service layer and the same synchronous session code, which avoids maintaining two data-access paths. Connection pooling is handled by SQLAlchemy's `QueuePool` with `pool_pre_ping`.
Trigger to revisit: I/O-bound endpoints saturate the threadpool under load.

### ADR-003 Configuration from the environment
`app/core/config.py` reads `SMARTCART_*` variables through `pydantic-settings`. Secrets are `SecretStr`, so they do not appear in `repr` or logs. The signing key must be at least 32 characters. No credentials have defaults. Production values come from Vault or the platform secret manager.

### ADR-004 One error envelope
Every error response has the shape `{"error": {"code", "message", "details", "request_id"}}`. Validation errors report field locations and messages only, never the submitted values, because request bodies can contain passwords or receipt text. Unhandled exceptions return a generic 500 and log the exception type with the request ID.

### ADR-005 Request IDs
Each response carries `X-Request-ID`. A client-supplied value is accepted only if it matches `[A-Za-z0-9._-]{1,64}`. Otherwise a new UUID hex is generated. The validation prevents log injection.

### ADR-006 Structured JSON logs
Logs are emitted as one JSON object per line to stdout. Extra fields are passed with `extra=`. Log shipping and Sentry are wired in the operations phase.

### ADR-007 Versioned API
Feature routes mount under `/api/v1`. Operational endpoints (`/health`, `/health/ready`) sit at the root and are unversioned. OpenAPI and docs are disabled in production.

### ADR-008 Money and time
Money is `NUMERIC(12, 2)` in PostgreSQL and `Decimal` in Python. Unit prices use a higher scale where needed (for example `NUMERIC(12, 4)`). Each monetary value carries a currency code. Timestamps are stored in UTC. Purchase dates keep the local calendar date and an IANA timezone name.

### ADR-009 Receipts are kept separate from catalog data
Original receipt text is stored on `receipt_items` and never edited by matching. Matches to `products` and `product_variants` are references with a confidence score and a match source (system or user). Price observations are derived from confirmed receipt items and keep a foreign key to their source receipt and purchase date.

### ADR-010 Provider interfaces for OCR and LLM
OCR and LLM extraction sit behind Python `Protocol` interfaces in `app/integrations/ocr` and `app/integrations/llm`. Tests use deterministic local implementations. No provider credentials are needed to run the test suite.

### ADR-011 PCI scope handling for receipts
Receipts may show partial card numbers and tender lines. The pipeline masks anything that looks like a card number (13 to 19 digits, including separated groups) before OCR text reaches an LLM, a log, or persistent storage. Masking is tested with synthetic fixtures. This is a technical control, not a compliance determination. The scope question goes to the organization's security and compliance owners.

### ADR-012 `ai/` is a pure library
`ai/` holds parsing, matching, scoring, forecasting, prompts and evaluation sets. It has no database or HTTP access. Backend integrations call it. This keeps the evaluation harness runnable without a server.

### ADR-014 Opaque session tokens, not JWTs
Access and refresh tokens are random strings stored as SHA-256 digests in `auth_sessions`. Authorization is a database lookup, so logout and password changes take effect immediately, and no signing library is needed. Passwords use scrypt from the standard library. Trigger to revisit: authentication lookups become a measurable bottleneck, or a second service needs to verify tokens without database access.
Details and limits: `docs/security.md`.

### ADR-013 Recommendations are deterministic
Store comparison, basket totals, and multi-store optimization are deterministic Python. An LLM may only turn the computed result into a sentence. Missing prices are reported as missing and are never replaced with zero or an estimate labeled as observed.

## Price data classes
Every price shown to a user is labeled with one of these classes:
- **Historical user-observed** — from a receipt the user confirmed.
- **Authorized current retailer** — only from an authorized API or licensed feed. None are integrated yet.
- **Estimated** — computed from historical observations.
- **Forecasted** — produced by the optional forecasting module, with an interval and a coverage note.

## Open items
- Hosting target for staging and production (AWS is assumed, not decided).
- Choice of managed Postgres and Redis for staging.
- OCR and LLM vendors and their data-processing terms.
- Legal review of receipt retention, privacy notices, and US state privacy obligations.
