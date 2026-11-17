"""Application errors and centralized exception handlers.

Every error response uses one envelope so clients can rely on a single shape:

    {"error": {"code": "...", "message": "...", "details": {...}, "request_id": "..."}}

Validation details list the field location and message only. Submitted values are
never echoed back, because request bodies can contain passwords or receipt text.
"""

import logging
from http import HTTPStatus
from typing import Any, ClassVar, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

GENERIC_ERROR_MESSAGE = "An unexpected error occurred."


class AppError(Exception):
    """Base class for errors that map to a documented HTTP response."""

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    code: str = "internal_error"
    default_message: str = GENERIC_ERROR_MESSAGE
    default_headers: ClassVar[dict[str, str]] = {}

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.details = details or {}
        self.headers = headers or dict(self.default_headers)
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code = HTTPStatus.BAD_REQUEST
    code = "bad_request"
    default_message = "The request could not be processed."


class NotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND
    code = "not_found"
    default_message = "The requested resource was not found."


class ConflictError(AppError):
    status_code = HTTPStatus.CONFLICT
    code = "conflict"
    default_message = "The request conflicts with the current state of the resource."


class ServiceUnavailableError(AppError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "service_unavailable"
    default_message = "A dependent service is temporarily unavailable."


class UnauthorizedError(AppError):
    status_code = HTTPStatus.UNAUTHORIZED
    code = "unauthorized"
    default_message = "Authentication is required."
    default_headers: ClassVar[dict[str, str]] = {"WWW-Authenticate": "Bearer"}


class RateLimitedError(AppError):
    status_code = HTTPStatus.TOO_MANY_REQUESTS
    code = "rate_limited"
    default_message = "Too many requests. Try again later."


def _error_body(
    code: str,
    message: str,
    details: dict[str, Any] | list[dict[str, str]],
    request_id: str | None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": request_id,
        }
    }


def _request_id(request: Request) -> str | None:
    value: object = getattr(request.state, "request_id", None)
    return value if isinstance(value, str) else None


def _http_error_code(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).name.lower()
    except ValueError:
        return "http_error"


async def _handle_app_error(request: Request, exc: Exception) -> JSONResponse:
    error = cast(AppError, exc)
    return JSONResponse(
        status_code=error.status_code,
        content=_error_body(error.code, error.message, error.details, _request_id(request)),
        headers=error.headers,
    )


async def _handle_http_exception(request: Request, exc: Exception) -> JSONResponse:
    http_error = cast(StarletteHTTPException, exc)
    message = http_error.detail if isinstance(http_error.detail, str) else "Request failed."
    return JSONResponse(
        status_code=http_error.status_code,
        content=_error_body(
            _http_error_code(http_error.status_code),
            message,
            {},
            _request_id(request),
        ),
        headers=http_error.headers,
    )


async def _handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    validation_error = cast(RequestValidationError, exc)
    details = [
        {"field": ".".join(str(part) for part in item["loc"]), "message": item["msg"]}
        for item in validation_error.errors()
    ]
    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content=_error_body(
            "validation_error",
            "The request failed validation.",
            details,
            _request_id(request),
        ),
    )


async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # Log the type and traceback server-side only. The client gets no internal detail.
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        extra={"request_id": _request_id(request), "error_type": type(exc).__name__},
    )
    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content=_error_body("internal_error", GENERIC_ERROR_MESSAGE, {}, _request_id(request)),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach the envelope handlers to an application."""
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)
