"""Authentication endpoints under /api/v1/auth."""

import math
from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.config import Settings
from app.core.errors import RateLimitedError
from app.core.rate_limit import RateLimiter
from app.modules.auth.dependencies import get_auth_service, get_current_auth
from app.modules.auth.schemas import (
    DeleteAccountRequest,
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.modules.auth.service import AuthContext, AuthService, TokenPair

router = APIRouter(prefix="/auth", tags=["auth"])


def _limit(scope: str) -> Callable[[Request], None]:
    """Cap attempts per client address per minute. Runs before any database or hashing work."""

    def enforce(request: Request) -> None:
        settings: Settings = request.app.state.settings
        limiter: RateLimiter = request.app.state.rate_limiter
        client_host = request.client.host if request.client else "unknown"
        retry_after = limiter.check(
            f"{scope}:{client_host}",
            limit=settings.auth_rate_limit_per_minute,
            window_seconds=60,
        )
        if retry_after is not None:
            raise RateLimitedError(headers={"Retry-After": str(math.ceil(retry_after))})

    return enforce


def _to_response(pair: TokenPair) -> TokenResponse:
    return TokenResponse(
        access_token=pair.access_token,
        access_expires_in=pair.access_expires_in,
        refresh_token=pair.refresh_token,
        refresh_expires_in=pair.refresh_expires_in,
    )


@router.post(
    "/register",
    status_code=201,
    summary="Create an account and sign in",
    dependencies=[Depends(_limit("auth.register"))],
)
def register(
    payload: RegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return _to_response(service.register(payload.email, payload.password, payload.display_name))


@router.post(
    "/login",
    summary="Sign in with email and password",
    dependencies=[Depends(_limit("auth.login"))],
)
def login(
    payload: LoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return _to_response(service.login(payload.email, payload.password))


@router.post("/refresh", summary="Rotate the session's tokens")
def refresh(
    payload: RefreshRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return _to_response(service.refresh(payload.refresh_token))


@router.post("/logout", status_code=204, summary="End the current session")
def logout(
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    service.logout(auth)


@router.post(
    "/password-reset/request",
    status_code=202,
    summary="Email a password reset link if the account exists",
    dependencies=[Depends(_limit("auth.password_reset"))],
)
def request_password_reset(
    payload: PasswordResetRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, str]:
    # Same response whether or not the account exists, so this cannot be used to probe emails.
    service.request_password_reset(payload.email)
    return {"status": "accepted"}


@router.post(
    "/password-reset/confirm",
    status_code=204,
    summary="Set a new password using a reset token",
)
def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    service.confirm_password_reset(payload.token, payload.new_password)


@router.post("/password/change", status_code=204, summary="Change password while signed in")
def change_password(
    payload: PasswordChangeRequest,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    service.change_password(auth, payload.current_password, payload.new_password)


@router.post(
    "/account/delete",
    status_code=204,
    summary="Delete the account and all of its data (requires password)",
)
def delete_account(
    payload: DeleteAccountRequest,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    service.delete_account(auth, payload.password)
