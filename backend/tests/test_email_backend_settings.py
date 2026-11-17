"""Email backends are only allowed in the environments they are built for."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from tests.conftest import TEST_SECRET_KEY, UNREACHABLE_DATABASE_URL


def _settings(environment: str, email_backend: str) -> Settings:
    return Settings(
        _env_file=None,
        environment=environment,  # type: ignore[arg-type]
        database_url=UNREACHABLE_DATABASE_URL,  # type: ignore[arg-type]
        secret_key=TEST_SECRET_KEY,  # type: ignore[arg-type]
        email_backend=email_backend,  # type: ignore[arg-type]
    )


def test_console_backend_is_allowed_in_development() -> None:
    assert _settings("development", "console").email_backend == "console"


def test_memory_backend_is_allowed_in_tests() -> None:
    assert _settings("test", "memory").email_backend == "memory"


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_deployed_environments_refuse_to_start_without_a_provider(environment: str) -> None:
    with pytest.raises(ValidationError, match="No email provider is configured"):
        _settings(environment, "console")


def test_console_backend_is_refused_in_tests() -> None:
    with pytest.raises(ValidationError, match="requires the development environment"):
        _settings("test", "console")
