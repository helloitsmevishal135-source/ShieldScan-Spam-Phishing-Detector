"""Process Gmail messages through the existing ML detection pipeline."""

import html
import logging
import re

logger = logging.getLogger(__name__)
from app.models import EmailScan
from app.services.ml_service import (
    confidence_to_percent,
    get_threat_level,
    run_prediction,
    sanitize_confidence_fraction,
)


def clean_email_text(text: str) -> str:
    """Normalize email text before classification (no ML logic changes)."""
    text = html.unescape(str(text or ""))
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_scan_input(
    subject: str,
    body: str,
    *,
    combined_text: str | None = None,
) -> str:
    """Combine subject and body (or use pre-built combined_text) for the predictor."""
    if combined_text:
        text = clean_email_text(combined_text)
    else:
        subject = clean_email_text(subject)
        body = clean_email_text(body)
        parts = [p for p in (subject, body) if p]
        text = "\n\n".join(parts)
    return text[:5000]


def to_risk_label(threat_level: str) -> str:
    return "safe" if threat_level == "safe" else "threat"


def build_detected_reason(prediction: dict) -> str:
    label = prediction.get("label", "UNKNOWN")
    level = (prediction.get("threat_level") or "unknown").capitalize()
    return f"{label} — {level}"


def scan_email_content(
    user,
    *,
    gmail_message_id: str,
    subject: str,
    sender: str,
    body: str,
    snippet: str | None = None,
    combined_text: str | None = None,
    body_source: str | None = None,
    urls: list[str] | None = None,
) -> EmailScan | None:
    """
    Run existing ML modules on full email content and persist result.
    Returns None if content is empty or message was already scanned.
    """
    uid = str(user.pk)
    existing = EmailScan.objects(user_id=uid, gmail_message_id=gmail_message_id).first()
    if existing:
        return None

    scan_text = build_scan_input(subject, body, combined_text=combined_text)
    if not scan_text:
        logger.debug(
            "Gmail scan skipped empty content message_id=%s subject=%r",
            gmail_message_id,
            subject,
        )
        return None

    logger.debug(
        "Gmail scan prepare message_id=%s body_len=%d body_source=%s url_count=%d "
        "combined_preview=%.200s",
        gmail_message_id,
        len(body or ""),
        body_source or "unknown",
        len(urls or []),
        scan_text,
    )

    prediction = run_prediction(scan_text)
    logger.debug(
        "Gmail scan result message_id=%s label=%s confidence=%s type=%s",
        gmail_message_id,
        prediction.get("label"),
        prediction.get("confidence"),
        prediction.get("type"),
    )
    threat_level = prediction.get("threat_level") or get_threat_level(
        prediction["label"], prediction["confidence"]
    )
    risk_label = to_risk_label(threat_level)
    confidence_fraction = sanitize_confidence_fraction(prediction.get("confidence"))

    record = EmailScan(
        user_id=uid,
        gmail_message_id=gmail_message_id,
        subject=clean_email_text(subject)[:512] or "(no subject)",
        sender=(sender or "unknown")[:256],
        snippet=(snippet or "")[:512] or None,
        input_type=prediction["type"],
        label=prediction["label"],
        confidence=confidence_fraction,
        threat_level=threat_level,
        risk_label=risk_label,
        risk_score=confidence_fraction,
        detected_reason=build_detected_reason(prediction),
    )
    record.save()
    return record


def get_recent_email_scans(user, limit: int = 20):
    return EmailScan.objects(user_id=str(user.pk)).order_by("-created_at").limit(limit)


def email_scan_to_dict(scan: EmailScan) -> dict:
    return {
        "id": str(scan.pk),
        "subject": scan.subject,
        "sender": scan.sender,
        "snippet": scan.snippet,
        "risk_label": scan.risk_label,
        "risk_score": confidence_to_percent(scan.risk_score),
        "detected_reason": scan.detected_reason,
        "threat_level": scan.threat_level,
        "label": scan.label,
        "confidence": confidence_to_percent(scan.confidence),
        "created_at": scan.created_at.isoformat() + "Z" if scan.created_at else None,
    }
