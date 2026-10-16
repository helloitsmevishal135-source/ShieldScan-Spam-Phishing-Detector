"""Website crawler service — persistence and scan history integration."""

from __future__ import annotations

import json
import logging

from app.ml.crawler.analyzer import analyze_website
from app.models import CrawlerLog, Scan, SystemLog
from app.services.ml_service import threat_display

logger = logging.getLogger(__name__)


def perform_website_analysis(user, seed_url: str) -> dict:
    """
    Crawl and analyze a website, persist crawler log + scan history, return report.
    """
    seed_url = (seed_url or "").strip()
    if not seed_url:
        raise ValueError("Website URL is required.")

    report = analyze_website(seed_url)
    overall = report["overall"]
    link_summary = report["link_summary"]
    threat_level = overall["threat_level"]
    uid = str(user.pk)

    crawler_log = CrawlerLog(
        user_id=uid,
        seed_url=report["seed_url"],
        pages_crawled=report.get("pages_crawled", 1),
        links_found=link_summary.get("total_hyperlinks", 0),
        report_json=json.dumps(report),
        status="completed",
    )
    crawler_log.save()

    scan = Scan(
        user_id=uid,
        input_text=report["seed_url"][:500],
        input_type="WEBSITE",
        label=report["seed_analysis"].get("label", "WEBSITE ANALYSIS"),
        confidence=overall["model_probability"],
        threat_level=threat_level,
        model_probability=overall["model_probability"],
        risk_score=overall["risk_score"],
        reasons_json=json.dumps(overall.get("reasons", [])),
        feature_summary_json=json.dumps(overall.get("feature_summary", {})),
    )
    scan.save()

    SystemLog(
        level="INFO",
        category="crawler",
        message=f"Website analyzed: {report['seed_url']}",
        details=json.dumps({
            "user_id": uid,
            "crawler_log_id": str(crawler_log.pk),
            "links_found": link_summary.get("total_hyperlinks", 0),
            "phishing_links": link_summary.get("phishing_hyperlinks", 0),
            "risk_score": overall["risk_score"],
        }),
    ).save()

    result = {
        **report,
        "threat_level": threat_level,
        "threat": threat_display(threat_level),
        "crawler_log_id": str(crawler_log.pk),
        "scan_id": str(scan.pk),
    }
    return result


def get_crawler_report(user, log_id: str) -> dict | None:
    log = CrawlerLog.objects(pk=log_id, user_id=str(user.pk)).first()
    if not log or not log.report_json:
        return None
    return json.loads(log.report_json)
