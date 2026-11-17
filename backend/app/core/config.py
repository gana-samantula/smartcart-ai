"""Application settings, loaded from `SMARTCART_*` environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    """Runtime configuration. Secrets are `SecretStr` so they never appear in `repr` or logs."""

    model_config = SettingsConfigDict(env_prefix="SMARTCART_", env_file=".env", extra="ignore")

    environment: Literal["development", "test", "staging", "production"] = "development"
    app_name: str = "SmartCart AI API"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    database_url: SecretStr = Field(
        description="SQLAlchemy URL, e.g. postgresql+psycopg://user:password@host:5432/db",
    )
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=10, ge=0, le=100)
    database_pool_timeout_seconds: int = Field(default=10, ge=1, le=60)
    database_connect_timeout_seconds: int = Field(default=5, ge=1, le=30)

    secret_key: SecretStr = Field(
        description="Token signing key. Load from Vault or the platform secret manager.",
    )

    cors_allowed_origins: list[str] = Field(default_factory=list)

    # Authentication. Access tokens are short-lived; refresh tokens rotate on every use.
    access_token_ttl_minutes: int = Field(default=15, ge=1, le=60)
    refresh_token_ttl_days: int = Field(default=30, ge=1, le=90)
    password_reset_ttl_minutes: int = Field(default=30, ge=5, le=120)
    auth_rate_limit_per_minute: int = Field(default=10, ge=1, le=1000)

    # "console" prints reset tokens to stdout (development only). "memory" records them for tests.
    # No production email provider exists yet, so staging and production refuse to start.
    email_backend: Literal["console", "memory"] = "console"

    @field_validator("secret_key")
    @classmethod
    def _require_strong_secret_key(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < MIN_SECRET_KEY_LENGTH:
            raise ValueError(
                f"SMARTCART_SECRET_KEY must be at least {MIN_SECRET_KEY_LENGTH} characters",
            )
        return value

    @model_validator(mode="after")
    def _check_email_backend(self) -> "Settings":
        required_environment = {"console": "development", "memory": "test"}[self.email_backend]
        if self.environment != required_environment:
            if self.environment in ("staging", "production"):
                raise ValueError(
                    f"No email provider is configured for {self.environment}. "
                    "Add a provider integration before deploying."
                )
            raise ValueError(
                f"SMARTCART_EMAIL_BACKEND={self.email_backend} requires the "
                f"{required_environment} environment, not {self.environment}"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings, read once from the environment."""
    return Settings()
