"""
Wraps the existing ML pipeline in main.py without modifying model logic.
"""

import math

from main import predict as _predict

DEFAULT_CONFIDENCE_FRACTION = 0.5
DEFAULT_CONFIDENCE_PERCENT = 50.0


def _coerce_float(value) -> float | None:
    """Return a finite float, or None if value is missing/invalid."""
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def sanitize_confidence_percent(value, default: float = 0.0) -> float:
    """Return a finite 0–100 confidence for threat-level logic and display."""
    number = _coerce_float(value)
    if number is None:
        return default
    if 0.0 <= number <= 1.0:
        number = number * 100.0
    return max(0.0, min(100.0, round(number, 2)))


def sanitize_confidence_fraction(value, default: float = DEFAULT_CONFIDENCE_FRACTION) -> float:
    """Return a finite 0–1 confidence safe for SQLite NOT NULL float columns."""
    number = _coerce_float(value)
    if number is None:
        return default
    if number > 1.0:
        number = number / 100.0
    return max(0.0, min(1.0, round(number, 4)))


def confidence_to_percent(value) -> float:
    """Convert stored fraction (0–1) or legacy percent (0–100) for UI."""
    number = _coerce_float(value)
    if number is None:
        return DEFAULT_CONFIDENCE_PERCENT
    if number > 1.0:
        return round(number, 1)
    return round(number * 100.0, 1)


def run_prediction(user_input: str) -> dict:
    """
    Call the hybrid detector and normalize the response for the web application.
    """
    result = _predict(user_input)
    confidence = sanitize_confidence_percent(result.get("confidence"))
    model_probability = sanitize_confidence_percent(
        result.get("model_probability", result.get("confidence"))
    )
    risk_score = sanitize_confidence_percent(
        result.get("risk_score", result.get("confidence"))
    )
    threat_level = result.get("threat_level") or get_threat_level(
        result.get("label", "ERROR"), confidence
    )
    return {
        "type": result.get("type", "UNKNOWN"),
        "label": result.get("label", "ERROR"),
        "confidence": confidence,
        "model_probability": model_probability,
        "risk_score": risk_score,
        "threat_level": threat_level,
        "reasons": result.get("reasons", []),
        "feature_summary": result.get("feature_summary", {}),
        "trusted_domain_signal": result.get("trusted_domain_signal", 0.0),
    }


def get_threat_level(label: str, confidence: float) -> str:
    """
    Map ML labels to UI threat levels.
    Green = safe | Yellow = suspicious | Red = dangerous
    """
    confidence = sanitize_confidence_percent(confidence)
    label_upper = str(label).upper()

    is_threat = "SPAM" in label_upper or "PHISHING" in label_upper
    is_safe = "HAM" in label_upper or "SAFE" in label_upper

    if is_safe and not is_threat:
        return "safe"

    if is_threat:
        if confidence >= 70:
            return "dangerous"
        if confidence >= 40:
            return "suspicious"
        return "suspicious"

    if "INVALID" in label_upper or "ERROR" in label_upper:
        return "suspicious"

    return "safe"


def threat_display(threat_level: str) -> dict:
    """Human-readable threat metadata for templates."""
    mapping = {
        "safe": {
            "text": "Safe",
            "color": "success",
            "icon": "fa-circle-check",
            "action": "Safe to proceed",
        },
        "suspicious": {
            "text": "Suspicious",
            "color": "warning",
            "icon": "fa-triangle-exclamation",
            "action": "Review carefully before acting",
        },
        "dangerous": {
            "text": "Dangerous",
            "color": "danger",
            "icon": "fa-skull-crossbones",
            "action": "Block and report immediately",
        },
    }
    return mapping.get(threat_level, mapping["suspicious"])
