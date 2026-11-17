"""Settings validation and secret handling."""

import pytest
from pydantic import ValidationError

from app.core.config import MIN_SECRET_KEY_LENGTH, Settings
from tests.conftest import TEST_SECRET_KEY, UNREACHABLE_DATABASE_URL


def test_defaults_are_safe_for_local_development(test_settings: Settings) -> None:
    assert test_settings.environment == "test"
    assert test_settings.log_level == "INFO"
    assert test_settings.cors_allowed_origins == []


def test_secret_key_shorter_than_minimum_is_rejected() -> None:
    short_key = "x" * (MIN_SECRET_KEY_LENGTH - 1)
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(
            _env_file=None,
            database_url=UNREACHABLE_DATABASE_URL,  # type: ignore[arg-type]
            secret_key=short_key,  # type: ignore[arg-type]
        )


def test_secrets_are_masked_in_repr(test_settings: Settings) -> None:
    rendered = repr(test_settings)
    assert TEST_SECRET_KEY not in rendered
    assert "smartcart:smartcart" not in rendered
