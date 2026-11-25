"""Time helpers shared by models, routers and services.

All timestamps are stored as timezone-aware UTC values. Calendar boundaries
(“today”, “from 2026-11-01 to 2026-11-07”) are interpreted in the caregiver's
timezone, configured with ``APP_TIMEZONE`` (default ``America/Bogota``).
"""
import os
from datetime import date, datetime, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TIMEZONE = "America/Bogota"


def utc_now() -> datetime:
    """Timezone-aware replacement for the deprecated ``datetime.utcnow``."""
    return datetime.now(timezone.utc)


@lru_cache(maxsize=32)
def _zone(name: str) -> ZoneInfo:
    return ZoneInfo(name)


def app_timezone(name: str | None = None) -> ZoneInfo:
    """Return the requested IANA zone, falling back to APP_TIMEZONE."""
    candidate = name or os.getenv("APP_TIMEZONE", DEFAULT_TIMEZONE)
    try:
        return _zone(candidate)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError(f"Zona horaria no válida: {candidate}")


def local_today(name: str | None = None) -> date:
    """Calendar date in the caregiver timezone (not the server's)."""
    return utc_now().astimezone(app_timezone(name)).date()


def as_utc(value: datetime) -> datetime:
    """Normalize naive values (legacy rows) and aware values to UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
