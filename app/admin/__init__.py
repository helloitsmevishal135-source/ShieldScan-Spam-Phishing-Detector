"""Admin panel blueprint."""

from flask import Blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

from app.admin import auth_routes, dashboard_routes, domains_routes, logs_routes, models_routes  # noqa: E402, F401

__all__ = ["admin_bp"]
