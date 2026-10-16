"""HTML feature extraction for phishing website analysis."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.ml.utils.url_normalize import normalize_url, registered_domain

HTML_FEATURE_NAMES = [
    "nb_hyperlinks",
    "ratio_intHyperlinks",
    "ratio_extHyperlinks",
    "ratio_nullHyperlinks",
    "nb_extCSS",
    "ratio_intRedirection",
    "ratio_extRedirection",
    "ratio_intErrors",
    "ratio_extErrors",
    "login_form",
    "external_favicon",
    "links_in_tags",
    "submit_email",
    "ratio_intMedia",
    "ratio_extMedia",
    "sfh",
    "iframe",
    "popup_window",
    "safe_anchor",
    "onmouseover",
    "right_clic",
    "empty_title",
    "domain_in_title",
    "domain_with_copyright",
]


def _is_internal(url: str, base_domain: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    if not host:
        return False
    return registered_domain(host) == base_domain


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


class HTMLFeatureExtractor:
    """Compute locally analyzable HTML features from fetched page content."""

    feature_names = HTML_FEATURE_NAMES

    def extract(
        self,
        html: str,
        *,
        page_url: str,
        link_records: list[dict] | None = None,
    ) -> dict[str, float]:
        soup = BeautifulSoup(html or "", "lxml")
        base_domain = registered_domain(urlparse(page_url).hostname or "")
        link_records = link_records or []

        anchors = soup.find_all("a", href=True)
        all_links = soup.find_all(["a", "link", "area"], href=True)
        hyperlinks = len(all_links)

        internal = sum(1 for row in link_records if row.get("category") == "internal")
        external = sum(1 for row in link_records if row.get("category") == "external")
        null_links = sum(1 for row in link_records if row.get("category") == "null")

        ext_css = 0
        for tag in soup.find_all("link", rel=True):
            rel = " ".join(tag.get("rel", [])).lower()
            href = tag.get("href", "")
            if "stylesheet" in rel and href:
                normalized = normalize_url(href, page_url)
                if normalized and not _is_internal(normalized, base_domain):
                    ext_css += 1

        media_internal = 0
        media_external = 0
        for tag in soup.find_all(["img", "video", "audio", "source", "iframe"], src=True):
            src = normalize_url(tag.get("src", ""), page_url)
            if not src:
                continue
            if _is_internal(src, base_domain):
                media_internal += 1
            else:
                media_external += 1
        media_total = media_internal + media_external

        login_form = int(any(
            form.find("input", {"type": re.compile("password", re.I)})
            for form in soup.find_all("form")
        ))

        submit_email = int(any(
            form.find("input", {"type": re.compile("email", re.I)})
            for form in soup.find_all("form")
        ))

        favicon_external = 0
        for tag in soup.find_all("link", rel=True):
            rel = " ".join(tag.get("rel", [])).lower()
            href = tag.get("href", "")
            if "icon" in rel and href:
                normalized = normalize_url(href, page_url)
                if normalized and not _is_internal(normalized, base_domain):
                    favicon_external = 1
                    break

        links_in_tags = sum(
            1
            for tag_name in ("link", "meta", "script", "img")
            for tag in soup.find_all(tag_name)
            if tag.get("href") or tag.get("src")
        )

        sfh = 0
        for form in soup.find_all("form"):
            action = normalize_url(form.get("action") or page_url, page_url) or page_url
            if not _is_internal(action, base_domain):
                sfh = 1
                break

        title = (soup.title.string or "").strip() if soup.title else ""
        page_text = soup.get_text(" ", strip=True).lower()
        domain_in_title = int(base_domain and base_domain in title.lower())
        domain_with_copyright = int(
            base_domain and base_domain in page_text and "copyright" in page_text
        )

        popup_window = int(bool(soup.find(attrs={"onclick": re.compile(r"window\.open", re.I)})))
        onmouseover = int(bool(soup.find(attrs={"onmouseover": True})))
        right_clic = int(bool(soup.find(attrs={"oncontextmenu": True})))

        safe_anchor = 0
        for anchor in anchors:
            href = (anchor.get("href") or "").strip().lower()
            text = anchor.get_text(" ", strip=True).lower()
            if href.startswith("#") or href in ("", "javascript:void(0)", "javascript:void(0);"):
                if text and not href.startswith("http"):
                    safe_anchor += 1

        features = {
            "nb_hyperlinks": hyperlinks,
            "ratio_intHyperlinks": _safe_ratio(internal, hyperlinks),
            "ratio_extHyperlinks": _safe_ratio(external, hyperlinks),
            "ratio_nullHyperlinks": _safe_ratio(null_links, hyperlinks),
            "nb_extCSS": ext_css,
            "ratio_intRedirection": 0.0,
            "ratio_extRedirection": 0.0,
            "ratio_intErrors": 0.0,
            "ratio_extErrors": 0.0,
            "login_form": login_form,
            "external_favicon": favicon_external,
            "links_in_tags": links_in_tags,
            "submit_email": submit_email,
            "ratio_intMedia": _safe_ratio(media_internal, media_total),
            "ratio_extMedia": _safe_ratio(media_external, media_total),
            "sfh": sfh,
            "iframe": len(soup.find_all("iframe")),
            "popup_window": popup_window,
            "safe_anchor": safe_anchor,
            "onmouseover": onmouseover,
            "right_clic": right_clic,
            "empty_title": int(not title),
            "domain_in_title": domain_in_title,
            "domain_with_copyright": domain_with_copyright,
        }
        return {name: float(features[name]) for name in self.feature_names}
