"""Health endpoints, request IDs and the shared error envelope."""

import re
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.config import Settings
from app.core.errors import NotFoundError
from app.main import create_app

SECRET_MARKER = "hunter2-do-not-leak"
SUBMITTED_VALUE = "super-secret-submitted-value"


class EchoPayload(BaseModel):
    email: str
    password: str


@pytest.fixture
def app(test_settings: Settings) -> FastAPI:
    application = create_app(test_settings)

    @application.get("/_test/not-found")
    def _not_found() -> None:
        raise NotFoundError("Receipt not found.")

    @application.post("/_test/echo")
    def _echo(payload: EchoPayload) -> dict[str, str]:
        return {"email": payload.email}

    @application.get("/_test/crash")
    def _crash() -> None:
        raise RuntimeError(f"connection failed: password={SECRET_MARKER}")

    return application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_liveness_reports_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_response_carries_generated_request_id(client: TestClient) -> None:
    response = client.get("/health")
    assert re.fullmatch(r"[0-9a-f]{32}", response.headers["X-Request-ID"])


def test_valid_client_request_id_is_echoed(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "trace-abc.123"})
    assert response.headers["X-Request-ID"] == "trace-abc.123"


def test_invalid_client_request_id_is_replaced(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "has spaces and\tcontrols"})
    assert response.headers["X-Request-ID"] != "has spaces and\tcontrols"
    assert re.fullmatch(r"[0-9a-f]{32}", response.headers["X-Request-ID"])


def test_readiness_reports_unavailable_when_database_is_down(client: TestClient) -> None:
    response = client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()["error"]
    assert body["code"] == "service_unavailable"
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert "127.0.0.1" not in response.text


def test_app_error_uses_error_envelope(client: TestClient) -> None:
    response = client.get("/_test/not-found")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "not_found"
    assert error["message"] == "Receipt not found."
    assert error["details"] == {}


def test_unknown_route_uses_error_envelope(client: TestClient) -> None:
    response = client.get("/no-such-route")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_validation_error_lists_fields_without_submitted_values(client: TestClient) -> None:
    response = client.post(
        "/_test/echo",
        json={"email": "shopper@example.com", "password": [SUBMITTED_VALUE]},
    )
    assert response.status_code == 422
    body = response.json()["error"]
    assert body["code"] == "validation_error"
    assert body["details"][0]["field"] == "body.password"
    assert SUBMITTED_VALUE not in response.text
    assert "shopper@example.com" not in response.text


def test_unexpected_error_hides_internal_details(client: TestClient) -> None:
    response = client.get("/_test/crash")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert SECRET_MARKER not in response.text
