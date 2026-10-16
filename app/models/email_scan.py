from datetime import datetime

import mongoengine as me

def _confidence_to_percent(value) -> float:
    if value is None:
        return 50.0
    try:
        n = float(value)
    except (TypeError, ValueError):
        return 50.0
    if n > 1.0:
        return round(n, 1)
    return round(n * 100.0, 1)



class EmailScan(me.Document):
    """Gmail message scan result for a user."""

    meta = {
        "collection": "email_scans",
        "indexes": [
            "user_id",
            "-created_at",
            {"fields": ["user_id", "gmail_message_id"], "unique": True},
        ],
    }

    user_id = me.StringField(required=True)  # stores User pk as string
    gmail_message_id = me.StringField(max_length=128, required=True)
    subject = me.StringField(max_length=512, default="")
    sender = me.StringField(max_length=256, default="")
    snippet = me.StringField(max_length=512, null=True)
    input_type = me.StringField(max_length=20, required=True)
    label = me.StringField(max_length=64, required=True)
    confidence = me.FloatField(required=True)
    threat_level = me.StringField(max_length=20, required=True)
    risk_label = me.StringField(max_length=16, required=True)  # safe | threat
    risk_score = me.FloatField(required=True)
    detected_reason = me.StringField(max_length=256, default="")
    created_at = me.DateTimeField(default=datetime.utcnow)

    @property
    def risk_score_percent(self) -> float:
        """Risk score for templates/API (handles 0–1 storage and legacy 0–100 rows)."""
        return _confidence_to_percent(self.risk_score)

    @property
    def user(self):
        """Fetch corresponding User document for display/admin."""
        from app.models.user import User

        if not self.user_id:
            return None
        try:
            return User.objects(pk=self.user_id).first()
        except Exception:
            return None
