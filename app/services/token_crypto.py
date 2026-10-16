"""Encrypt OAuth tokens at rest using Fernet."""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app


def _fernet() -> Fernet:
    key_material = (
        current_app.config.get("TOKEN_ENCRYPTION_KEY")
        or current_app.config.get("SECRET_KEY")
        or "dev-change-this-in-production"
    )
    digest = hashlib.sha256(key_material.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_token(value: str | None) -> str | None:
    if not value:
        return None
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_token(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None
