from datetime import datetime

import mongoengine as me
from werkzeug.security import check_password_hash, generate_password_hash


class AdminUser(me.Document):
    meta = {"collection": "admin_users", "indexes": ["email", "username"]}

    username = me.StringField(max_length=80, required=True, unique=True)
    email = me.StringField(max_length=120, required=True, unique=True)
    password_hash = me.StringField(max_length=256, required=True)
    is_active = me.BooleanField(default=True)
    created_at = me.DateTimeField(default=datetime.utcnow)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class SystemLog(me.Document):
    meta = {"collection": "system_logs", "indexes": ["level", "category", "-created_at"]}

    level = me.StringField(max_length=20, required=True)
    category = me.StringField(max_length=50, required=True)
    message = me.StringField(required=True)
    details = me.StringField(null=True)
    created_at = me.DateTimeField(default=datetime.utcnow)


class TrainingLog(me.Document):
    meta = {"collection": "training_logs", "indexes": ["model_name", "-created_at"]}

    model_name = me.StringField(max_length=80, required=True)
    version = me.StringField(max_length=40, required=True)
    metrics_json = me.StringField(required=True)
    artifact_path = me.StringField(max_length=512, null=True)
    trained_by = me.StringField(max_length=80, null=True)
    created_at = me.DateTimeField(default=datetime.utcnow)


class CrawlerLog(me.Document):
    meta = {"collection": "crawler_logs", "indexes": ["user_id", "-created_at"]}

    user_id = me.StringField(null=True)
    seed_url = me.StringField(max_length=1024, required=True)
    pages_crawled = me.IntField(default=0)
    links_found = me.IntField(default=0)
    report_json = me.StringField(null=True)
    status = me.StringField(max_length=20, default="completed")
    created_at = me.DateTimeField(default=datetime.utcnow)


class ModelVersion(me.Document):
    meta = {"collection": "model_versions", "indexes": ["model_name", "-created_at"]}

    model_name = me.StringField(max_length=80, required=True)
    version = me.StringField(max_length=40, required=True)
    artifact_path = me.StringField(max_length=512, required=True)
    metrics_json = me.StringField(null=True)
    is_active = me.BooleanField(default=False)
    created_at = me.DateTimeField(default=datetime.utcnow)


class TrustedDomain(me.Document):
    meta = {"collection": "trusted_domains", "indexes": ["domain"]}

    domain = me.StringField(max_length=255, required=True, unique=True)
    notes = me.StringField(max_length=512, null=True)
    is_active = me.BooleanField(default=True)
    created_at = me.DateTimeField(default=datetime.utcnow)


class BlockedDomain(me.Document):
    meta = {"collection": "blocked_domains", "indexes": ["domain"]}

    domain = me.StringField(max_length=255, required=True, unique=True)
    reason = me.StringField(max_length=512, null=True)
    is_active = me.BooleanField(default=True)
    created_at = me.DateTimeField(default=datetime.utcnow)


class ScanStatistic(me.Document):
    meta = {"collection": "scan_statistics", "indexes": ["period_type", "period_start"]}

    period_type = me.StringField(max_length=20, required=True)  # daily/weekly/monthly
    period_start = me.DateTimeField(required=True)
    total_scans = me.IntField(default=0)
    spam_detections = me.IntField(default=0)
    phishing_detections = me.IntField(default=0)
    safe_detections = me.IntField(default=0)
    created_at = me.DateTimeField(default=datetime.utcnow)
