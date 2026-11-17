"""Database engine construction and access.

The engine is created once per process. Creating it opens no connections, so the
application can start before the database is reachable; readiness reports the state.
"""

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import Settings

# Deterministic constraint names. Migrations can then drop constraints by name on any database.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base for every ORM model. Alembic autogenerate reads `Base.metadata`."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def create_db_engine(settings: Settings) -> Engine:
    """Build the pooled SQLAlchemy engine from settings."""
    return create_engine(
        settings.database_url.get_secret_value(),
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout_seconds,
        pool_pre_ping=True,
        connect_args={"connect_timeout": settings.database_connect_timeout_seconds},
    )


def get_engine(request: Request) -> Engine:
    """FastAPI dependency that returns the engine owned by the application."""
    engine: Engine = request.app.state.engine
    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Sessions do not expire attributes on commit, so responses can read committed rows."""
    return sessionmaker(bind=engine, expire_on_commit=False)


def get_session(request: Request) -> Iterator[Session]:
    """One session per request. Closing it rolls back anything the service did not commit."""
    factory: sessionmaker[Session] = request.app.state.session_factory
    session = factory()
    try:
        yield session
    finally:
        session.close()
