import json

from app.models import Scan
from app.admin.services.log_helper import write_system_log
from app.services.ml_service import get_threat_level, run_prediction


def perform_scan(user, input_text: str) -> dict:
    """
    Run ML prediction, persist scan history, and return enriched result.
    """
    input_text = (input_text or "").strip()
    if not input_text:
        raise ValueError("Input cannot be empty.")

    if len(input_text) > 5000:
        raise ValueError("Input is too long (max 5000 characters).")

    prediction = run_prediction(input_text)
    threat_level = prediction.get("threat_level") or get_threat_level(
        prediction["label"], prediction["confidence"]
    )

    scan = Scan(
        user_id=str(user.pk),
        input_text=input_text[:500],
        input_type=prediction["type"],
        label=prediction["label"],
        confidence=prediction["confidence"],
        threat_level=threat_level,
        model_probability=prediction.get("model_probability"),
        risk_score=prediction.get("risk_score"),
        reasons_json=json.dumps(prediction.get("reasons", [])),
        feature_summary_json=json.dumps(prediction.get("feature_summary", {})),
    )
    scan.save()

    write_system_log(
        "INFO",
        "scan",
        f"Manual scan by user {user.pk}: {prediction['label']}",
        {
            "user_id": str(user.pk),
            "scan_id": str(scan.pk),
            "input_type": prediction["type"],
            "label": prediction["label"],
            "probability": prediction.get("model_probability"),
            "risk_score": prediction.get("risk_score"),
            "threat_level": threat_level,
        },
    )

    return {
        **prediction,
        "threat_level": threat_level,
        "scan_id": str(scan.pk),
    }


def _extract_uid(user) -> str:
    return str(getattr(user, "pk", getattr(user, "id", user)))


def get_user_stats(user) -> dict:
    """Aggregate scan statistics for dashboard charts."""
    uid = _extract_uid(user)
    total = Scan.objects(user_id=uid).count()
    safe = Scan.objects(user_id=uid, threat_level="safe").count()
    suspicious = Scan.objects(user_id=uid, threat_level="suspicious").count()
    dangerous = Scan.objects(user_id=uid, threat_level="dangerous").count()
    threats = suspicious + dangerous

    return {
        "total": total,
        "safe": safe,
        "suspicious": suspicious,
        "dangerous": dangerous,
        "threats": threats,
    }


def get_recent_scans(user, limit: int = 10):
    """Most recent scans for history table."""
    uid = _extract_uid(user)
    return Scan.objects(user_id=uid).order_by("-created_at").limit(limit)

