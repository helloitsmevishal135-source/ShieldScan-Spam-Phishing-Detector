"""URL normalization utilities."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse, urlunparse

IGNORED_SCHEMES = ("javascript:", "mailto:", "tel:", "data:", "#")

DEFAULT_PORTS = {"http": 80, "https": 443}


def is_ignored_url(url: str) -> bool:
    value = (url or "").strip().lower()
    if not value or value in ("#", ""):
        return True
    return any(value.startswith(scheme) for scheme in IGNORED_SCHEMES)


def normalize_url(url: str, base_url: str | None = None) -> str | None:
    """
    Normalize absolute/relative URLs:
    - resolve relatives against base_url
    - lowercase hostname
    - remove fragments
    - remove default ports
    - collapse duplicate slashes in path
    """
    raw = (url or "").strip()
    if is_ignored_url(raw):
        return None

    if base_url and not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw):
        raw = urljoin(base_url, raw)

    if raw.startswith("//"):
        raw = "https:" + raw

    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw):
        raw = "https://" + raw

    try:
        parsed = urlparse(raw)
    except Exception:
        return None

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return None

    scheme = (parsed.scheme or "http").lower()
    port = parsed.port
    if port and DEFAULT_PORTS.get(scheme) == port:
        port = None

    path = parsed.path or "/"
    path = re.sub(r"/{2,}", "/", path)

    netloc = hostname
    if port:
        netloc = f"{hostname}:{port}"

    normalized = urlunparse(
        (
            scheme,
            netloc,
            path,
            "",
            parsed.query,
            "",
        )
    )
    return normalized


def registered_domain(hostname: str) -> str:
    host = (hostname or "").lower().replace("www.", "")
    parts = [p for p in host.split(".") if p]
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


def dedupe_urls(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for url in urls:
        key = (url or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(url)
    return unique
