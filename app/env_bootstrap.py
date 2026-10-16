"""
Load .env and configure OAuth transport before any Google OAuth imports run.

Production: HTTPS required (OAUTHLIB_INSECURE_TRANSPORT unset).
Development: HTTP allowed on 127.0.0.1 when FLASK_ENV=development or
OAUTHLIB_INSECURE_TRANSPORT=1 in .env.
"""

import os

# Resolve project root locally — do NOT import app.config here.
# Importing Config before load_dotenv() freezes SECRET_KEY as the default
# ("dev-change-this-in-production"), which breaks session cookies and
# Fernet-encrypted Gmail tokens that were saved with the .env key.
_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

_dotenv_loaded = False
_oauth_configured = False


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in ("1", "true", "yes", "on")


def is_production_env() -> bool:
    """True when app should enforce HTTPS for OAuth."""
    env = (os.environ.get("FLASK_ENV") or os.environ.get("ENV") or "").strip().lower()
    if env == "production":
        return True
    if _truthy(os.environ.get("PRODUCTION")):
        return True
    return False


def load_dotenv_if_needed() -> None:
    global _dotenv_loaded
    if _dotenv_loaded:
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(os.path.join(_BASE_DIR, ".env"))
    except ImportError:
        pass
    _dotenv_loaded = True


def configure_oauth_transport() -> None:
    """
    Set OAUTHLIB_INSECURE_TRANSPORT for local HTTP OAuth only.
    Must run before google_auth_oauthlib / requests_oauthlib token exchange.
    """
    global _oauth_configured

    load_dotenv_if_needed()

    if is_production_env():
        os.environ.pop("OAUTHLIB_INSECURE_TRANSPORT", None)
        _oauth_configured = True
        return

    # Explicit .env override (local only — ignored in production above)
    if _truthy(os.environ.get("OAUTHLIB_INSECURE_TRANSPORT")):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        _oauth_configured = True
        return

    # Dev fallback: FLASK_ENV=development or FLASK_DEBUG=1
    flask_env = (os.environ.get("FLASK_ENV") or "development").strip().lower()
    if flask_env == "development" or _truthy(os.environ.get("FLASK_DEBUG")):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    _oauth_configured = True


def bootstrap_environment() -> None:
    """Load .env and apply OAuth transport rules (idempotent)."""
    load_dotenv_if_needed()
    configure_oauth_transport()


def ensure_oauth_transport_configured() -> None:
    """Safe to call from gmail_service before token exchange."""
    if not _oauth_configured:
        configure_oauth_transport()
