"""Alembic environment. Migrations use the same settings and metadata as the application."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import get_settings
from app.core.database import Base

# Importing the model modules registers their tables on Base.metadata for autogenerate.
from app.modules.audit import models as _audit_models  # noqa: F401
from app.modules.auth import models as _auth_models  # noqa: F401
from app.modules.users import models as _users_models  # noqa: F401

config = context.config

# Keep application loggers enabled when Alembic runs inside the test process.
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _database_url() -> str:
    """Prefer an explicit URL set programmatically (tests), otherwise use application settings."""
    override = config.attributes.get("sqlalchemy.url")
    if isinstance(override, str) and override:
        return override
    return get_settings().database_url.get_secret_value()


def run_migrations_offline() -> None:
    """Emit SQL to stdout without connecting to a database (`alembic upgrade head --sql`)."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations over a live connection. Each run uses its own short-lived engine."""
    engine = create_engine(_database_url(), poolclass=pool.NullPool)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
