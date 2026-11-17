# SmartCart AI — Implementation Progress

Last updated: 2026-11-16

## Current phase
**Phase 2 — Authentication (backend complete, mobile pending).** Backend registration, login, refresh with replay detection, logout, password recovery and change, profile, account deletion, rate limiting and audit events are implemented and tested against PostgreSQL. Flutter auth screens and secure token storage are next. Phase 1 remaining work: GitHub Actions CI, Redis and Celery worker wiring, git and pre-commit.

## Phase 2 backend (2026-11-17)
- Endpoints (`/api/v1`): `auth/register` (201), `auth/login`, `auth/refresh`, `auth/logout` (204), `auth/password-reset/request` (202), `auth/password-reset/confirm` (204), `auth/password/change` (204), `auth/account/delete` (204), `users/me` GET and PATCH.
- Migration `0002_auth_users`: `users`, `auth_sessions`, `password_reset_tokens`, `audit_logs`. `alembic check` reports no drift.
- No new packages. Passwords use stdlib scrypt and tokens are opaque (ADR-014), so the `argon2-cffi` and `PyJWT` packages from the earlier proposal were not needed.
- Email: `console` backend for development (prints reset tokens to stdout). `memory` for tests. Staging and production refuse to start until a provider is added.
- Known limits, decisions and trade-offs: `docs/security.md`.

## Test results — Phase 2
- `make test` without a database: **35 passed, 21 skipped** (DB-backed tests skip).
- `make test` against `smartcart_test` (compose Postgres): **56 passed, 0 skipped**, including the auth API flow, refresh replay, password reset, password change, account deletion, rate limiting, audit trail, and the migration round-trip.
- `make lint`: passes (ruff check, ruff format, mypy strict on `app/`, 36 files).
- The `.env` file sets `SMARTCART_ENVIRONMENT=development`. Tests now force their own environment, so a sourced `.env` cannot push the suite out of test mode or point it at the development database.

## Completed
- Repository conventions and rules: `CLAUDE.md`.
- Architecture decisions ADR-001 to ADR-013: `docs/architecture.md`.
- Backend skeleton in `backend/app/`:
  - `core/config.py` — environment settings with `SecretStr` secrets and a 32-character minimum signing key.
  - `core/logging_config.py` — one JSON object per log line.
  - `core/errors.py` — `AppError` hierarchy and one error envelope. Validation errors omit submitted values.
  - `core/middleware.py` — request ID generation and validation.
  - `core/database.py` — SQLAlchemy engine with pooling, `pool_pre_ping` and a connect timeout. Lazy connection.
  - `api/health.py` — `/health` (liveness) and `/health/ready` (database check, 503 when unreachable).
  - `api/v1/router.py` — empty `/api/v1` router that feature modules will mount on.
  - `main.py` — application factory. Docs are disabled when `environment=production`.
- Backend tests in `backend/tests/` covering config validation, the error envelope, request IDs, readiness failure, no secret leakage on 500s, and JSON logging.
- `backend/pyproject.toml` with constrained versions and ruff, mypy and pytest configuration.
- `backend/Dockerfile` (non-root user) and `backend/.dockerignore`.
- `docker-compose.yml` for Postgres 17, Redis 7 and the API.
- `Makefile` targets: `install`, `lint`, `format`, `test`, `run`, `up`, `down`.
- `.gitignore`, `.env.example` (placeholders only), `README.md`.

## In progress / blocked
- **Docker build and compose.** The Docker daemon is not reachable from this session. The Dockerfile and compose file are unverified.
- **Flutter app shell (Phase 1 done, Phase 2 nav started).** `lib/app/`: Riverpod `routerProvider` (GoRouter, disposed with the app), `StatefulShellRoute` with five tabs (Home, Receipts, Lists, Catalog, Settings), theme from one seed color. Welcome screen with "Get started" → `/home`. Four tabs show `ComingSoonView` naming their phase. That is a known gap against the spec's rule that primary navigation must not lead to placeholders, and it closes as each phase lands. Widget test walks welcome → home → tabs. `flutter analyze`: no issues. `flutter test`: 1 passed. Not yet run in a browser or on a device (no web platform folder; Android SDK and Xcode not set up).
- **Flutter sign-in (Phase 2 mobile, 2026-11-17).** Screens: splash, welcome, sign in, register, forgot password, reset password (paste the code from the email; deep-link handling not built). Home shows the signed-in user and a working sign-out. Router redirects by auth state (splash while the stored session is checked).
  - Data layer (`lib/features/auth/`): `AuthApi` (Dio, all errors become `AuthFailure`), `AuthInterceptor` (adds the bearer token, retries a 401 once after refreshing), `SessionRefresher` (one rotation at a time, so concurrent 401s can't trigger replay detection), `HttpAuthRepository`, `SecureTokenStore` (flutter_secure_storage).
  - Base URL: `--dart-define=SMARTCART_API_URL=...`. Default `http://127.0.0.1:8000`. Android emulators need `http://10.0.2.2:8000`.
  - Android: `INTERNET` is now in the main manifest, so release builds can reach the API. Cleartext http is allowed only in the debug manifest.
  - **Verified:** `flutter analyze` no issues. `flutter test`: 16 passed, 2 skipped (live). Live test against the local API (`--dart-define=SMARTCART_LIVE_API=http://127.0.0.1:8000`): 2 passed. It covers register, restore, refresh after an expired access token, sign-out, sign-in, delete, and the wrong-password error code. Each run creates and deletes its own account in the development database.
  - **Not verified:** running on a device or simulator. Android SDK and Xcode are still not set up. The iOS simulator needs an App Transport Security setting for plain http to the local API, which hasn't been checked.
- **Flutter scaffold.** `frontend/flutter_app` (Flutter 3.50.0, android and ios). Approved packages installed: `flutter_riverpod` 3.5.0, `go_router` 18.1.4, `dio` 5.11.1, `flutter_secure_storage` 11.2.0, `freezed_annotation` 3.1.0, `json_annotation` 4.12.0; dev: `freezed` 4.0.3, `json_serializable` 6.15.2, `build_runner` 2.17.1. `flutter analyze`: 2 deprecation infos. `flutter test`: 1 passed.
- **`material_ui` resolved.** The SDK recommends `package:material_ui/material_ui.dart` over the deprecated `flutter/material`. Both imports now use `material_ui`, and `material_ui: ^1.11.1` is a direct dependency (user-approved; already resolved through `flutter_riverpod`). `flutter analyze`: no issues. The `flutter_lints` dev dependency came from the template, not the approved list.
- `flutter doctor`: Android SDK missing; Xcode incomplete and CocoaPods missing, so iOS builds aren't possible yet.
- **Git.** `smartcart-ai` is not a git repository yet. Commits are blocked until the user decides whether to initialize one, and until `make lint` and tests pass.

## Remaining work
**Phase 1 (rest):** Alembic setup and the first migration. Redis and Celery worker wiring. GitHub Actions workflows for backend lint and tests, Flutter analysis, dependency audit, and image build. Flutter foundation with Riverpod, GoRouter, Dio and secure token storage.
**Phase 2:** Registration, login, refresh, logout, password recovery and change, profile, account deletion. Rate limiting on auth endpoints. Flutter onboarding, auth screens and navigation shell.
**Phase 3:** Receipt upload with file and image validation, private S3-compatible storage, duplicate detection by content hash, processing job records.
**Phase 4:** OCR and LLM provider interfaces with local fakes, card-number masking, strict schema validation, extraction evaluation set, receipt review screens.
**Phase 5:** Catalog (brands, categories, products, variants), product matching with ranked candidates and confidence.
**Phase 6:** Verified price observations, deterministic price statistics and confidence levels.
**Phase 7:** Shopping lists, three recommendation strategies with tests.
**Phase 8:** Analytics, price alerts and notifications.
**Phase 9:** Subscription model, entitlements, usage limits, payment provider interface (requires security review under `/billing`).
**Phase 10:** Security hardening, integration and end-to-end tests, deployment configuration, operations and privacy documents, release preparation.

Documents not yet written: `product-requirements.md`, `database-design.md`, `api-specification.md`, `security.md`, `privacy.md`, `ai-processing.md`, `testing-strategy.md`, `deployment.md`, `operations-runbook.md`, `roadmap.md`.

## Test results (2026-11-16, backend venv on Python 3.12.16)
- `make test`: **13 passed**. Covers config validation, secret masking, error envelope, request ID handling, readiness failure, validation errors without echoed values, no internal detail in 500s, JSON log format.
- `make test` after Alembic: **14 passed, 1 skipped**. The skipped test is the live migration round-trip, which needs `SMARTCART_TEST_DATABASE_URL`.
- `make lint`: **passes**. ruff check and format over `app/`, `tests/`, `migrations/`; mypy strict on `app/` (12 files).
- Live smoke test (uvicorn, no database): `/health` 200, `/health/ready` 503 with the error envelope, `/docs` 200.
- Docker (2026-11-16, Docker Desktop 29.6.2): **image builds** (`smartcart-api:dev`). Compose `postgres` (17-alpine) and `redis` (7-alpine) are healthy. The API container returned `/health` 200 and `/health/ready` 200 with the database ready.
- **Live migration round-trip: passed** (15 passed, 0 skipped) against `smartcart_test` in the compose Postgres.
- Compose `api` service: not started. The host already had `smartcart-ai-api-1` on port 8000, and running `docker compose up api` would recreate it.

## Local environment notes
- Host Postgres (Homebrew) is on 127.0.0.1:5432. Compose Postgres uses `POSTGRES_HOST_PORT`, default 5434.
- Removed 2026-11-16 at the user's request: `smartcart-ai-api-1` and `smartcart-ai-db-1` (containers only). Volume `smartcart-ai_pgdata` was kept, since it holds the old database's data (about 47 MB). Decide whether to delete that volume separately.
- `.env` was generated locally with new secrets (mode 600, gitignored). Do not commit it.

## Known issues
- Starlette's TestClient emits a deprecation warning recommending `httpx2`. Harmless today. Revisit when the test client is upgraded.
- The editable install prints setuptools' flat-layout warning about folders whose names match the package. Set explicit package discovery in `pyproject.toml` to silence it.
- Response headers are not added to 500 responses. The unhandled-exception path sits outside the request-ID middleware. The request ID is still in the body.

## External dependencies
- OCR provider — no credential. Interface plus a local fake for tests.
- LLM extraction provider — no credential. Same approach.
- Sentry or equivalent — DSN needed.
- S3-compatible private bucket — needed for staging.
- Managed PostgreSQL and Redis for staging — not chosen.
- Google and Apple sign-in — optional, needs developer accounts and client IDs.
- Payment provider — needs an account and a security review before implementation.
- Apple Developer Program and Google Play Console — needed for release builds.

## Manual configuration required
1. Copy `.env.example` to `.env`. Set `POSTGRES_PASSWORD` and `SMARTCART_SECRET_KEY` to new random values.
2. Start Docker Desktop before `make up`.
3. Install Flutter with a writable SDK directory, or run the Flutter commands outside the sandbox.

## Installed packages (approved by user 2026-11-16, alembic approved 2026-11-16)
Runtime: `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `psycopg[binary]`, `alembic` (1.20.1, with Mako 1.4.3).
Dev: `pytest`, `pytest-cov`, `httpx`, `ruff`, `mypy`.
Resolved versions in `backend/.venv`: fastapi 0.163.1, starlette 1.10.0, pydantic 2.14.3, sqlalchemy 2.0.58, psycopg 3.3.9, uvicorn 0.54.0, pytest 8.4.2, ruff 0.17.5, mypy 1.20.2.

No lockfile exists yet. Generating one (for example `uv lock` or `pip-compile`) is a pending decision, because it adds a tool.

## Migrations
- Alembic lives in `backend/migrations/`. `env.py` reads the URL from `SMARTCART_DATABASE_URL` through the application settings, and `Base.metadata` (in `app/core/database.py`) is the autogenerate target. Constraint naming is deterministic.
- Revision chain: `0001_baseline` (empty; schema starts with the Phase 2 auth tables).
- Verified: single head; offline `upgrade head --sql` and `downgrade --sql` emit correct SQL.
- Make targets: `make migrate` (upgrade to head) and `make migration MSG="..."` (autogenerate).
- **Not verified against a live database.** `tests/test_migrations.py` runs upgrade and downgrade round-trip only when `SMARTCART_TEST_DATABASE_URL` is set. The test refuses any database whose name lacks "test". A local PostgreSQL 17 server is accepting connections on 127.0.0.1:5432, but no credentials for it have been provided for this project.

## Next steps (pending)
- Live migration round-trip, once a disposable test database URL is provided.
- Docker image build and compose verification. Needs Docker Desktop running.
- Flutter scaffold. Needs the Flutter cache made writable, or an unsandboxed run.
- Git initialization, so `make lint` and `make test` gate commits.
