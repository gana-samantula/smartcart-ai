BACKEND := backend
PYTHON ?= python3.12
VENV := $(BACKEND)/.venv
BIN := $(VENV)/bin

.PHONY: install lint format test run migrate migration up down

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e "./$(BACKEND)[dev]"

lint:
	cd $(BACKEND) && .venv/bin/ruff check .
	cd $(BACKEND) && .venv/bin/ruff format --check .
	cd $(BACKEND) && .venv/bin/mypy

format:
	cd $(BACKEND) && .venv/bin/ruff format .
	cd $(BACKEND) && .venv/bin/ruff check --fix .

test:
	cd $(BACKEND) && .venv/bin/pytest

run:
	cd $(BACKEND) && .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

migrate:
	cd $(BACKEND) && .venv/bin/alembic upgrade head

# Usage: make migration MSG="add users table"
migration:
	cd $(BACKEND) && .venv/bin/alembic revision --autogenerate -m "$(MSG)"

up:
	docker compose up -d postgres redis

down:
	docker compose down
