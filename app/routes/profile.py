from flask import Blueprint, flash, render_template
from flask_login import current_user, login_required

from app.services.scan_service import get_user_stats

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
@login_required
def index():
    stats = get_user_stats(current_user)
    return render_template("profile.html", stats=stats)
