"""Profile endpoints under /api/v1/users."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.modules.auth.dependencies import get_current_auth
from app.modules.auth.service import AuthContext
from app.modules.users.schemas import UserResponse, UserUpdateRequest
from app.modules.users.service import update_display_name

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", summary="Current user's profile")
def read_me(auth: Annotated[AuthContext, Depends(get_current_auth)]) -> UserResponse:
    return UserResponse.model_validate(auth.user)


@router.patch("/me", summary="Update the current user's profile")
def update_me(
    payload: UserUpdateRequest,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
    db: Annotated[Session, Depends(get_session)],
) -> UserResponse:
    if "display_name" in payload.model_fields_set:
        update_display_name(db, auth.user, payload.display_name)
    return UserResponse.model_validate(auth.user)
