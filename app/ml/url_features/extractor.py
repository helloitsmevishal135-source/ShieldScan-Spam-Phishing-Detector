"""Locally computable URL features for phishing detection."""

from __future__ import annotations

import re
from urllib.parse import urlparse, unquote

import numpy as np

from app.ml.utils.url_normalize import registered_domain

LOCAL_URL_FEATURE_NAMES = [
    "length_url",
    "length_hostname",
    "ip",
    "nb_dots",
    "nb_hyphens",
    "nb_at",
    "nb_qm",
    "nb_and",
    "nb_or",
    "nb_eq",
    "nb_underscore",
    "nb_tilde",
    "nb_percent",
    "nb_slash",
    "nb_star",
    "nb_colon",
    "nb_comma",
    "nb_semicolumn",
    "nb_dollar",
    "nb_space",
    "nb_www",
    "nb_com",
    "nb_dslash",
    "http_in_path",
    "https_token",
    "punycode",
    "port",
    "tld_in_path",
    "tld_in_subdomain",
    "abnormal_subdomain",
    "nb_subdomains",
    "prefix_suffix",
    "random_domain",
    "shortening_service",
    "path_extension",
    "ratio_digits_url",
    "ratio_digits_host",
    "length_words_raw",
    "char_repeat",
    "shortest_words_raw",
    "shortest_word_host",
    "shortest_word_path",
    "longest_words_raw",
    "longest_word_host",
    "longest_word_path",
    "avg_words_raw",
    "avg_word_host",
    "avg_word_path",
    "phish_hints",
    "domain_in_brand",
    "brand_in_subdomain",
    "brand_in_path",
    "suspecious_tld",
    "statistical_report",
]

IP_PATTERN = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
SHORTENERS = {
    "bit.ly",
    "tinyurl.com",
    "goo.gl",
    "t.co",
    "ow.ly",
    "is.gd",
    "buff.ly",
    "cutt.ly",
    "rebrand.ly",
    "shorturl.at",
}
SUSPICIOUS_TLDS = {".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".ru", ".work", ".click"}
PHISH_HINTS = [
    "login",
    "verify",
    "secure",
    "account",
    "update",
    "bank",
    "confirm",
    "signin",
    "password",
    "wallet",
]
BRANDS = [
    "paypal",
    "google",
    "microsoft",
    "apple",
    "amazon",
    "facebook",
    "netflix",
    "instagram",
    "whatsapp",
    "chase",
    "wellsfargo",
]
# Dangerous / unusual download-style extensions used by the training dataset.
PATH_EXTENSIONS = re.compile(r"\.(txt|exe|js|apk|scr|zip|jar|bat|cmd|dll)$", re.I)


def _word_stats(text: str) -> tuple[int, int, int, float]:
    words = [w for w in re.split(r"[/.\-_]+", text) if w]
    if not words:
        return 0, 0, 0, 0.0
    lengths = [len(w) for w in words]
    return min(lengths), max(lengths), sum(lengths), sum(lengths) / len(lengths)


def _char_repeat_score(text: str) -> int:
    """Count characters that appear consecutively 2+ times (dataset-compatible)."""
    if not text:
        return 0
    score = 0
    prev = ""
    run = 0
    for ch in text:
        if ch == prev:
            run += 1
            if run == 2:
                score += 1
        else:
            prev = ch
            run = 1
    return score


def _prepare_url(url: str) -> str:
    """
    Light cleanup for feature extraction.
    Preserves the original path shape (no forced trailing slash) so
    length/slash counts stay consistent with training URLs.
    """
    raw = unquote(str(url or "").strip())
    if not raw:
        return ""
    if raw.startswith("//"):
        raw = "https:" + raw
    elif not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw):
        raw = "https://" + raw
    return raw


def _is_shortener(hostname: str) -> bool:
    host = (hostname or "").lower().rstrip(".")
    if not host:
        return False
    if host in SHORTENERS:
        return True
    return any(host.endswith("." + shortener) for shortener in SHORTENERS)


def _count_nb_com(raw: str, hostname: str) -> int:
    """Count '.com' occurrences excluding the hostname's TLD '.com'."""
    host = (hostname or "").lower()
    remainder = raw.lower()
    if host and host in remainder:
        # Count in host excluding trailing TLD .com, plus path/query.
        host_idx = remainder.find(host)
        host_part = host
        path_part = remainder[host_idx + len(host) :]
        if host_part.endswith(".com"):
            host_count = host_part[:-4].count(".com")
        else:
            host_count = host_part.count(".com")
        return host_count + path_part.count(".com")
    return remainder.count(".com")


class URLFeatureExtractor:
    """Extract phishing URL features without external network calls."""

    feature_names = LOCAL_URL_FEATURE_NAMES

    def extract(self, url: str) -> np.ndarray:
        raw = _prepare_url(url)
        if not raw:
            return np.zeros(len(self.feature_names), dtype=float)

        parsed = urlparse(raw)
        hostname = (parsed.hostname or "").lower()
        # Keep original casing for length counts; use lower copy for token checks.
        raw_lower = raw.lower()
        path = parsed.path or ""
        host_no_www = hostname[4:] if hostname.startswith("www.") else hostname
        tld = host_no_www.split(".")[-1] if "." in host_no_www else ""

        words_raw = [w for w in re.split(r"[/.\-_]+", raw_lower) if w]
        words_host = [w for w in re.split(r"[.\-_]+", hostname) if w]
        words_path = [w for w in re.split(r"[/.\-_]+", path.lower()) if w]

        shortest_raw, longest_raw, _total_raw, avg_raw = _word_stats(raw_lower)
        shortest_host, longest_host, _total_host, avg_host = _word_stats(hostname)
        shortest_path, longest_path, _total_path, avg_path = _word_stats(path.lower())

        reg_domain = registered_domain(hostname)
        brand_in_domain = any(brand in reg_domain for brand in BRANDS)
        brand_in_sub = any(brand in host_no_www and brand not in reg_domain for brand in BRANDS)
        brand_in_path = any(brand in path.lower() for brand in BRANDS)

        # Dataset semantics: https_token=1 means the URL uses http (not https).
        https_token = int((parsed.scheme or "").lower() != "https")

        # Count '//' outside the scheme separator (protocol://).
        after_scheme = raw.split("://", 1)[1] if "://" in raw else raw
        nb_dslash = after_scheme.count("//")

        labels = host_no_www.split(".") if host_no_www else []
        nb_subdomains = max(len(labels) - 1, 0)

        features = {
            "length_url": len(raw),
            "length_hostname": len(hostname),
            "ip": int(bool(IP_PATTERN.match(hostname))),
            "nb_dots": raw.count("."),
            "nb_hyphens": raw.count("-"),
            "nb_at": raw.count("@"),
            "nb_qm": raw.count("?"),
            "nb_and": raw.count("&"),
            "nb_or": raw.count("|"),
            "nb_eq": raw.count("="),
            "nb_underscore": raw.count("_"),
            "nb_tilde": raw.count("~"),
            "nb_percent": raw.count("%"),
            "nb_slash": raw.count("/"),
            "nb_star": raw.count("*"),
            "nb_colon": raw.count(":"),
            "nb_comma": raw.count(","),
            "nb_semicolumn": raw.count(";"),
            "nb_dollar": raw.count("$"),
            "nb_space": raw.count(" ") + raw_lower.count("%20"),
            "nb_www": raw_lower.count("www"),
            "nb_com": _count_nb_com(raw, hostname),
            "nb_dslash": nb_dslash,
            "http_in_path": int("http" in path.lower()),
            "https_token": https_token,
            "punycode": int("xn--" in raw_lower),
            "port": int(parsed.port is not None),
            "tld_in_path": int(bool(tld and f".{tld}" in path.lower())),
            "tld_in_subdomain": int(bool(tld and host_no_www.count(f".{tld}") > 1)),
            "abnormal_subdomain": int(len(labels) > 3),
            "nb_subdomains": nb_subdomains,
            "prefix_suffix": int("-" in (labels[0] if labels else "")),
            "random_domain": int(bool(re.search(r"[a-z]{5,}\d{2,}|\d{4,}[a-z]{3,}", host_no_www))),
            "shortening_service": int(_is_shortener(hostname)),
            "path_extension": int(bool(PATH_EXTENSIONS.search(path))),
            "ratio_digits_url": sum(c.isdigit() for c in raw) / len(raw) if raw else 0,
            "ratio_digits_host": sum(c.isdigit() for c in hostname) / len(hostname) if hostname else 0,
            "length_words_raw": len(words_raw),
            "char_repeat": _char_repeat_score(raw_lower),
            "shortest_words_raw": shortest_raw,
            "shortest_word_host": shortest_host,
            "shortest_word_path": shortest_path,
            "longest_words_raw": longest_raw,
            "longest_word_host": longest_host,
            "longest_word_path": longest_path,
            "avg_words_raw": avg_raw,
            "avg_word_host": avg_host,
            "avg_word_path": avg_path,
            "phish_hints": sum(1 for hint in PHISH_HINTS if hint in raw_lower),
            "domain_in_brand": int(brand_in_domain),
            "brand_in_subdomain": int(brand_in_sub),
            "brand_in_path": int(brand_in_path),
            "suspecious_tld": int(any(host_no_www.endswith(tld_name) for tld_name in SUSPICIOUS_TLDS)),
            "statistical_report": int(
                raw.count(".") > 3
                or raw.count("-") > 3
                or (sum(c.isdigit() for c in raw) / len(raw) if raw else 0) > 0.3
            ),
        }
        return np.array([float(features[name]) for name in self.feature_names], dtype=float)

    def transform(self, urls: list[str]) -> np.ndarray:
        return np.vstack([self.extract(url) for url in urls])

    def extract_dict(self, url: str) -> dict[str, float]:
        values = self.extract(url)
        return {name: float(values[i]) for i, name in enumerate(self.feature_names)}
