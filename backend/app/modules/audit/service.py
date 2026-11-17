"""Writes audit events. Callers commit, so each event shares a transaction with its action."""

import uuid

from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog


def record_event(db: Session, event: str, user_id: uuid.UUID | None) -> None:
    db.add(AuditLog(event=event, user_id=user_id))
