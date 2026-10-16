"""Gmail OAuth2 and message fetching via Google API."""

import base64
import logging
import secrets
from datetime import datetime, timezone
from urllib.parse import urlencode

from app.env_bootstrap import ensure_oauth_transport_configured

# Required before google_auth_oauthlib token exchange on http://127.0.0.1 (dev only)
ensure_oauth_transport_configured()

from flask import current_app, request, session
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.extensions import db
from app.services.email_scan_service import scan_email_content
from app.services.gmail_content import extract_email_content
from app.services.token_crypto import decrypt_token, encrypt_token

logger = logging.getLogger(__name__)

# Pending OAuth: state + PKCE verifier + redirect_uri (must survive Google redirect)
OAUTH_PENDING_KEY = "gmail_oauth_pending"


def _utc_now_aware() -> datetime:
    """Current time as timezone-aware UTC."""
    return datetime.now(timezone.utc)


def _utc_now_naive() -> datetime:
    """Current time as naive UTC (matches google.auth._helpers.utcnow())."""
    return _utc_now_aware().replace(tzinfo=None)


def _to_aware_utc(value: datetime) -> datetime:
    """Convert any datetime to timezone-aware UTC for safe comparison."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _to_naive_utc(value: datetime) -> datetime:
    """Convert any datetime to naive UTC for google-auth Credentials.expiry."""
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _normalize_expiry(value: datetime | None) -> datetime | None:
    """Normalize token expiry for DB storage and google-auth (naive UTC)."""
    if value is None:
        return None
    return _to_naive_utc(value)


def _is_token_expired(expiry: datetime | None, *, now: datetime | None = None) -> bool:
    """Compare expiry to now with both values normalized to aware UTC."""
    if expiry is None:
        return False
    now = now or _utc_now_aware()
    expiry_aware = _to_aware_utc(expiry)
    now_aware = _to_aware_utc(now)
    return now_aware >= expiry_aware


def _credentials_expired(creds: Credentials) -> bool:
    """Check expiry using google-auth; fall back to aware UTC comparison on mismatch."""
    if creds.expiry is not None:
        creds.expiry = _normalize_expiry(creds.expiry)
    try:
        return creds.expired
    except TypeError:
        logger.warning(
            "Naive/aware datetime mismatch on creds.expired; using UTC-normalized comparison"
        )
        return _is_token_expired(creds.expiry)


def google_oauth_configured() -> bool:
    return bool(
        current_app.config.get("GOOGLE_CLIENT_ID")
        and current_app.config.get("GOOGLE_CLIENT_SECRET")
    )


def get_redirect_uri() -> str:
    """Single source of truth for OAuth redirect — must match Google Cloud Console."""
    uri = (current_app.config.get("GOOGLE_REDIRECT_URI") or "").strip()
    if not uri:
        raise ValueError(
            "GOOGLE_REDIRECT_URI is not set. Add it to .env and match Google Cloud Console exactly."
        )
    return uri


def _oauth_flow(redirect_uri: str) -> Flow:
    client_config = {
        "web": {
            "client_id": current_app.config["GOOGLE_CLIENT_ID"],
            "client_secret": current_app.config["GOOGLE_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=current_app.config["GMAIL_SCOPES"],
        redirect_uri=redirect_uri,
    )


def _save_oauth_pending(*, state: str, code_verifier: str, redirect_uri: str) -> None:
    session[OAUTH_PENDING_KEY] = {
        "state": state,
        "code_verifier": code_verifier,
        "redirect_uri": redirect_uri,
    }
    session.modified = True


def _load_oauth_pending() -> dict | None:
    return session.get(OAUTH_PENDING_KEY)


def _clear_oauth_pending() -> None:
    session.pop(OAUTH_PENDING_KEY, None)
    session.modified = True


def build_authorization_response() -> str:
    """
    Build the callback URL for fetch_token using GOOGLE_REDIRECT_URI + query params.
    Avoids host/scheme mismatch (127.0.0.1 vs localhost) that breaks token exchange.
    """
    redirect_uri = get_redirect_uri()
    params = {k: v for k, v in request.args.items() if k != "error"}
    if not params:
        return redirect_uri
    return f"{redirect_uri}?{urlencode(params)}"


def format_oauth_error(exc: Exception) -> str:
    """User-visible summary; full detail is logged separately."""
    name = type(exc).__name__
    msg = str(exc).strip() or "unknown error"
    lower = msg.lower()
    hints = []

    if "invalid_grant" in lower:
        hints.append("Revoke this app at myaccount.google.com/permissions and try again.")
    if "redirect_uri" in lower or "redirect" in lower:
        hints.append("GOOGLE_REDIRECT_URI must match Google Cloud Console exactly.")
    if "verifier" in lower or "code_challenge" in lower:
        hints.append("OAuth session expired — click Connect Gmail again without delay.")
    if "invalid_client" in lower:
        hints.append("Check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env.")

    hint_text = " ".join(hints)
    if hint_text:
        return f"{name}: {msg} — {hint_text}"
    return f"{name}: {msg}"


def start_oauth_authorization() -> str:
    """Return Google authorization URL; stores state + PKCE verifier in session."""
    redirect_uri = get_redirect_uri()
    flow = _oauth_flow(redirect_uri)

    state = secrets.token_urlsafe(32)
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=state,
    )

    if not flow.code_verifier:
        raise RuntimeError("OAuth PKCE code_verifier was not generated.")

    _save_oauth_pending(
        state=state,
        code_verifier=flow.code_verifier,
        redirect_uri=redirect_uri,
    )
    logger.info("Gmail OAuth started (redirect_uri=%s)", redirect_uri)
    return authorization_url


def complete_oauth(user, authorization_response: str, state: str) -> None:
    """Exchange authorization code for tokens using the same PKCE verifier + redirect URI."""
    pending = _load_oauth_pending()
    if not pending:
        raise ValueError(
            "OAuth session expired or was lost. Please click Connect Gmail again."
        )

    expected_state = pending.get("state")
    if not expected_state or state != expected_state:
        _clear_oauth_pending()
        raise ValueError("Invalid OAuth state. Please connect Gmail again.")

    redirect_uri = pending.get("redirect_uri") or get_redirect_uri()
    code_verifier = pending.get("code_verifier")
    if not code_verifier:
        _clear_oauth_pending()
        raise ValueError("Missing OAuth PKCE verifier. Please connect Gmail again.")

    # Restore the same redirect_uri and PKCE verifier — do not use a fresh Flow
    flow = _oauth_flow(redirect_uri)
    flow.code_verifier = code_verifier

    try:
        flow.fetch_token(authorization_response=authorization_response)
    except Exception as exc:
        logger.exception(
            "Gmail OAuth fetch_token failed (redirect_uri=%s, response=%s)",
            redirect_uri,
            authorization_response,
        )
        raise RuntimeError(format_oauth_error(exc)) from exc
    finally:
        _clear_oauth_pending()

    creds = flow.credentials
    if not creds or not creds.token:
        raise RuntimeError("Token exchange succeeded but no access token was returned.")

    user.gmail_access_token = encrypt_token(creds.token)
    user.gmail_refresh_token = encrypt_token(creds.refresh_token)
    user.gmail_token_expiry = _normalize_expiry(creds.expiry)
    user.gmail_connected = True
    user.save()

    if not creds.refresh_token:
        logger.warning(
            "Gmail connected for user %s without refresh_token; re-consent may be needed later.",
            user.id,
        )
    else:
        logger.info("Gmail OAuth completed for user %s", user.id)


def disconnect_gmail(user) -> None:
    user.gmail_connected = False
    user.gmail_access_token = None
    user.gmail_refresh_token = None
    user.gmail_token_expiry = None
    user.gmail_last_sync = None
    user.save()


def _user_credentials(user) -> Credentials | None:
    access = decrypt_token(user.gmail_access_token)
    refresh = decrypt_token(user.gmail_refresh_token)
    if not access and not refresh:
        # Encrypted values present but undecryptable usually means SECRET_KEY changed.
        if user.gmail_access_token or user.gmail_refresh_token:
            raise ValueError(
                "Gmail credentials could not be decrypted. Please disconnect and reconnect Gmail."
            )
        return None

    creds = Credentials(
        token=access,
        refresh_token=refresh,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=current_app.config["GOOGLE_CLIENT_ID"],
        client_secret=current_app.config["GOOGLE_CLIENT_SECRET"],
        scopes=current_app.config["GMAIL_SCOPES"],
    )
    if user.gmail_token_expiry:
        creds.expiry = _normalize_expiry(user.gmail_token_expiry)

    if _credentials_expired(creds):
        if not creds.refresh_token:
            raise ValueError(
                "Gmail access expired and no refresh token is available. "
                "Please disconnect and reconnect Gmail."
            )
        creds.refresh(Request())
        user.gmail_access_token = encrypt_token(creds.token)
        if creds.refresh_token:
            user.gmail_refresh_token = encrypt_token(creds.refresh_token)
        user.gmail_token_expiry = _normalize_expiry(creds.expiry)
        user.save()

    return creds


def _gmail_client(user):
    creds = _user_credentials(user)
    if not creds:
        raise ValueError("Gmail is not connected or tokens are invalid.")
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def fetch_message_summaries(user) -> list[dict]:
    """List recent inbox messages (ids + snippet only)."""
    service = _gmail_client(user)
    max_results = current_app.config.get("GMAIL_FETCH_MAX_RESULTS", 25)
    response = (
        service.users()
        .messages()
        .list(userId="me", labelIds=["INBOX"], maxResults=max_results)
        .execute()
    )
    messages = response.get("messages") or []
    results = []
    for item in messages:
        msg_id = item.get("id")
        if not msg_id:
            continue
        try:
            detail = (
                service.users()
                .messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )
        except Exception as exc:
            logger.warning("Failed to fetch Gmail message %s: %s", msg_id, exc)
            continue

        if not isinstance(detail, dict):
            logger.warning("Unexpected Gmail message payload for id=%s", msg_id)
            continue

        extracted = extract_email_content(detail)
        results.append(
            {
                "id": msg_id,
                "subject": extracted["subject"],
                "sender": extracted["sender"],
                "snippet": detail.get("snippet") or "",
                "body": extracted["body"],
                "combined_text": extracted["combined_text"],
                "urls": extracted["urls"],
                "body_source": extracted.get("body_source", ""),
                "body_length": extracted.get("body_length", 0),
            }
        )
    return results


def sync_user_mailbox(user) -> int:
    """
    Fetch recent Gmail messages and scan new ones.
    Returns count of newly scanned messages.
    """
    if not user.gmail_connected:
        return 0

    scanned = 0
    for message in fetch_message_summaries(user):
        record = scan_email_content(
            user,
            gmail_message_id=message["id"],
            subject=message["subject"],
            sender=message["sender"],
            body=message["body"],
            snippet=message.get("snippet"),
            combined_text=message.get("combined_text"),
            body_source=message.get("body_source"),
            urls=message.get("urls"),
        )
        if record:
            scanned += 1

    user.gmail_last_sync = _utc_now_naive()
    user.save()
    return scanned
