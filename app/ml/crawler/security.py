"""SSRF-safe URL validation for the website crawler."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


def is_public_http_url(url: str) -> bool:
    """Allow only http(s) URLs that do not resolve to private/local networks."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    hostname = (parsed.hostname or "").strip().lower()
    if not hostname or hostname == "localhost":
        return False

    try:
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False

    for info in addr_infos:
        ip = info[4][0]
        try:
            ip_obj = ipaddress.ip_address(ip)
        except ValueError:
            continue
        if (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_reserved
            or ip_obj.is_multicast
        ):
            return False
    return True
