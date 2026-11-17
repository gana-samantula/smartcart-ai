"""Audit log persistence model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.common.time import utc_now
from app.core.database import Base


class AuditLog(Base):
    """One row per sensitive action. Records event names and user IDs only, never secrets.

    `user_id` has no foreign key on purpose: the trail survives account deletion. The ID is
    still personal data, so retention of this table needs a documented policy.
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
    )
    event: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
