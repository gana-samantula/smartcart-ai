"""Request and response schemas for authentication. Every request model forbids unknown fields."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.modules.users.schemas import DisplayName

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
PASSWORD_MIN_LENGTH = 12
# Capped so a huge password cannot be used to make hashing expensive.
PASSWORD_MAX_LENGTH = 128

Email = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        min_length=3,
        max_length=320,
        pattern=EMAIL_PATTERN,
    ),
]
NewPassword = Annotated[
    str,
    StringConstraints(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH),
]
CurrentPassword = Annotated[str, StringConstraints(min_length=1, max_length=PASSWORD_MAX_LENGTH)]
OpaqueToken = Annotated[str, StringConstraints(min_length=20, max_length=200)]


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Email
    password: NewPassword
    display_name: DisplayName | None = None


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Email
    password: CurrentPassword


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: OpaqueToken


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105 - OAuth token type name, not a secret
    access_expires_in: int
    refresh_token: str
    refresh_expires_in: int


class PasswordResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Email


class PasswordResetConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: OpaqueToken
    new_password: NewPassword


class PasswordChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: CurrentPassword
    new_password: NewPassword


class DeleteAccountRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: CurrentPassword
