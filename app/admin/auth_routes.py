"""Admin authentication routes."""

from flask import flash, redirect, render_template, request, session, url_for

from app.admin.decorators import admin_required, get_current_admin
from app.admin.services.log_helper import write_system_log
from app.admin import admin_bp
from app.models import AdminUser


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if get_current_admin():
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        login_identifier = (request.form.get("email") or request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        admin = AdminUser.objects(email=login_identifier.lower(), is_active=True).first()
        if not admin:
            admin = AdminUser.objects(username=login_identifier, is_active=True).first()

        if not admin or not admin.check_password(password):
            write_system_log("WARNING", "auth", f"Failed admin login attempt for {login_identifier}")
            flash("Invalid administrator credentials.", "danger")
            return render_template("admin/login.html", email=login_identifier)

        session["admin_id"] = str(admin.pk)
        session.permanent = bool(request.form.get("remember"))
        write_system_log("INFO", "auth", f"Admin login: {admin.username}", {"admin_id": str(admin.pk)})
        flash(f"Welcome, {admin.username}.", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/login.html")


@admin_bp.route("/logout")
@admin_required
def logout():
    admin = get_current_admin()
    if admin:
        write_system_log("INFO", "auth", f"Admin logout: {admin.username}")
    session.pop("admin_id", None)
    flash("Signed out of admin panel.", "info")
    return redirect(url_for("admin.login"))
