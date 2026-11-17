# SmartCart AI — Implementation Progress

Last updated: 2026-11-17

## Current phase
**Phase 2 — Authentication (backend and sign-in screens done; deep links and profile screens pending).** Phase 1 remaining work: GitHub Actions CI, Redis and Celery worker wiring, lockfile decision.

## Repository
- Remote: `github.com/gana-samantula/smartcart-ai`, branch `main`, at `d99d533`.
- Commits: `304b919` (backend foundation, auth API, migrations, Flutter sign-in), `d99d533` (pre-commit hook chain).
- Commits are authored with the personal identity. The clone has a local git identity and a local `core.sshCommand` that uses the personal key `~/.ssh/id_ed25519_personal`.
- The project folder (`smartcart-ai`) is the working copy. The git repo is the sibling clone `smartcart-ai-repo`.

## Pre-commit hooks
- `.pre-commit-config.yaml` runs `make lint` and `make test` before every commit.
- Installed in the clone with `pre-commit` 4.7.0 (installed to the user site-packages with `pip install --user`). Per clone: `pip install pre-commit && pre-commit install`.
- Verified: `pre-commit run --all-files` passes in the clone.
- The database-backed tests skip in the hook, because `SMARTCART_TEST_DATABASE_URL` isn't set there. Full database runs are done manually (below).

## Phase 2 backend
- Endpoints (`/api/v1`): `auth/register` (201), `auth/login`, `auth/refresh`, `auth/logout` (204), `auth/password-reset/request` (202), `auth/password-reset/confirm` (204), `auth/password/change` (204), `auth/account/delete` (204, POST), `users/me` GET and PATCH.
- Migration `0002_auth_users`: `users`, `auth_sessions`, `password_reset_tokens`, `audit_logs`. `alembic check` reports no drift.
- No new packages. Passwords use stdlib scrypt and tokens are opaque (ADR-014).
- Email: `console` backend for development (prints reset tokens to stdout). `memory` for tests. Staging and production refuse to start until a provider is added.
- Rate limiting: in-process sliding window on the auth endpoints, 10 per minute per client IP. It is per process only.
- Known limits, decisions and trade-offs: `docs/security.md`.

## Phase 2 Flutter
- Screens: splash, welcome, sign in, register, forgot password, reset password (paste the code from the email). Home shows the signed-in user and a working sign-out. The router redirects by auth state.
- Data layer (`lib/features/auth/`): `AuthApi` (Dio, all errors become `AuthFailure`), `AuthInterceptor` (adds the bearer token, retries a 401 once after refreshing), `SessionRefresher` (one rotation at a time, so concurrent 401s can't trigger replay detection), `HttpAuthRepository`, `SecureTokenStore` (flutter_secure_storage).
- Base URL: `--dart-define=SMARTCART_API_URL=...`. Default `http://127.0.0.1:8000`. Android emulators need `http://10.0.2.2:8000`.
- Android: `INTERNET` is in the main manifest. Cleartext http is allowed only in the debug manifest.
- Web: `web/` platform folder added. Served in Chrome on `localhost:5050` with CORS.
- Packages: `flutter_riverpod` 3.5.0, `go_router` 18.1.4, `dio` 5.11.1, `flutter_secure_storage` 11.2.0, `freezed_annotation` 3.1.0, `json_annotation` 4.12.0, `material_ui` 1.11.1 (the SDK analyzer recommends it over the deprecated `flutter/material`). Dev: `freezed` 4.0.3, `json_serializable` 6.15.2, `build_runner` 2.17.1.

## Test results
**Backend**
- `make test` without a database: **35 passed, 21 skipped**.
- `make test` against `smartcart_test` (compose Postgres): **56 passed, 0 skipped**. Covers the auth API flow, refresh replay, password reset and change, account deletion, rate limiting, the audit trail, and the migration round-trip.
- `make lint`: passes (ruff check, ruff format, mypy strict on `app/`).
- Tests force their own environment (`SMARTCART_ENVIRONMENT=test`, a non-development database URL), so a sourced `.env` can't redirect them.

**Flutter**
- `flutter analyze`: no issues.
- `flutter test`: 16 passed, 2 skipped (live).
- Live API test (`--dart-define=SMARTCART_LIVE_API=http://127.0.0.1:8000`): 2 passed. Covers register, restore, refresh after an expired access token, sign-out, sign-in, delete, and the wrong-password error code. Each run creates and deletes its own account in the development database.

**Docker** (Docker Desktop 29.6.2)
- Image `smartcart-api:dev` builds. Compose `postgres` (17-alpine) and `redis` (7-alpine) are healthy.
- The API container returned `/health` 200 and `/health/ready` 200.
- Compose `api` service is not started by `make up`. The host has no conflicting containers now, but the service has not been re-run since the old containers were removed.

**Migrations**
- Live round-trip against `smartcart_test`: passed (15 passed, 0 skipped).

## Local environment notes
- Host Postgres (Homebrew) is on 127.0.0.1:5432. Compose Postgres uses `POSTGRES_HOST_PORT`, default 5434.
- Removed 2026-11-16 at the user's request: `smartcart-ai-api-1` and `smartcart-ai-db-1` (containers only). Volume `smartcart-ai_pgdata` was kept, since it holds about 47 MB of old data. Decide whether to delete it.
- `.env` was generated locally with new secrets (mode 600, gitignored). Do not commit it.
- Backend venv exists in both the project folder and the clone (`backend/.venv`, gitignored).

## Not verified
- Running the Flutter app on a device or simulator. Android SDK and Xcode are not set up. `flutter doctor`: Android SDK missing; Xcode incomplete and CocoaPods missing.
- iOS App Transport Security for plain http to the local API.
- GitHub Actions CI (no workflow file yet).

## Known issues
- Starlette's TestClient emits a deprecation warning recommending `httpx2`. Harmless today.
- The editable install prints setuptools' flat-layout warning. Set explicit package discovery in `pyproject.toml` to silence it.
- Response headers are not added to 500 responses. The unhandled-exception path sits outside the request-ID middleware. The request ID is still in the body.
- `flutter_lints` came from the Flutter template, not the approved package list.

## Remaining work
**Phase 1 (rest):** GitHub Actions workflows for backend lint and tests, Flutter analysis, dependency audit, and image build. Redis and Celery worker wiring. Lockfile decision (`uv lock` or `pip-compile`), which adds a tool and needs approval.

**Phase 2 (rest):** deep-link handling for the password-reset code. Settings and profile screens (currently placeholders). Run on Android and iOS. Live migration check is done; the compose `api` service still needs a re-run.

**Phase 3:** Receipt upload with file and image validation, private S3-compatible storage, duplicate detection by content hash, processing job records.

**Phase 4:** OCR and LLM provider interfaces with local fakes, card-number masking before any OCR or LLM call, strict schema validation, extraction evaluation set, receipt review screens.

**Phase 5:** Catalog (brands, categories, products, variants), product matching with ranked candidates and confidence.

**Phase 6:** Verified price observations, deterministic price statistics and confidence levels.

**Phase 7:** Shopping lists, three recommendation strategies with tests.

**Phase 8:** Analytics, price alerts and notifications.

**Phase 9:** Subscription model, entitlements, usage limits, payment provider interface (requires security review under `/billing`).

**Phase 10:** Security hardening, integration and end-to-end tests, deployment configuration, operations and privacy documents, release preparation.

Documents not yet written: `product-requirements.md`, `database-design.md`, `api-specification.md`, `privacy.md`, `ai-processing.md`, `testing-strategy.md`, `deployment.md`, `operations-runbook.md`, `roadmap.md`. (`security.md` exists.)

## External dependencies
- OCR provider — no credential. Interface plus a local fake for tests.
- LLM extraction provider — no credential. Same approach.
- Sentry or equivalent — DSN needed.
- S3-compatible private bucket — needed for staging.
- Managed PostgreSQL and Redis for staging — not chosen.
- Google and Apple sign-in — optional, needs developer accounts and client IDs.
- Payment provider — needs an account and a security review before implementation.
- Apple Developer Program and Google Play Console — needed for release builds.

## Installed packages (backend)
Runtime (approved 2026-11-16): `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `psycopg[binary]`, `alembic`.
Dev (approved 2026-11-16): `pytest`, `pytest-cov`, `httpx`, `ruff`, `mypy`.
Resolved in `backend/.venv`: fastapi 0.163.2, starlette 1.10.0, pydantic 2.14.3, sqlalchemy 2.0.58, psycopg 3.3.9, uvicorn 0.54.0, alembic 1.20.1, pytest 8.4.2, ruff 0.17.5, mypy 1.20.2.

Host tool (approved 2026-11-17, not a project dependency): `pre-commit` 4.7.0.

No lockfile exists yet.

## Migrations
- Alembic lives in `backend/migrations/`. `env.py` reads the URL from `SMARTCART_DATABASE_URL` through the application settings, and `Base.metadata` (in `app/core/database.py`) is the autogenerate target. Constraint naming is deterministic.
- Revision chain: `0001_baseline` (empty), then `0002_auth_users`. Single head.
- Make targets: `make migrate` (upgrade to head) and `make migration MSG="..."` (autogenerate).
- `tests/test_migrations.py` runs the round-trip only when `SMARTCART_TEST_DATABASE_URL` is set. The test refuses any database whose name lacks "test".
