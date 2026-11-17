"""Authentication errors. Messages stay generic where they could reveal account state."""

from app.core.errors import BadRequestError, ConflictError, UnauthorizedError


class EmailAlreadyRegisteredError(ConflictError):
    code = "email_already_registered"
    default_message = "An account with this email already exists."


class InvalidCredentialsError(UnauthorizedError):
    code = "invalid_credentials"
    default_message = "Email or password is incorrect."


class InvalidRefreshTokenError(UnauthorizedError):
    code = "invalid_refresh_token"
    default_message = "Your session has ended. Sign in again."


class InvalidResetTokenError(BadRequestError):
    code = "invalid_reset_token"
    default_message = "This reset link is invalid or has expired."


class InvalidCurrentPasswordError(BadRequestError):
    code = "invalid_current_password"
    default_message = "Current password is incorrect."
