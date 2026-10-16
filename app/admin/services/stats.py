"""Admin dashboard statistics — MongoDB version."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.models import CrawlerLog, EmailScan, Scan, ScanStatistic, SystemLog, TrainingLog, User


def _period_start(period: str) -> datetime:
    now = datetime.utcnow()
    if period == "daily":
        return now - timedelta(days=1)
    if period == "weekly":
        return now - timedelta(days=7)
    if period == "monthly":
        return now - timedelta(days=30)
    return now - timedelta(days=1)


def count_scans_since(since: datetime) -> int:
    manual = Scan.objects(created_at__gte=since).count()
    email = EmailScan.objects(created_at__gte=since).count()
    return manual + email


def get_dashboard_stats() -> dict:
    now = datetime.utcnow()
    daily_since = _period_start("daily")
    weekly_since = _period_start("weekly")
    monthly_since = _period_start("monthly")

    # Sum of links_found across all crawler logs
    crawler_links = sum(
        (c.links_found or 0) for c in CrawlerLog.objects.only("links_found")
    )

    return {
        "total_users": User.objects.count(),
        "total_scans": Scan.objects.count() + EmailScan.objects.count(),
        "manual_scans": Scan.objects.count(),
        "email_scans": EmailScan.objects.count(),
        "spam_detections": (
            Scan.objects(label__icontains="spam").count()
            + EmailScan.objects(label__icontains="spam").count()
        ),
        "phishing_detections": (
            Scan.objects(label__icontains="phishing").count()
            + EmailScan.objects(label__icontains="phishing").count()
        ),
        "daily_scans": count_scans_since(daily_since),
        "weekly_scans": count_scans_since(weekly_since),
        "monthly_scans": count_scans_since(monthly_since),
        "crawler_runs": CrawlerLog.objects.count(),
        "crawler_links": crawler_links,
        "training_runs": TrainingLog.objects.count(),
        "system_logs": SystemLog.objects.count(),
        "scan_statistics_rows": ScanStatistic.objects.count(),
        "generated_at": now.isoformat(),
    }


def get_scan_trend(days: int = 14) -> dict:
    """Daily scan counts for charting."""
    labels: list[str] = []
    manual_counts: list[int] = []
    email_counts: list[int] = []

    for offset in range(days - 1, -1, -1):
        day = datetime.utcnow().date() - timedelta(days=offset)
        start = datetime.combine(day, datetime.min.time())
        end = start + timedelta(days=1)
        labels.append(day.strftime("%b %d"))
        manual_counts.append(
            Scan.objects(created_at__gte=start, created_at__lt=end).count()
        )
        email_counts.append(
            EmailScan.objects(created_at__gte=start, created_at__lt=end).count()
        )

    return {"labels": labels, "manual": manual_counts, "email": email_counts}


def sync_scan_statistics() -> None:
    """Aggregate daily stats into scan_statistics collection."""
    today = datetime.utcnow().date()
    start = datetime.combine(today, datetime.min.time())
    end = start + timedelta(days=1)

    total = count_scans_since(start)
    spam = (
        Scan.objects(created_at__gte=start, created_at__lt=end, label__icontains="spam").count()
        + EmailScan.objects(created_at__gte=start, created_at__lt=end, label__icontains="spam").count()
    )
    phishing = (
        Scan.objects(created_at__gte=start, created_at__lt=end, label__icontains="phishing").count()
        + EmailScan.objects(created_at__gte=start, created_at__lt=end, label__icontains="phishing").count()
    )
    safe = (
        Scan.objects(created_at__gte=start, created_at__lt=end, threat_level="safe").count()
        + EmailScan.objects(created_at__gte=start, created_at__lt=end, risk_label="safe").count()
    )

    row = ScanStatistic.objects(period_type="daily", period_start=start).first()
    if not row:
        row = ScanStatistic(period_type="daily", period_start=start)
    row.total_scans = total
    row.spam_detections = spam
    row.phishing_detections = phishing
    row.safe_detections = safe
    row.save()
