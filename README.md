# SmartCart AI

Grocery and household price intelligence for US shoppers. Users confirm their receipts, SmartCart builds a price history from those confirmed purchases, and it recommends where to buy a shopping list at the lowest estimated cost.

Status: early foundation. See `docs/implementation-progress.md`.

## Repository layout

| Path | Purpose |
| --- | --- |
| `backend/` | FastAPI modular monolith, Alembic migrations, tests |
| `frontend/flutter_app/` | Flutter client (not yet created) |
| `ai/` | Receipt parsing, product matching, price intelligence, evaluation sets |
| `docs/` | Architecture, decisions, progress |
| `infrastructure/`, `scripts/` | Deployment and tooling (not yet created) |

## Local setup (backend)

Prerequisites: Python 3.12, Docker Desktop, GNU make.

```sh
cp .env.example .env          # then set POSTGRES_PASSWORD and SMARTCART_SECRET_KEY
make install                  # creates backend/.venv and installs dev dependencies
make up                       # starts Postgres and Redis
make test
make run                      # http://127.0.0.1:8000/docs
```

Health checks:
- `GET /health` — the process is up.
- `GET /health/ready` — the database is reachable (503 otherwise).

## Quality gates

- `make lint` — ruff and mypy.
- `make test` — pytest.

Both must pass before a commit.

## Documentation

- `CLAUDE.md` — conventions and organization policy for contributors and AI assistants.
- `docs/architecture.md` — architecture decisions.
- `docs/implementation-progress.md` — live status, test results, known issues, manual steps.

## Data and privacy

Receipts can contain payment card data. Test fixtures are synthetic. Production secrets come from the secret manager and are never committed.
