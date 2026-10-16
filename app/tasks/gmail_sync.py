"""Periodic Gmail sync for all connected users."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.models import User
from app.services.gmail_service import sync_user_mailbox

logger = logging.getLogger(__name__)
_scheduler = None


def _sync_all_connected_users(app):
    with app.app_context():
        users = User.objects(gmail_connected=True)
        for user in users:
            try:
                count = sync_user_mailbox(user)
                if count:
                    logger.info("Gmail sync: user %s scanned %s new message(s)", str(user.pk), count)
            except Exception:
                logger.exception("Gmail sync failed for user %s", str(user.pk))


def init_gmail_scheduler(app):
    """Start background Gmail polling if interval > 0."""
    global _scheduler

    if _scheduler is not None:
        return

    interval = app.config.get("GMAIL_SYNC_INTERVAL_MINUTES", 5)
    if interval <= 0:
        return

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        func=lambda: _sync_all_connected_users(app),
        trigger="interval",
        minutes=interval,
        id="gmail_sync",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Gmail background sync started (every %s minutes)", interval)


def shutdown_gmail_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
