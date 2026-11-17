"""Email delivery. Only development and test backends exist; production needs a provider.

Reset tokens are sent through this interface. They are never written to application logs.
"""

from dataclasses import dataclass, field
from typing import Protocol

from app.core.config import Settings


class EmailSender(Protocol):
    def send_password_reset(self, recipient: str, reset_token: str) -> None: ...


@dataclass(frozen=True)
class PasswordResetMessage:
    recipient: str
    reset_token: str


class ConsoleEmailSender:
    """Development only. Prints the reset token to stdout so the flow can be tried locally."""

    def send_password_reset(self, recipient: str, reset_token: str) -> None:
        print(f"[dev-email] password reset for {recipient}: token={reset_token}", flush=True)


@dataclass
class MemoryEmailSender:
    """Test double. Records every message so tests can read the token."""

    sent: list[PasswordResetMessage] = field(default_factory=list)

    def send_password_reset(self, recipient: str, reset_token: str) -> None:
        self.sent.append(PasswordResetMessage(recipient=recipient, reset_token=reset_token))


def build_email_sender(settings: Settings) -> EmailSender:
    if settings.email_backend == "memory":
        return MemoryEmailSender()
    return ConsoleEmailSender()
