"""Website Link Analyzer — crawl, extract links, classify, and report."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from flask import current_app

from app.ml.crawler.security import is_public_http_url
from app.ml.html_features.extractor import HTMLFeatureExtractor
from app.ml.inference import classify_url, predict
from app.ml.risk_engine.scorer import compute_risk_assessment
from app.ml.utils.url_normalize import dedupe_urls, normalize_url, registered_domain
from app.services.trusted_domains import get_trusted_domains
from app.services.blocked_domains import get_blocked_domains

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "ShieldScan-Crawler/1.0 (+https://localhost; security research crawler)"
    ),
    "Accept": "text/html,application/xhtml+xml",
}


@dataclass
class LinkAnalysis:
    url: str
    category: str
    label: str
    model_probability: float
    risk_score: float
    threat_level: str
    reasons: list[str] = field(default_factory=list)


def _categorize_link(url: str, seed_domain: str) -> str:
    if not url:
        return "null"
    parsed = urlparse(url)
    if not parsed.hostname:
        return "null"
    if registered_domain(parsed.hostname) == seed_domain:
        return "internal"
    return "external"


def _classify_threat_level(label: str, probability: float) -> str:
    label_upper = label.upper()
    if "PHISHING" in label_upper and probability >= 70:
        return "dangerous"
    if "PHISHING" in label_upper or probability >= 40:
        return "suspicious"
    return "safe"


def _extract_raw_links(html: str, page_url: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    candidates: list[str] = []

    for tag in soup.find_all(["a", "link", "area", "form", "iframe"]):
        for attr in ("href", "action", "src"):
            value = tag.get(attr)
            if value:
                candidates.append(str(value))

    normalized: list[str] = []
    for raw in candidates:
        url = normalize_url(raw, page_url)
        if url:
            normalized.append(url)
    return dedupe_urls(normalized)


def _analyze_link(url: str, category: str, trusted: set[str], blocked: set[str]) -> LinkAnalysis:
    label, probability, feature_summary = classify_url(url)
    domain = registered_domain(urlparse(url).hostname or "")
    assessment = compute_risk_assessment(
        model_probability=probability,
        input_type="URL",
        label=label,
        url_feature_summary=feature_summary,
        trusted_domains=trusted,
        blocked_domains=blocked,
        scanned_domain=domain,
    )
    return LinkAnalysis(
        url=url,
        category=category,
        label=label,
        model_probability=assessment.model_probability,
        risk_score=assessment.risk_score,
        threat_level=assessment.threat_level,
        reasons=assessment.reasons,
    )


def analyze_website(seed_url: str, *, max_links: int | None = None) -> dict:
    """
    Download a webpage, extract hyperlinks, classify each with the phishing model,
    and return a complete security report.
    """
    normalized_seed = normalize_url(seed_url)
    if not normalized_seed:
        raise ValueError("Invalid or unsupported URL.")

    if not is_public_http_url(normalized_seed):
        raise ValueError(
            "Could not crawl website: The domain could not be reached or is not a public website. "
            "Note: The Website Link Analyzer requires an active, live website to crawl. "
            "To analyze text patterns or offline/sample phishing links, please use the Quick Scan above."
        )

    timeout = 12
    max_bytes = 2_000_000
    max_links = max_links or 50
    try:
        timeout = current_app.config.get("CRAWLER_TIMEOUT_SECONDS", timeout)
        max_bytes = current_app.config.get("CRAWLER_MAX_BYTES", max_bytes)
        if max_links == 50:
            max_links = current_app.config.get("CRAWLER_MAX_LINKS", max_links)
    except RuntimeError:
        pass

    logger.info("Crawler fetching seed URL: %s", normalized_seed)

    response = requests.get(
        normalized_seed,
        headers=DEFAULT_HEADERS,
        timeout=timeout,
        allow_redirects=True,
    )
    response.raise_for_status()

    if len(response.content) > max_bytes:
        raise ValueError("Page is too large to analyze safely.")

    final_url = response.url or normalized_seed
    html = response.text
    seed_domain = registered_domain(urlparse(final_url).hostname or "")

    raw_links = _extract_raw_links(html, final_url)
    link_records: list[dict] = []
    for url in raw_links:
        link_records.append(
            {
                "url": url,
                "category": _categorize_link(url, seed_domain),
            }
        )

    html_extractor = HTMLFeatureExtractor()
    html_features = html_extractor.extract(html, page_url=final_url, link_records=link_records)

    trusted = get_trusted_domains()
    blocked = get_blocked_domains()
    analyzed_links: list[LinkAnalysis] = []
    for record in link_records[:max_links]:
        try:
            analyzed_links.append(_analyze_link(record["url"], record["category"], trusted, blocked))
        except Exception as exc:
            logger.warning("Link analysis failed for %s: %s", record["url"], exc)

    seed_prediction = predict(final_url)
    phishing_count = sum(1 for link in analyzed_links if "PHISHING" in link.label.upper())
    suspicious_count = sum(
        1 for link in analyzed_links if link.threat_level == "suspicious"
    )
    safe_count = sum(1 for link in analyzed_links if link.threat_level == "safe")

    overall = compute_risk_assessment(
        model_probability=seed_prediction.get("model_probability", seed_prediction.get("confidence", 0)),
        input_type="WEBSITE",
        label=seed_prediction.get("label", "UNKNOWN"),
        url_feature_summary=seed_prediction.get("feature_summary", {}).get("url", {}),
        html_summary=html_features,
        trusted_domains=trusted,
        blocked_domains=blocked,
        scanned_domain=seed_domain,
        suspicious_link_count=suspicious_count,
        phishing_link_count=phishing_count,
    )

    report = {
        "seed_url": final_url,
        "pages_crawled": 1,
        "html_features": html_features,
        "link_summary": {
            "total_hyperlinks": len(link_records),
            "internal_hyperlinks": sum(1 for r in link_records if r["category"] == "internal"),
            "external_hyperlinks": sum(1 for r in link_records if r["category"] == "external"),
            "null_hyperlinks": sum(1 for r in link_records if r["category"] == "null"),
            "analyzed_links": len(analyzed_links),
            "safe_hyperlinks": safe_count,
            "suspicious_hyperlinks": suspicious_count,
            "phishing_hyperlinks": phishing_count,
        },
        "seed_analysis": seed_prediction,
        "links": [
            {
                "url": link.url,
                "category": link.category,
                "label": link.label,
                "model_probability": link.model_probability,
                "risk_score": link.risk_score,
                "threat_level": link.threat_level,
                "reasons": link.reasons,
            }
            for link in analyzed_links
        ],
        "overall": {
            "model_probability": overall.model_probability,
            "risk_score": overall.risk_score,
            "threat_level": overall.threat_level,
            "reasons": overall.reasons,
            "feature_summary": overall.feature_summary,
        },
    }

    logger.info(
        "Crawler report for %s: links=%d analyzed=%d phishing=%d risk=%.1f",
        final_url,
        len(link_records),
        len(analyzed_links),
        phishing_count,
        overall.risk_score,
    )
    return report
