"""Transactional email behind a replaceable interface."""

from app.integrations.email.sender import (
    ConsoleEmailSender,
    EmailSender,
    MemoryEmailSender,
    PasswordResetMessage,
    build_email_sender,
)

__all__ = [
    "ConsoleEmailSender",
    "EmailSender",
    "MemoryEmailSender",
    "PasswordResetMessage",
    "build_email_sender",
]
