import os

# Project root (parent of app package)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    """Application configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-this-in-production")
    MONGODB_URI = os.environ.get(
        "MONGODB_URI",
        "mongodb+srv://helloitsmevishal135_db_user:ShieldScan2024@cluster0.ihkwyee.mongodb.net/shieldscan?retryWrites=true&w=majority&appName=Cluster0",
    )
    # Session cookie settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Google OAuth2 / Gmail (set in environment — never expose secret to frontend)
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.environ.get(
        "GOOGLE_REDIRECT_URI",
        "http://127.0.0.1:5000/gmail/callback",
    )
    GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    GMAIL_FETCH_MAX_RESULTS = int(os.environ.get("GMAIL_FETCH_MAX_RESULTS", "25"))
    GMAIL_SYNC_INTERVAL_MINUTES = int(os.environ.get("GMAIL_SYNC_INTERVAL_MINUTES", "5"))
    TOKEN_ENCRYPTION_KEY = os.environ.get("TOKEN_ENCRYPTION_KEY", "")

    # Website crawler
    CRAWLER_TIMEOUT_SECONDS = int(os.environ.get("CRAWLER_TIMEOUT_SECONDS", "12"))
    CRAWLER_MAX_LINKS = int(os.environ.get("CRAWLER_MAX_LINKS", "50"))
    CRAWLER_MAX_BYTES = int(os.environ.get("CRAWLER_MAX_BYTES", "2000000"))
