"""Time helpers. All timestamps are stored as UTC ISO strings."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from config import STALE_AFTER_HOURS


def utc_now() -> datetime:
    """Current time as an aware UTC datetime."""
    return datetime.now(timezone.utc)


def to_iso(moment: datetime) -> str:
    """Store a datetime as a stable ISO string."""
    return moment.astimezone(timezone.utc).isoformat()


def parse_iso(value: str) -> datetime:
    """Read one of our ISO strings. Old records without Z are assumed UTC."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Missing timestamp")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    moment = datetime.fromisoformat(text)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def is_stale(updated_at: str, now: datetime | None = None,
             hours: int = STALE_AFTER_HOURS) -> bool:
    """True only when the timestamp is MORE than `hours` old."""
    if now is None:
        now = utc_now()
    try:
        moment = parse_iso(updated_at)
    except (ValueError, TypeError):
        return True  # unreadable time is treated as stale, never as fresh
    return (now - moment) > timedelta(hours=hours)


def age_text(updated_at: str, now: datetime | None = None,
             hours: int = STALE_AFTER_HOURS) -> str:
    """Short text for the compact board: '5m', '3h', '2d' or '⚠ STALE'."""
    if now is None:
        now = utc_now()
    if is_stale(updated_at, now=now, hours=hours):
        return "⚠ STALE"

    moment = parse_iso(updated_at)
    seconds = max(0.0, (now - moment).total_seconds())
    if seconds < 60:
        return "now"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes}m"
    total_hours = minutes // 60
    if hours >= 24 and total_hours >= 48:
        return f"{total_hours // 24}d"
    return f"{total_hours}h"
