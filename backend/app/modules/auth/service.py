"""Authentication use cases: registration, sessions, password recovery and account deletion.

Routers call these methods. Each method runs in one transaction. Sensitive actions write an audit
event in the same transaction, so an action and its record succeed or fail together.
"""

import uuid
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.time import utc_now
from app.core.config import Settings
from app.core.security import (
    dummy_password_hash,
    hash_password,
    hash_token,
    new_token,
    verify_password,
)
from app.integrations.email import EmailSender
from app.modules.audit.service import record_event
from app.modules.auth.errors import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidCurrentPasswordError,
    InvalidRefreshTokenError,
    InvalidResetTokenError,
)
from app.modules.auth.models import AuthSession, PasswordResetToken
from app.modules.users.models import User


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    access_expires_in: int
    refresh_expires_in: int


@dataclass(frozen=True)
class AuthContext:
    """The authenticated user and the session that presented a valid access token."""

    user: User
    session: AuthSession


def normalize_email(email: str) -> str:
    return email.strip().lower()


class AuthService:
    def __init__(self, db: Session, settings: Settings, email_sender: EmailSender) -> None:
        self._db = db
        self._settings = settings
        self._email_sender = email_sender

    def register(self, email: str, password: str, display_name: str | None) -> TokenPair:
        user = User(
            email=normalize_email(email),
            password_hash=hash_password(password),
            display_name=display_name,
            is_active=True,
        )
        self._db.add(user)
        try:
            self._db.flush()
        except IntegrityError as exc:
            # Two concurrent registrations for one email: the unique constraint decides.
            self._db.rollback()
            raise EmailAlreadyRegisteredError() from exc
        pair = self._open_session(user)
        record_event(self._db, "auth.registered", user.id)
        self._db.commit()
        return pair

    def login(self, email: str, password: str) -> TokenPair:
        user = self._user_by_email(email)
        if user is None:
            # Run a full hash check so unknown emails take as long as real ones.
            verify_password(password, dummy_password_hash())
            record_event(self._db, "auth.login_failed", None)
            self._db.commit()
            raise InvalidCredentialsError()
        password_ok = verify_password(password, user.password_hash)
        if not (password_ok and user.is_active):
            record_event(self._db, "auth.login_failed", user.id)
            self._db.commit()
            raise InvalidCredentialsError()
        pair = self._open_session(user)
        record_event(self._db, "auth.login", user.id)
        self._db.commit()
        return pair

    def refresh(self, refresh_token: str) -> TokenPair:
        digest = hash_token(refresh_token)
        session = self._db.scalar(
            select(AuthSession).where(AuthSession.refresh_token_hash == digest)
        )
        if session is None:
            self._revoke_if_replayed(digest)
            raise InvalidRefreshTokenError()

        now = utc_now()
        if session.revoked_at is not None or session.refresh_expires_at <= now:
            raise InvalidRefreshTokenError()
        user = self._db.get(User, session.user_id)
        if user is None or not user.is_active:
            raise InvalidRefreshTokenError()

        access_token = new_token()
        new_refresh_token = new_token()
        session.previous_refresh_token_hash = session.refresh_token_hash
        session.refresh_token_hash = hash_token(new_refresh_token)
        session.access_token_hash = hash_token(access_token)
        session.access_expires_at = now + self._access_ttl()
        session.refresh_expires_at = now + self._refresh_ttl()
        session.last_used_at = now
        self._db.commit()
        return self._token_pair(access_token, new_refresh_token)

    def authenticate_access_token(self, access_token: str) -> AuthContext | None:
        row = self._db.execute(
            select(AuthSession, User)
            .join(User, User.id == AuthSession.user_id)
            .where(
                AuthSession.access_token_hash == hash_token(access_token),
                AuthSession.revoked_at.is_(None),
                AuthSession.access_expires_at > utc_now(),
                User.is_active.is_(True),
            )
        ).first()
        if row is None:
            return None
        session, user = row
        return AuthContext(user=user, session=session)

    def logout(self, context: AuthContext) -> None:
        context.session.revoked_at = utc_now()
        record_event(self._db, "auth.logout", context.user.id)
        self._db.commit()

    def request_password_reset(self, email: str) -> None:
        """Send a reset email if the account exists. Callers must not reveal which case happened."""
        user = self._user_by_email(email)
        if user is None or not user.is_active:
            return
        self._db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))
        reset_token = new_token()
        self._db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_token(reset_token),
                expires_at=utc_now() + timedelta(minutes=self._settings.password_reset_ttl_minutes),
            )
        )
        record_event(self._db, "auth.password_reset_requested", user.id)
        self._db.commit()
        self._email_sender.send_password_reset(user.email, reset_token)

    def confirm_password_reset(self, reset_token: str, new_password: str) -> None:
        now = utc_now()
        reset = self._db.scalar(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == hash_token(reset_token)
            )
        )
        if reset is None or reset.used_at is not None or reset.expires_at <= now:
            raise InvalidResetTokenError()
        user = self._db.get(User, reset.user_id)
        if user is None:
            raise InvalidResetTokenError()

        user.password_hash = hash_password(new_password)
        reset.used_at = now
        self._revoke_sessions(user.id, keep=None)
        self._db.execute(
            delete(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.id != reset.id,
            )
        )
        record_event(self._db, "auth.password_reset_completed", user.id)
        self._db.commit()

    def change_password(
        self,
        context: AuthContext,
        current_password: str,
        new_password: str,
    ) -> None:
        if not verify_password(current_password, context.user.password_hash):
            raise InvalidCurrentPasswordError()
        context.user.password_hash = hash_password(new_password)
        # Other devices must sign in again. The current session stays signed in.
        self._revoke_sessions(context.user.id, keep=context.session.id)
        record_event(self._db, "auth.password_changed", context.user.id)
        self._db.commit()

    def delete_account(self, context: AuthContext, password: str) -> None:
        """Delete the account. Sessions and reset tokens go with it through database cascades."""
        if not verify_password(password, context.user.password_hash):
            raise InvalidCurrentPasswordError()
        record_event(self._db, "auth.account_deleted", context.user.id)
        self._db.delete(context.user)
        self._db.commit()

    def _open_session(self, user: User) -> TokenPair:
        access_token = new_token()
        refresh_token = new_token()
        now = utc_now()
        self._db.add(
            AuthSession(
                user_id=user.id,
                access_token_hash=hash_token(access_token),
                access_expires_at=now + self._access_ttl(),
                refresh_token_hash=hash_token(refresh_token),
                refresh_expires_at=now + self._refresh_ttl(),
                last_used_at=now,
            )
        )
        return self._token_pair(access_token, refresh_token)

    def _revoke_if_replayed(self, digest: str) -> None:
        """A rotated-out refresh token was presented. Treat the session as stolen and end it."""
        replayed = self._db.scalar(
            select(AuthSession).where(AuthSession.previous_refresh_token_hash == digest)
        )
        if replayed is None:
            return
        replayed.revoked_at = utc_now()
        record_event(self._db, "auth.refresh_replay_detected", replayed.user_id)
        self._db.commit()

    def _revoke_sessions(self, user_id: uuid.UUID, keep: uuid.UUID | None) -> None:
        statement = update(AuthSession).where(
            AuthSession.user_id == user_id,
            AuthSession.revoked_at.is_(None),
        )
        if keep is not None:
            statement = statement.where(AuthSession.id != keep)
        self._db.execute(statement.values(revoked_at=utc_now()))

    def _user_by_email(self, email: str) -> User | None:
        return self._db.scalar(select(User).where(User.email == normalize_email(email)))

    def _access_ttl(self) -> timedelta:
        return timedelta(minutes=self._settings.access_token_ttl_minutes)

    def _refresh_ttl(self) -> timedelta:
        return timedelta(days=self._settings.refresh_token_ttl_days)

    def _token_pair(self, access_token: str, refresh_token: str) -> TokenPair:
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_expires_in=int(self._access_ttl().total_seconds()),
            refresh_expires_in=int(self._refresh_ttl().total_seconds()),
        )
