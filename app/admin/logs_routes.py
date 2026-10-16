"""Admin log viewer routes — MongoDB version."""

from flask import render_template, request

from app.admin.decorators import admin_required
from app.admin import admin_bp
from app.models import CrawlerLog, EmailScan, Scan, SystemLog, TrainingLog


@admin_bp.route("/logs")
@admin_required
def logs():
    category = (request.args.get("category") or "scan").strip().lower()
    q = (request.args.get("q") or "").strip()

    system_logs = []
    scan_logs = []
    email_logs = []
    training_logs = []
    crawler_logs = []

    if category in ("system", "prediction", "auth", "error", "all"):
        if category == "error":
            qs = SystemLog.objects(level__in=["ERROR", "CRITICAL", "WARNING"])
        elif category in ("all", "system"):
            qs = SystemLog.objects
        else:
            qs = SystemLog.objects(category=category)
        if q:
            qs = qs.filter(message__icontains=q)
        system_logs = qs.order_by("-created_at").limit(100)

    if category in ("scan", "all"):
        scan_qs = Scan.objects
        if q:
            scan_qs = Scan.objects(__raw__={
                "$or": [
                    {"input_text": {"$regex": q, "$options": "i"}},
                    {"label": {"$regex": q, "$options": "i"}},
                ]
            })
        scan_logs = scan_qs.order_by("-created_at").limit(100)

        email_qs = EmailScan.objects
        if q:
            email_qs = EmailScan.objects(__raw__={
                "$or": [
                    {"subject": {"$regex": q, "$options": "i"}},
                    {"sender": {"$regex": q, "$options": "i"}},
                ]
            })
        email_logs = email_qs.order_by("-created_at").limit(100)

    if category in ("training", "all"):
        training_qs = TrainingLog.objects
        if q:
            training_qs = training_qs.filter(model_name__icontains=q)
        training_logs = training_qs.order_by("-created_at").limit(50)

    if category in ("crawler", "all"):
        crawler_qs = CrawlerLog.objects
        if q:
            crawler_qs = crawler_qs.filter(seed_url__icontains=q)
        crawler_logs = crawler_qs.order_by("-created_at").limit(50)

    return render_template(
        "admin/logs.html",
        category=category,
        q=q,
        system_logs=system_logs,
        scan_logs=scan_logs,
        email_logs=email_logs,
        training_logs=training_logs,
        crawler_logs=crawler_logs,
    )
