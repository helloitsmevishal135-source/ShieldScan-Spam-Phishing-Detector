from datetime import datetime

import mongoengine as me


class Scan(me.Document):
    """Stored scan history for a user."""

    meta = {"collection": "scans", "indexes": ["user_id", "-created_at"]}

    user_id = me.StringField(required=True)  # stores User pk as string
    input_text = me.StringField(required=True)
    input_type = me.StringField(max_length=20, required=True)
    label = me.StringField(max_length=64, required=True)
    confidence = me.FloatField(required=True)
    threat_level = me.StringField(max_length=20, required=True)  # safe | suspicious | dangerous
    model_probability = me.FloatField(null=True)
    risk_score = me.FloatField(null=True)
    reasons_json = me.StringField(null=True)
    feature_summary_json = me.StringField(null=True)
    created_at = me.DateTimeField(default=datetime.utcnow)

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
