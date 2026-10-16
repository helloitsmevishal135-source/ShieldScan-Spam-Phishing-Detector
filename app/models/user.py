from datetime import datetime

import mongoengine as me
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


class User(UserMixin, me.Document):
    """Registered user account — stored in MongoDB."""

    meta = {"collection": "users", "indexes": ["email"]}

    username = me.StringField(max_length=80, required=True)
    email = me.StringField(max_length=120, required=True, unique=True)
    password_hash = me.StringField(max_length=256, required=True)
    created_at = me.DateTimeField(default=datetime.utcnow)

    # Gmail OAuth (tokens stored encrypted)
    gmail_connected = me.BooleanField(default=False)
    gmail_access_token = me.StringField(null=True)
    gmail_refresh_token = me.StringField(null=True)
    gmail_token_expiry = me.DateTimeField(null=True)
    gmail_last_sync = me.DateTimeField(null=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # Flask-Login requires get_id() to return a string
    def get_id(self) -> str:
        return str(self.pk)
