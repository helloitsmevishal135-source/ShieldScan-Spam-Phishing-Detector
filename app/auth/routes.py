import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.models import User

try:
    from app.admin.services.log_helper import write_system_log
except ImportError:
    write_system_log = None

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")


def _validate_registration(username, email, password, confirm):
    errors = []
    username = (username or "").strip()
    email = (email or "").strip().lower()

    if not username or len(username) < 2:
        errors.append("Username must be at least 2 characters.")
    if len(username) > 80:
        errors.append("Username is too long.")
    if not email or not EMAIL_RE.match(email):
        errors.append("Please enter a valid email address.")
    if not password or len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if password != confirm:
        errors.append("Passwords do not match.")

    return errors, username, email


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        errors, username, email = _validate_registration(
            request.form.get("username"),
            request.form.get("email"),
            request.form.get("password"),
            request.form.get("confirm_password"),
        )

        if User.objects(email=email).first():
            errors.append("An account with this email already exists.")

        if errors:
            for msg in errors:
                flash(msg, "danger")
            return render_template(
                "auth/register.html",
                username=username,
                email=email,
            )

        user = User(username=username, email=email)
        user.set_password(request.form.get("password"))
        user.save()
        if write_system_log:
            write_system_log("INFO", "auth", f"User registered: {username}", {"email": email})

        flash("Account created successfully. Please sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        login_identifier = (request.form.get("email") or request.form.get("username") or request.form.get("login") or "").strip()
        password = request.form.get("password") or ""
        remember = request.form.get("remember") == "on"

        user = User.objects(email=login_identifier.lower()).first()
        if user is None:
            user = User.objects(username=login_identifier).first()
        if user is None or not user.check_password(password):
            if write_system_log:
                write_system_log("WARNING", "auth", f"Failed login attempt for {login_identifier}")
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", email=login_identifier)

        login_user(user, remember=remember)
        if write_system_log:
            write_system_log("INFO", "auth", f"User login: {user.username}", {"user_id": str(user.pk)})
        next_page = request.args.get("next")
        if next_page:
            return redirect(next_page)
        return redirect(url_for("dashboard.index"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
