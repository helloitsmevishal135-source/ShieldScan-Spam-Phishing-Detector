"""Admin panel helpers."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from app.models import SystemLog

logger = logging.getLogger(__name__)


def write_system_log(
    level: str,
    category: str,
    message: str,
    details: dict | str | None = None,
) -> None:
    """Persist a structured log entry to MongoDB."""
    payload = details
    if isinstance(details, dict):
        payload = json.dumps(details)
    try:
        SystemLog(
            level=level.upper(),
            category=category,
            message=message[:2000],
            details=payload,
        ).save()
    except Exception as exc:
        logger.warning("Failed to write system log: %s", exc)


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
