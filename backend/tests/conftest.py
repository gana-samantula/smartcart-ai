"""Shared test fixtures.

All values here are test-only. The database URL points at a closed local port, so no
test can reach a real database. Secrets are fake and never leave the test process.
"""

import os

import pytest

from app.core.config import Settings

TEST_SECRET_KEY = "test-only-signing-key-not-a-secret-0123456789"
UNREACHABLE_DATABASE_URL = "postgresql+psycopg://smartcart:smartcart@127.0.0.1:1/smartcart_test"

# Set before any test imports `app.main`, which reads settings at import time. These are forced,
# not defaulted, so a developer's shell (for example one that sourced `.env`) cannot point the
# test process at a real database or switch it out of the test environment.
os.environ["SMARTCART_ENVIRONMENT"] = "test"
os.environ["SMARTCART_DATABASE_URL"] = UNREACHABLE_DATABASE_URL
os.environ["SMARTCART_SECRET_KEY"] = TEST_SECRET_KEY
os.environ["SMARTCART_EMAIL_BACKEND"] = "memory"


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        _env_file=None,
        environment="test",
        database_url=UNREACHABLE_DATABASE_URL,  # type: ignore[arg-type]
        secret_key=TEST_SECRET_KEY,  # type: ignore[arg-type]
        email_backend="memory",
    )
