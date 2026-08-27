from datetime import datetime, timezone
from typing import Any


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def normalize_timestamp(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_severity(value: str | None) -> str | None:
    if value is None:
        return None
    return normalize_text(value.lower())


def normalize_status(value: str | None) -> str | None:
    if value is None:
        return None
    return normalize_text(value.lower())


def normalize_environment(value: str | None) -> str | None:
    if value is None:
        return None
    return normalize_text(value.lower())


def normalize_metadata(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    return {"value": value}
