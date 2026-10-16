"""Trusted domain registry — positive signal only, never auto-safe."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.ml.utils.url_normalize import registered_domain

logger = logging.getLogger(__name__)

LEGACY_WHITELIST_PATH = Path("whitelist.csv")

# High-reputation public sites used as a modest trust signal only (never auto-safe).
BUILTIN_HIGH_REPUTATION_DOMAINS = {
    "google.com", "microsoft.com", "github.com", "stackoverflow.com",
    "wikipedia.org", "python.org", "apple.com", "amazon.com",
    "facebook.com", "instagram.com", "twitter.com", "x.com",
    "linkedin.com", "youtube.com", "reddit.com", "netflix.com",
    "cloudflare.com", "mozilla.org", "openai.com", "bing.com",
    "yahoo.com", "office.com", "live.com", "outlook.com",
    "adobe.com", "npmjs.com", "pypi.org", "debian.org",
    "ubuntu.com", "archlinux.org",
}


def _load_legacy_whitelist() -> set[str]:
    if not LEGACY_WHITELIST_PATH.exists():
        return set()
    try:
        df = pd.read_csv(LEGACY_WHITELIST_PATH, usecols=[0], nrows=50000)
        domains = df.iloc[:, 0].astype(str).str.strip().str.lower()
        domains = domains[domains.str.contains(r"[a-zA-Z]", na=False)]
        domains = domains[domains.str.contains(r"\.", na=False)]
        return {registered_domain(d) for d in domains.tolist() if d}
    except Exception as exc:
        logger.warning("Could not load legacy whitelist.csv: %s", exc)
        return set()


def _load_db_trusted_domains() -> set[str]:
    try:
        from flask import has_app_context
        if not has_app_context():
            return set()
        from app.models.platform import TrustedDomain
        rows = TrustedDomain.objects(is_active=True)
        return {registered_domain(row.domain) for row in rows if row.domain}
    except Exception:
        return set()


def get_builtin_high_reputation_domains() -> set[str]:
    return set(BUILTIN_HIGH_REPUTATION_DOMAINS)


@lru_cache(maxsize=1)
def get_trusted_domains() -> set[str]:
    """Merge built-in, DB, and legacy trusted domains."""
    domains = set(BUILTIN_HIGH_REPUTATION_DOMAINS)
    domains.update(_load_legacy_whitelist())
    domains.update(_load_db_trusted_domains())
    return domains


def clear_trusted_domain_cache() -> None:
    get_trusted_domains.cache_clear()
