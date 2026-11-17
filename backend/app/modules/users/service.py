"""Profile changes for an authenticated user."""

from sqlalchemy.orm import Session

from app.modules.users.models import User


def update_display_name(db: Session, user: User, display_name: str | None) -> None:
    user.display_name = display_name
    db.commit()
