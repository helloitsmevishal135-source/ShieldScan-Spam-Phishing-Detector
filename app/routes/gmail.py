import logging

from flask import Blueprint, flash, jsonify, redirect, request, url_for
from flask_login import current_user, login_required

from app.services.email_scan_service import email_scan_to_dict, get_recent_email_scans
from app.services.gmail_service import (
    build_authorization_response,
    complete_oauth,
    disconnect_gmail,
    format_oauth_error,
    google_oauth_configured,
    start_oauth_authorization,
    sync_user_mailbox,
)

logger = logging.getLogger(__name__)
gmail_bp = Blueprint("gmail", __name__, url_prefix="/gmail")


@gmail_bp.route("/connect")
@login_required
def connect():
    if not google_oauth_configured():
        flash(
            "Gmail integration is not configured. Set GOOGLE_CLIENT_ID and "
            "GOOGLE_CLIENT_SECRET in your environment.",
            "warning",
        )
        return redirect(url_for("dashboard.index"))

    try:
        auth_url = start_oauth_authorization()
        return redirect(auth_url)
    except Exception as exc:
        logger.exception("Gmail OAuth connect failed")
        flash(f"Could not start Gmail authorization: {format_oauth_error(exc)}", "danger")
        return redirect(url_for("dashboard.index"))


@gmail_bp.route("/callback")
@login_required
def callback():
    if request.args.get("error"):
        flash("Gmail connection was cancelled or denied.", "warning")
        return redirect(url_for("dashboard.index"))

    if not request.args.get("code"):
        logger.error("Gmail OAuth callback missing code: %s", dict(request.args))
        flash("Gmail authorization did not return a code. Please try again.", "danger")
        return redirect(url_for("dashboard.index"))

    state = request.args.get("state", "")
    authorization_response = build_authorization_response()

    try:
        complete_oauth(current_user, authorization_response, state)
        synced = sync_user_mailbox(current_user)
        flash(
            f"Gmail connected successfully. Scanned {synced} new message(s).",
            "success",
        )
    except ValueError as exc:
        logger.warning("Gmail OAuth callback validation failed: %s", exc)
        flash(str(exc), "danger")
    except Exception as exc:
        logger.exception(
            "Gmail OAuth callback failed (authorization_response=%s)",
            authorization_response,
        )
        flash(f"Failed to connect Gmail: {format_oauth_error(exc)}", "danger")

    return redirect(url_for("dashboard.index"))


@gmail_bp.route("/disconnect", methods=["POST"])
@login_required
def disconnect():
    disconnect_gmail(current_user)
    flash("Gmail disconnected.", "info")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True, "connected": False})
    return redirect(url_for("dashboard.index"))


def _sync_error_message(exc: Exception) -> str:
    """Map Gmail/sync failures to short user-facing messages."""
    text = str(exc).lower()
    if isinstance(exc, ValueError):
        return str(exc)
    if "refresh" in text and ("token" in text or "invalid_grant" in text):
        return "Gmail access expired. Please disconnect and reconnect Gmail."
    if "invalid_grant" in text or "token" in text and "expired" in text:
        return "Gmail access expired. Please disconnect and reconnect Gmail."
    if "credentials" in text or "not connected" in text:
        return "Gmail is not connected or tokens are invalid. Please reconnect Gmail."
    if "timeout" in text or "timed out" in text or "connection" in text or "network" in text:
        return "Could not reach Gmail. Check your connection and try again."
    if "database" in text or "mongo" in text or "pymongo" in text:
        return "A database error occurred while saving scan results. Please try again."
    return "Gmail refresh failed. Please try again or reconnect Gmail."


@gmail_bp.route("/sync", methods=["POST"])
@login_required
def sync_now():
    if not current_user.gmail_connected:
        return jsonify({
            "success": False,
            "new_emails": 0,
            "message": "Gmail is not connected.",
            "error": "Gmail is not connected.",
        }), 400
    try:
        count = sync_user_mailbox(current_user)
        if count == 0:
            message = "No new emails found."
        elif count == 1:
            message = "1 new email scanned."
        else:
            message = f"{count} new emails scanned."
        emails = [email_scan_to_dict(s) for s in get_recent_email_scans(current_user)]
        last_sync = None
        if current_user.gmail_last_sync:
            last_sync = current_user.gmail_last_sync.isoformat() + "Z"
        return jsonify({
            "success": True,
            "new_emails": count,
            "message": message,
            "ok": True,
            "synced": count,
            "emails": emails,
            "last_sync": last_sync,
        })
    except ValueError as exc:
        message = str(exc)
        return jsonify({
            "success": False,
            "new_emails": 0,
            "message": message,
            "error": message,
            "ok": False,
        }), 400
    except Exception as exc:
        logger.exception("Manual Gmail sync failed for user %s", current_user.id)
        message = _sync_error_message(exc)
        return jsonify({
            "success": False,
            "new_emails": 0,
            "message": message,
            "error": message,
            "ok": False,
        }), 500


@gmail_bp.route("/status")
@login_required
def status():
    last_sync = None
    if current_user.gmail_last_sync:
        last_sync = current_user.gmail_last_sync.isoformat() + "Z"
    return jsonify(
        {
            "connected": bool(current_user.gmail_connected),
            "oauth_configured": google_oauth_configured(),
            "last_sync": last_sync,
        }
    )


@gmail_bp.route("/emails")
@login_required
def emails():
    scans = get_recent_email_scans(current_user)
    return jsonify(
        {
            "ok": True,
            "emails": [email_scan_to_dict(s) for s in scans],
        }
    )
