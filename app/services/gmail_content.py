"""Gmail MIME parsing and email text extraction for ML scanning."""

from __future__ import annotations

import base64
import html
import logging
import re
from email.utils import parseaddr
from typing import Any

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(
    r"https?://[^\s<>\"')\]]+|www\.[^\s<>\"')\]]+",
    re.IGNORECASE,
)
HREF_PATTERN = re.compile(
    r"""<a\s+[^>]*href\s*=\s*["']([^"']+)["']""",
    re.IGNORECASE,
)
SCRIPT_STYLE_PATTERN = re.compile(
    r"(?is)<(script|style)[^>]*>.*?</\1>",
)


def decode_body_data(data: str | None) -> str:
    """Decode Gmail API base64url body data."""
    if not data:
        return ""
    try:
        padded = data + "=" * (-len(data) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("utf-8"))
        return raw.decode("utf-8", errors="replace")
    except Exception as exc:
        logger.debug("Failed to decode Gmail body data: %s", exc)
        return ""


def html_to_plain_text(raw_html: str) -> str:
    """Strip scripts/styles/tags and decode entities into readable plain text."""
    if not raw_html:
        return ""

    text = SCRIPT_STYLE_PATTERN.sub(" ", raw_html)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\s*>", "\n", text)
    text = re.sub(r"(?i)</div\s*>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _header_value(headers: list | None, name: str) -> str:
    for header in headers or []:
        if (header.get("name") or "").lower() == name.lower():
            return (header.get("value") or "").strip()
    return ""


def _normalize_sender(from_header: str) -> str:
    if not from_header:
        return ""
    _display, addr = parseaddr(from_header)
    return (addr or from_header).strip()


def _unique_urls(*sources: str) -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []
    for source in sources:
        if not source:
            continue
        for match in URL_PATTERN.findall(source):
            url = match.strip().rstrip(".,;:)")
            key = url.lower()
            if key and key not in seen:
                seen.add(key)
                urls.append(url)
        for match in HREF_PATTERN.findall(source):
            url = html.unescape(match.strip())
            key = url.lower()
            if key and key not in seen:
                seen.add(key)
                urls.append(url)
    return urls


def _collect_mime_parts(
    payload: dict | None,
    *,
    plain_parts: list[str],
    html_parts: list[str],
) -> None:
    """Recursively collect text/plain and text/html parts from a Gmail payload."""
    if not payload or not isinstance(payload, dict):
        return

    mime = (payload.get("mimeType") or "").lower()
    body = payload.get("body") or {}
    data = body.get("data")
    filename = (payload.get("filename") or "").strip()

    # Skip typical attachments (keep inline text parts without filenames)
    if filename and not mime.startswith("text/"):
        return

    if data:
        decoded = decode_body_data(data)
        if decoded:
            if mime == "text/plain":
                plain_parts.append(decoded)
            elif mime == "text/html":
                html_parts.append(decoded)

    for part in payload.get("parts") or []:
        if isinstance(part, dict):
            _collect_mime_parts(part, plain_parts=plain_parts, html_parts=html_parts)


def _join_body_parts(parts: list[str]) -> str:
    """Merge MIME parts, dropping duplicates and empties."""
    seen: set[str] = set()
    merged: list[str] = []
    for part in parts:
        cleaned = part.strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(cleaned)
    return "\n\n".join(merged).strip()


def extract_email_content(message: dict[str, Any]) -> dict[str, Any]:
    """
    Parse a Gmail API message (format=full) into scan-ready text.

    Returns subject, body, combined_text (subject + body), sender, and urls.
    """
    message = message or {}
    payload = message.get("payload") or {}
    headers = payload.get("headers") or []

    subject = _header_value(headers, "Subject") or "(no subject)"
    sender = _normalize_sender(_header_value(headers, "From")) or "unknown"

    plain_parts: list[str] = []
    html_parts: list[str] = []
    _collect_mime_parts(payload, plain_parts=plain_parts, html_parts=html_parts)

    plain_body = _join_body_parts(plain_parts)
    html_raw = _join_body_parts(html_parts)
    html_body = html_to_plain_text(html_raw)

    body = ""
    body_source = ""

    if plain_body:
        body = plain_body
        body_source = "text/plain"
    elif html_body:
        body = html_body
        body_source = "text/html"
    elif html_raw:
        body = html_raw
        body_source = "text/html"

    snippet = (message.get("snippet") or "").strip()
    if not body and snippet:
        body = snippet
        body_source = "snippet"

    combined_parts = [subject.strip()]
    if body:
        combined_parts.append(body)
    combined_text = "\n\n".join(p for p in combined_parts if p).strip()

    urls = _unique_urls(body, html_raw, plain_body, combined_text)

    return {
        "subject": subject,
        "body": body,
        "combined_text": combined_text,
        "sender": sender,
        "urls": urls,
        "body_source": body_source,
        "body_length": len(body),
    }
