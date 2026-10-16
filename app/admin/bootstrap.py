"""Ensure a default admin account exists."""

from __future__ import annotations

import logging
import os

from app.models import AdminUser

logger = logging.getLogger(__name__)


def ensure_default_admin() -> None:
    if AdminUser.objects.count() > 0:
        return

    username = os.environ.get("ADMIN_USERNAME", "admin")
    email = os.environ.get("ADMIN_EMAIL", "admin@shieldscan.local")
    password = os.environ.get("ADMIN_PASSWORD", "admin12345")

    admin = AdminUser(username=username, email=email.lower(), is_active=True)
    admin.set_password(password)
    admin.save()
    logger.warning(
        "Created default admin account '%s'. Change ADMIN_PASSWORD in production.",
        username,
    )
