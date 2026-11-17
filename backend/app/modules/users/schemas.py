"""API schemas for user profiles. Persistence models are never returned directly."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

DisplayName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str | None
    created_at: datetime


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Only fields present in the request are changed. An explicit null clears the name.
    display_name: DisplayName | None = None
