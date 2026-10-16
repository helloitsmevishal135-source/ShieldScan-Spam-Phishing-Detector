import logging

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.services.crawler_service import get_crawler_report, perform_website_analysis
from app.services.scan_service import get_user_stats

logger = logging.getLogger(__name__)
crawler_bp = Blueprint("crawler", __name__, url_prefix="/crawler")


@crawler_bp.route("/analyze", methods=["POST"])
@login_required
def analyze():
    """Analyze a website: crawl HTML, extract links, classify each URL."""
    wants_json = (
        request.is_json
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.accept_mimetypes.best == "application/json"
    )

    data = request.get_json(silent=True)
    if isinstance(data, dict):
        seed_url = (
            data.get("url")
            or data.get("seed_url")
            or data.get("website_url")
            or data.get("website")
            or ""
        ).strip()
    else:
        seed_url = (
            request.form.get("url")
            or request.form.get("seed_url")
            or request.form.get("website_url")
            or request.args.get("url")
            or ""
        ).strip()

    try:
        result = perform_website_analysis(current_user, seed_url)
        if wants_json:
            return jsonify({"ok": True, "result": result, "stats": get_user_stats(current_user)})
        flash("Website analysis completed.", "success")
        return render_template(
            "dashboard/index.html",
            stats=get_user_stats(current_user),
            website_result=result,
        )
    except ValueError as exc:
        logger.warning("Website analysis validation failed: %s", exc)
        if wants_json:
            return jsonify({"ok": False, "error": str(exc)}), 400
        flash(str(exc), "warning")
    except Exception:
        logger.exception("Website analysis failed for url=%s", seed_url)
        if wants_json:
            return jsonify({"ok": False, "error": "Website analysis failed. Please try again."}), 500
        flash("Website analysis failed. Please try again.", "danger")

    if wants_json:
        return jsonify({"ok": False, "error": "Website analysis failed."}), 500
    return redirect(url_for("dashboard.index"))


@crawler_bp.route("/reports/<string:log_id>")
@login_required
def report(log_id: str):
    report_data = get_crawler_report(current_user, log_id)
    if not report_data:
        return jsonify({"ok": False, "error": "Report not found."}), 404
    return jsonify({"ok": True, "report": report_data})
