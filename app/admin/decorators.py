"""Admin authentication decorators."""

from __future__ import annotations

from functools import wraps

from flask import flash, g, redirect, session, url_for

from app.models import AdminUser


def get_current_admin() -> AdminUser | None:
    admin_id = session.get("admin_id")
    if not admin_id:
        return None
    try:
        admin = AdminUser.objects(pk=admin_id).first()
    except Exception:
        session.pop("admin_id", None)
        return None
    if not admin or not admin.is_active:
        session.pop("admin_id", None)
        return None
    return admin


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        admin = get_current_admin()
        if not admin:
            flash("Administrator sign-in required.", "warning")
            return redirect(url_for("admin.login"))
        g.admin = admin
        return view(*args, **kwargs)

    return wrapped
