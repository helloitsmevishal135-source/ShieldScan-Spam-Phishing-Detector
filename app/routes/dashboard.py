from flask import Blueprint, flash, jsonify, render_template, request
from flask_login import current_user, login_required

from app.services.email_scan_service import get_recent_email_scans
from app.services.gmail_service import google_oauth_configured
from app.services.ml_service import threat_display
from app.services.scan_service import get_recent_scans, get_user_stats, perform_scan

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    stats = get_user_stats(current_user)
    recent_scans = get_recent_scans(current_user)
    recent_emails = get_recent_email_scans(current_user)
    return render_template(
        "dashboard/index.html",
        stats=stats,
        recent_scans=recent_scans,
        recent_emails=recent_emails,
        gmail_connected=current_user.gmail_connected,
        gmail_oauth_configured=google_oauth_configured(),
        gmail_last_sync=current_user.gmail_last_sync,
    )


@dashboard_bp.route("/scan", methods=["POST"])
@login_required
def scan():
    """Run detection — supports form POST and JSON (AJAX)."""
    wants_json = (
        request.is_json
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.accept_mimetypes.best == "application/json"
    )

    if request.is_json:
        data = request.get_json(silent=True) or {}
        user_input = (data.get("input_data") or "").strip()
    else:
        user_input = (request.form.get("input_data") or "").strip()

    try:
        result = perform_scan(current_user, user_input)
        result["threat"] = threat_display(result["threat_level"])

        if wants_json:
            stats = get_user_stats(current_user)
            latest = get_recent_scans(current_user, limit=1)
            scan_row = latest[0] if latest else None
            return jsonify({
                "ok": True,
                "result": result,
                "stats": stats,
                "scan": {
                    "input_text": scan_row.input_text,
                    "input_type": scan_row.input_type,
                    "label": scan_row.label,
                    "confidence": scan_row.confidence,
                    "threat_level": scan_row.threat_level,
                    "risk_score": scan_row.risk_score,
                } if scan_row else None,
            })

        flash("Scan completed.", "success")
        stats = get_user_stats(current_user)
        recent_scans = get_recent_scans(current_user)
        return render_template(
            "dashboard/index.html",
            stats=stats,
            recent_scans=recent_scans,
            last_result=result,
        )

    except ValueError as exc:
        if wants_json:
            return jsonify({"ok": False, "error": str(exc)}), 400
        flash(str(exc), "warning")
        return render_template(
            "dashboard/index.html",
            stats=get_user_stats(current_user),
            recent_scans=get_recent_scans(current_user),
        )

    except Exception:
        if wants_json:
            return jsonify({"ok": False, "error": "Scan failed. Please try again."}), 500
        flash("An error occurred during analysis. Please try again.", "danger")
        return render_template(
            "dashboard/index.html",
            stats=get_user_stats(current_user),
            recent_scans=get_recent_scans(current_user),
        )
