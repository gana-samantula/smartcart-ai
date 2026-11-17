"""Alembic migration chain.

The single-head check needs no database. The round-trip test runs only when
SMARTCART_TEST_DATABASE_URL is set, and it refuses any database whose name does not
contain "test", because it downgrades to base.
"""

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

BACKEND_ROOT = Path(__file__).resolve().parents[1]
HEAD_REVISION = "0002_auth_users"
TEST_DATABASE_URL = os.environ.get("SMARTCART_TEST_DATABASE_URL", "")


def _alembic_config(url: str | None = None) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    if url is not None:
        config.attributes["sqlalchemy.url"] = url
    return config


def test_migration_chain_has_a_single_head() -> None:
    directory = ScriptDirectory.from_config(_alembic_config())
    assert directory.get_heads() == [HEAD_REVISION]


@pytest.mark.skipif(not TEST_DATABASE_URL, reason="SMARTCART_TEST_DATABASE_URL is not set")
def test_upgrade_and_downgrade_round_trip() -> None:
    database_name = make_url(TEST_DATABASE_URL).database or ""
    if "test" not in database_name:
        pytest.fail(f"Refusing to run migration tests against non-test database {database_name!r}")

    config = _alembic_config(TEST_DATABASE_URL)
    engine = create_engine(TEST_DATABASE_URL)
    try:
        command.downgrade(config, "base")
        command.upgrade(config, "head")
        with engine.connect() as connection:
            version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
        assert version == HEAD_REVISION

        command.downgrade(config, "base")
        with engine.connect() as connection:
            remaining = connection.execute(text("SELECT count(*) FROM alembic_version")).scalar()
        assert remaining == 0
    finally:
        engine.dispose()
