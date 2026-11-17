"""Authentication and profile API against a real PostgreSQL test database.

Set SMARTCART_TEST_DATABASE_URL to a disposable database whose name contains "test". The suite
migrates it to head once, and truncates the auth tables before each test.
"""

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.core.config import Settings
from app.core.security import hash_token
from app.integrations.email import MemoryEmailSender
from app.main import create_app
from tests.conftest import TEST_SECRET_KEY

TEST_DATABASE_URL = os.environ.get("SMARTCART_TEST_DATABASE_URL", "")
BACKEND_ROOT = Path(__file__).resolve().parents[1]
EMAIL = "shopper@example.com"
PASSWORD = "correct horse battery staple"
NEW_PASSWORD = "a different long passphrase"

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="SMARTCART_TEST_DATABASE_URL is not set",
)


def _alembic_config(url: str) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.attributes["sqlalchemy.url"] = url
    return config


@pytest.fixture(scope="session")
def database_url() -> str:
    name = make_url(TEST_DATABASE_URL).database or ""
    if "test" not in name:
        pytest.fail(f"Refusing to reset non-test database {name!r}")
    config = _alembic_config(TEST_DATABASE_URL)
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    return TEST_DATABASE_URL


@pytest.fixture(autouse=True)
def _clean_tables(database_url: str) -> None:
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE audit_logs, password_reset_tokens, auth_sessions, users "
                "RESTART IDENTITY CASCADE"
            )
        )
    engine.dispose()


def _settings(database_url: str, **overrides: int) -> Settings:
    return Settings(
        _env_file=None,
        environment="test",
        database_url=database_url,  # type: ignore[arg-type]
        secret_key=TEST_SECRET_KEY,  # type: ignore[arg-type]
        email_backend="memory",
        **overrides,  # type: ignore[arg-type]
    )


@pytest.fixture
def client(database_url: str) -> Iterator[TestClient]:
    app = create_app(_settings(database_url))
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def limited_client(database_url: str) -> Iterator[TestClient]:
    app = create_app(_settings(database_url, auth_rate_limit_per_minute=3))
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def _sent_emails(client: TestClient) -> MemoryEmailSender:
    sender = client.app.state.email_sender  # type: ignore[attr-defined]
    assert isinstance(sender, MemoryEmailSender)
    return sender


def _register(client: TestClient, email: str = EMAIL, password: str = PASSWORD) -> Any:
    return client.post("/api/v1/auth/register", json={"email": email, "password": password})


def _login(client: TestClient, email: str = EMAIL, password: str = PASSWORD) -> Any:
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _query(database_url: str, sql: str, **params: Any) -> list[Any]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            return list(connection.execute(text(sql), params).fetchall())
    finally:
        engine.dispose()


# Registration and login


def test_register_returns_tokens_and_the_profile_is_readable(client: TestClient) -> None:
    response = _register(client)
    assert response.status_code == 201
    tokens = response.json()
    assert tokens["token_type"] == "bearer"
    assert tokens["access_expires_in"] == 15 * 60

    me = client.get("/api/v1/users/me", headers=_bearer(tokens["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == EMAIL
    assert "password" not in me.text


def test_email_is_normalized_on_register_and_login(client: TestClient) -> None:
    assert _register(client, email="  Shopper@Example.COM ").status_code == 201
    assert _login(client, email="shopper@example.com").status_code == 200


def test_duplicate_email_is_rejected_regardless_of_case(client: TestClient) -> None:
    assert _register(client).status_code == 201
    response = _register(client, email="SHOPPER@example.com")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_already_registered"


def test_short_password_is_rejected_with_field_detail(client: TestClient) -> None:
    response = _register(client, password="too short")
    assert response.status_code == 422
    fields = [item["field"] for item in response.json()["error"]["details"]]
    assert "body.password" in fields


def test_unknown_request_fields_are_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": EMAIL, "password": PASSWORD, "role": "admin"},
    )
    assert response.status_code == 422


def test_login_failures_do_not_reveal_which_part_was_wrong(client: TestClient) -> None:
    _register(client)
    wrong_password = _login(client, password="not the password at all")
    unknown_email = _login(client, email="nobody@example.com")

    assert wrong_password.status_code == unknown_email.status_code == 401
    wrong_error = wrong_password.json()["error"]
    unknown_error = unknown_email.json()["error"]
    assert wrong_error["code"] == unknown_error["code"] == "invalid_credentials"
    assert wrong_error["message"] == unknown_error["message"]


def test_session_tokens_are_stored_only_as_digests(client: TestClient, database_url: str) -> None:
    access_token = _register(client).json()["access_token"]
    rows = _query(database_url, "SELECT access_token_hash FROM auth_sessions")
    assert [row[0] for row in rows] == [hash_token(access_token)]
    assert access_token not in rows[0][0]


# Protected endpoints


def test_protected_endpoint_without_a_token_returns_401_with_challenge(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "unauthorized"


def test_protected_endpoint_rejects_an_unknown_token(client: TestClient) -> None:
    response = client.get("/api/v1/users/me", headers=_bearer("not-a-real-token-value-0000"))
    assert response.status_code == 401


# Refresh and logout


def test_refresh_issues_new_tokens_and_retires_the_old_access_token(client: TestClient) -> None:
    first = _register(client).json()
    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert rotated.status_code == 200
    second = rotated.json()

    assert (
        client.get("/api/v1/users/me", headers=_bearer(second["access_token"])).status_code == 200
    )
    assert client.get("/api/v1/users/me", headers=_bearer(first["access_token"])).status_code == 401


def test_replaying_a_rotated_refresh_token_revokes_the_session(
    client: TestClient,
    database_url: str,
) -> None:
    first = _register(client).json()
    rotated = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
    ).json()

    replay = client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert replay.status_code == 401

    # The legitimate client's newest tokens are dead too, because the whole session was revoked.
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": rotated["refresh_token"]}
        ).status_code
        == 401
    )
    assert (
        client.get("/api/v1/users/me", headers=_bearer(rotated["access_token"])).status_code == 401
    )
    events = [row[0] for row in _query(database_url, "SELECT event FROM audit_logs")]
    assert "auth.refresh_replay_detected" in events


def test_logout_ends_the_current_session(client: TestClient) -> None:
    token = _register(client).json()["access_token"]
    assert client.post("/api/v1/auth/logout", headers=_bearer(token)).status_code == 204
    assert client.get("/api/v1/users/me", headers=_bearer(token)).status_code == 401


# Password recovery


def test_reset_request_is_silent_for_unknown_emails(client: TestClient) -> None:
    response = client.post("/api/v1/auth/password-reset/request", json={"email": "x@example.com"})
    assert response.status_code == 202
    assert _sent_emails(client).sent == []


def test_password_reset_replaces_the_password_and_ends_all_sessions(client: TestClient) -> None:
    old_access = _register(client).json()["access_token"]
    assert (
        client.post("/api/v1/auth/password-reset/request", json={"email": EMAIL}).status_code == 202
    )

    sent = _sent_emails(client).sent
    assert len(sent) == 1
    assert sent[0].recipient == EMAIL
    reset_token = sent[0].reset_token

    confirm = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": NEW_PASSWORD},
    )
    assert confirm.status_code == 204

    assert _login(client, password=PASSWORD).status_code == 401
    assert _login(client, password=NEW_PASSWORD).status_code == 200
    assert client.get("/api/v1/users/me", headers=_bearer(old_access)).status_code == 401


def test_reset_token_cannot_be_used_twice(client: TestClient) -> None:
    _register(client)
    client.post("/api/v1/auth/password-reset/request", json={"email": EMAIL})
    reset_token = _sent_emails(client).sent[0].reset_token

    first = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": NEW_PASSWORD},
    )
    second = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": "yet another passphrase"},
    )
    assert first.status_code == 204
    assert second.status_code == 400
    assert second.json()["error"]["code"] == "invalid_reset_token"


# Password change and account deletion


def test_password_change_needs_the_current_password_and_signs_out_other_devices(
    client: TestClient,
) -> None:
    this_device = _register(client).json()["access_token"]
    other_device = _login(client).json()["access_token"]

    wrong = client.post(
        "/api/v1/auth/password/change",
        headers=_bearer(this_device),
        json={"current_password": "not my password", "new_password": NEW_PASSWORD},
    )
    assert wrong.status_code == 400
    assert wrong.json()["error"]["code"] == "invalid_current_password"

    changed = client.post(
        "/api/v1/auth/password/change",
        headers=_bearer(this_device),
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
    )
    assert changed.status_code == 204
    assert client.get("/api/v1/users/me", headers=_bearer(other_device)).status_code == 401
    assert client.get("/api/v1/users/me", headers=_bearer(this_device)).status_code == 200


def test_account_deletion_needs_the_password_and_removes_the_account(
    client: TestClient,
    database_url: str,
) -> None:
    token = _register(client).json()["access_token"]

    refused = client.post(
        "/api/v1/auth/account/delete",
        headers=_bearer(token),
        json={"password": "wrong password value"},
    )
    assert refused.status_code == 400

    deleted = client.post(
        "/api/v1/auth/account/delete",
        headers=_bearer(token),
        json={"password": PASSWORD},
    )
    assert deleted.status_code == 204
    assert client.get("/api/v1/users/me", headers=_bearer(token)).status_code == 401
    assert _login(client).status_code == 401
    assert _query(database_url, "SELECT count(*) FROM users")[0][0] == 0
    assert _query(database_url, "SELECT count(*) FROM auth_sessions")[0][0] == 0
    # The audit trail records the deletion but keeps no email address.
    assert (
        _query(
            database_url,
            "SELECT count(*) FROM audit_logs WHERE event = 'auth.account_deleted'",
        )[0][0]
        == 1
    )


# Profile and audit


def test_profile_update_sets_and_clears_the_display_name(client: TestClient) -> None:
    token = _register(client).json()["access_token"]

    set_name = client.patch(
        "/api/v1/users/me", headers=_bearer(token), json={"display_name": "  Gana  "}
    )
    assert set_name.json()["display_name"] == "Gana"

    untouched = client.patch("/api/v1/users/me", headers=_bearer(token), json={})
    assert untouched.json()["display_name"] == "Gana"

    cleared = client.patch("/api/v1/users/me", headers=_bearer(token), json={"display_name": None})
    assert cleared.json()["display_name"] is None


def test_sensitive_actions_are_recorded_in_order(client: TestClient, database_url: str) -> None:
    token = _register(client).json()["access_token"]
    _login(client)
    client.post("/api/v1/auth/logout", headers=_bearer(token))

    events = [
        row[0] for row in _query(database_url, "SELECT event FROM audit_logs ORDER BY occurred_at")
    ]
    assert events == ["auth.registered", "auth.login", "auth.logout"]


def test_repeated_attempts_are_rate_limited(limited_client: TestClient) -> None:
    for _ in range(3):
        assert _login(limited_client, password="wrong password value").status_code == 401

    blocked = _login(limited_client, password="wrong password value")
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"
    assert int(blocked.headers["Retry-After"]) >= 1
