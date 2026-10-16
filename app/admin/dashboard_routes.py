"""Admin dashboard routes."""

from flask import render_template

from app.admin.decorators import admin_required
from app.admin import admin_bp
from app.admin.services.stats import get_dashboard_stats, get_scan_trend, sync_scan_statistics


@admin_bp.route("/")
@admin_required
def dashboard():
    sync_scan_statistics()
    stats = get_dashboard_stats()
    trend = get_scan_trend()
    return render_template("admin/dashboard.html", stats=stats, trend=trend)
