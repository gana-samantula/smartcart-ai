"""Time helpers. The application stores and compares timestamps in UTC only."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Timezone-aware current time in UTC."""
    return datetime.now(UTC)
