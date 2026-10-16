# Load .env + OAuth dev transport before any Google OAuth modules import
from app.env_bootstrap import bootstrap_environment

bootstrap_environment()

import os
import mongoengine

from flask import redirect, url_for
from flask_login import current_user

from app.config import BASE_DIR, Config
from app.extensions import login_manager
from app.models import User


def create_app(config_class=Config):
    """Application factory."""
    from flask import Flask

    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "templates"),
        static_folder=os.path.join(BASE_DIR, "static"),
    )
    app.config.from_object(config_class)

    import logging

    if not app.debug and not app.logger.handlers:
        logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    # ── MongoDB Atlas connection (with local fallback) ───────────────────────
    mongo_uri = os.environ.get("MONGODB_URI", "").strip() or "mongodb://127.0.0.1:27017/shieldscan"
    try:
        conn = mongoengine.connect(host=mongo_uri, serverSelectionTimeoutMS=3000)
        conn.admin.command("ping")
        app.logger.info("Connected to MongoDB (%s).", "Atlas/Remote" if "mongodb+srv" in mongo_uri else "Local")
    except Exception as exc:
        local_uri = "mongodb://127.0.0.1:27017/shieldscan"
        if mongo_uri != local_uri:
            app.logger.warning(
                "Could not connect to MongoDB Atlas (%s). Falling back to local MongoDB (%s). "
                "Ensure your IP is whitelisted on MongoDB Atlas Network Access if using cloud database.",
                exc,
                local_uri,
            )
            mongoengine.disconnect()
            conn = mongoengine.connect(host=local_uri, serverSelectionTimeoutMS=3000)
            conn.admin.command("ping")
            app.logger.info("Connected to local MongoDB.")
        else:
            raise

    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.objects(pk=user_id).first()
        except Exception:
            return None

    @login_manager.unauthorized_handler
    def unauthorized():
        """Return JSON for AJAX/fetch calls instead of an HTML login redirect."""
        from flask import jsonify, request

        wants_json = (
            request.is_json
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or request.accept_mimetypes.best == "application/json"
        )
        if wants_json:
            return jsonify({
                "ok": False,
                "success": False,
                "error": "Please log in again.",
                "message": "Please log in again.",
            }), 401
        return redirect(url_for("auth.login"))

    # Blueprints
    from app.auth import auth_bp
    from app.routes import dashboard_bp, profile_bp
    from app.routes.gmail import gmail_bp
    from app.admin import admin_bp
    from app.routes.crawler import crawler_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(gmail_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(crawler_bp)

    # Create default admin if none exists
    from app.admin.bootstrap import ensure_default_admin
    ensure_default_admin()

    from app.tasks.gmail_sync import init_gmail_scheduler

    init_gmail_scheduler(app)

    @app.route("/")
    def root():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.index"))
        return redirect(url_for("auth.login"))

    return app
