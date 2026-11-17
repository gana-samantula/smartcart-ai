"""FastAPI dependencies that resolve the signed-in user from a bearer token."""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.errors import UnauthorizedError
from app.modules.auth.service import AuthContext, AuthService

# auto_error=False so a missing or malformed header gets our envelope, not FastAPI's default.
_bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(
    request: Request,
    db: Annotated[Session, Depends(get_session)],
) -> AuthService:
    return AuthService(db, request.app.state.settings, request.app.state.email_sender)


def get_current_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthContext:
    if credentials is None:
        raise UnauthorizedError()
    context = service.authenticate_access_token(credentials.credentials)
    if context is None:
        raise UnauthorizedError()
    return context
