"""Explainable risk scoring across ML, URL, HTML, and trust signals."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.ml.utils.url_normalize import registered_domain
from app.services.trusted_domains import get_builtin_high_reputation_domains


@dataclass
class RiskAssessment:
    model_probability: float
    risk_score: float
    threat_level: str
    reasons: list[str] = field(default_factory=list)
    feature_summary: dict = field(default_factory=dict)
    trusted_domain_signal: float = 0.0


HIGH_RISK_URL_FLAGS = {"ip", "punycode", "shortening_service", "phish_hints", "suspecious_tld"}


def _threat_level_from_score(score: float) -> str:
    if score >= 75:
        return "dangerous"
    if score >= 40:
        return "suspicious"
    return "safe"


def trusted_domain_adjustment(domain: str, trusted_domains: set[str]) -> tuple[float, list[str]]:
    reg = registered_domain(domain or "")
    if not reg or reg not in trusted_domains:
        return 0.0, []
    if reg in get_builtin_high_reputation_domains():
        return -22.0, [
            f"Registered domain '{reg}' is a well-known high-reputation site "
            "(trust signal only, not an automatic safe verdict)."
        ]
    return -8.0, [f"Registered domain '{reg}' is on the trusted list (small positive signal only)."]


def blocked_domain_adjustment(domain: str, blocked_domains: set[str]) -> tuple[float, list[str]]:
    reg = registered_domain(domain or "")
    if reg and reg in blocked_domains:
        return 25.0, [f"Registered domain '{reg}' is on the blocklist."]
    return 0.0, []


def clean_url_structure_adjustment(url_feature_summary: dict | None) -> tuple[float, list[str]]:
    """
    Modest discount for HTTPS URLs with no high-risk lexical flags.
    Counters apex-domain false positives from nb_www/length biases.
    """
    if not url_feature_summary:
        return 0.0, []

    high_risk = any(float(url_feature_summary.get(key, 0) or 0) > 0 for key in HIGH_RISK_URL_FLAGS)
    if high_risk:
        return 0.0, []
    if float(url_feature_summary.get("abnormal_subdomain", 0) or 0) > 0:
        return 0.0, []

    # Dataset encoding: https_token=1 means HTTP (less preferred), 0 means HTTPS.
    https_token = url_feature_summary.get("https_token", 1)
    if https_token is None:
        https_token = 1
    uses_https = float(https_token) == 0.0
    if uses_https:
        return -12.0, ["Clean HTTPS URL structure with no high-risk lexical flags."]
    return 0.0, []


def compute_risk_assessment(
    *,
    model_probability: float,
    input_type: str,
    label: str,
    url_feature_summary: dict | None = None,
    html_summary: dict | None = None,
    trusted_domains: set[str] | None = None,
    blocked_domains: set[str] | None = None,
    scanned_domain: str = "",
    suspicious_link_count: int = 0,
    phishing_link_count: int = 0,
) -> RiskAssessment:
    reasons: list[str] = []
    score = float(model_probability)

    label_upper = str(label).upper()
    if "SPAM" in label_upper or "PHISHING" in label_upper:
        reasons.append(f"ML classifier flagged content as {label_upper}.")
    elif "HAM" in label_upper or "SAFE" in label_upper:
        reasons.append(f"ML classifier indicates {label_upper}.")

    if input_type == "URL":
        reasons.append("Input routed to URL phishing analysis.")
    elif input_type == "WEBSITE":
        reasons.append("Website crawl and hyperlink analysis performed.")
    else:
        reasons.append("Input routed to text spam analysis.")

    trust_adj, trust_reasons = trusted_domain_adjustment(
        scanned_domain, trusted_domains or set()
    )
    score += trust_adj
    reasons.extend(trust_reasons)

    block_adj, block_reasons = blocked_domain_adjustment(
        scanned_domain, blocked_domains or set()
    )
    score += block_adj
    reasons.extend(block_reasons)

    clean_adj, clean_reasons = clean_url_structure_adjustment(url_feature_summary)
    score += clean_adj
    reasons.extend(clean_reasons)

    if url_feature_summary:
        high_risk_flags = {
            key: value
            for key, value in url_feature_summary.items()
            if key in HIGH_RISK_URL_FLAGS and float(value) > 0
        }
        for key, value in high_risk_flags.items():
            score += 4
            reasons.append(f"URL feature '{key}' triggered ({value}).")

    if html_summary:
        risky_html = {
            "login_form": 8,
            "iframe": 6,
            "popup_window": 5,
            "submit_email": 7,
            "empty_title": 4,
        }
        for key, weight in risky_html.items():
            if float(html_summary.get(key, 0)) > 0:
                score += weight
                reasons.append(f"HTML feature '{key}' increased risk.")

    if suspicious_link_count:
        score += min(suspicious_link_count * 3, 15)
        reasons.append(f"{suspicious_link_count} suspicious hyperlink(s) detected.")
    if phishing_link_count:
        score += min(phishing_link_count * 8, 30)
        reasons.append(f"{phishing_link_count} phishing hyperlink(s) detected.")

    score = max(0.0, min(100.0, round(score, 2)))
    return RiskAssessment(
        model_probability=round(float(model_probability), 2),
        risk_score=score,
        threat_level=_threat_level_from_score(score),
        reasons=reasons,
        feature_summary={
            "url": url_feature_summary or {},
            "html": html_summary or {},
        },
        trusted_domain_signal=abs(trust_adj),
    )
