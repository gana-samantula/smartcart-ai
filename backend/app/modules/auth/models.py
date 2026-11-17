"""Session and password-reset persistence models.

Both tables store SHA-256 digests of tokens, never the tokens themselves.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.common.models import TimestampMixin
from app.core.database import Base

TOKEN_DIGEST_LENGTH = 64  # SHA-256 hex


class AuthSession(TimestampMixin, Base):
    """One signed-in device. Refresh rotates both tokens in place.

    `previous_refresh_token_hash` holds the refresh digest from before the last rotation. Seeing
    it again means a rotated-out token was replayed, so the session is revoked.
    """

    __tablename__ = "auth_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    access_token_hash: Mapped[str] = mapped_column(
        String(TOKEN_DIGEST_LENGTH),
        unique=True,
    )
    access_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    refresh_token_hash: Mapped[str] = mapped_column(
        String(TOKEN_DIGEST_LENGTH),
        unique=True,
    )
    previous_refresh_token_hash: Mapped[str | None] = mapped_column(
        String(TOKEN_DIGEST_LENGTH),
        nullable=True,
        index=True,
    )
    refresh_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PasswordResetToken(TimestampMixin, Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(TOKEN_DIGEST_LENGTH), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
