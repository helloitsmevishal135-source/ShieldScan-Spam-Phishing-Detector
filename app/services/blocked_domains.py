"""Blocked domain registry — increases risk score, never auto-safe."""

from __future__ import annotations

import logging

from flask import has_app_context

from app.ml.utils.url_normalize import registered_domain

logger = logging.getLogger(__name__)


def get_blocked_domains() -> set[str]:
    try:
        if not has_app_context():
            return set()
        from app.models.platform import BlockedDomain
        rows = BlockedDomain.objects(is_active=True)
        return {registered_domain(row.domain) for row in rows if row.domain}
    except Exception as exc:
        logger.debug("Could not load blocked domains: %s", exc)
        return set()
