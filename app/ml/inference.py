"""Unified inference entrypoint with sklearn-first loading."""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path

from app.ml.phishing.pipeline import PhishingModel
from app.ml.risk_engine.scorer import RiskAssessment, compute_risk_assessment
from app.ml.spam.pipeline import SpamModel
from app.ml.url_features.extractor import URLFeatureExtractor
from app.ml.utils.url_normalize import registered_domain
from app.services.trusted_domains import get_trusted_domains
from app.services.blocked_domains import get_blocked_domains

logger = logging.getLogger(__name__)

SKLEARN_DIR = Path("models/sklearn")
USE_SKLEARN = SKLEARN_DIR.joinpath("spam_pipeline.joblib").exists() and SKLEARN_DIR.joinpath(
    "phishing_rf.joblib"
).exists()


@lru_cache(maxsize=1)
def _load_sklearn_models() -> tuple[SpamModel, PhishingModel]:
    return SpamModel.load(SKLEARN_DIR), PhishingModel.load(SKLEARN_DIR)


def _load_legacy_models():
    import pickle

    nb_model = pickle.load(open("models/nb_model.pkl", "rb"))
    vectorizer = pickle.load(open("models/vectorizer.pkl", "rb"))
    rf_model = pickle.load(open("models/rf_model.pkl", "rb"))
    return nb_model, vectorizer, rf_model


def safe_route(text: str) -> str:
    text = str(text).strip().lower()
    if re.search(r"(https?://|www\.|\.[a-z]{2,})", text) and " " not in text:
        return "URL 💀"
    return "TEXT 🧠"


def predict_text(text: str) -> tuple[str, float]:
    if USE_SKLEARN:
        spam_model, _ = _load_sklearn_models()
        return spam_model.predict_proba(text)
    nb_model, vectorizer, _ = _load_legacy_models()
    import numpy as np

    vec = vectorizer.transform([text])
    probs = nb_model.predict_proba(vec)[0]
    classes = np.array(getattr(nb_model, "classes_", getattr(nb_model, "classes", [])))
    spam_index = np.where(classes == 1)[0]
    spam_index = spam_index[0] if len(spam_index) > 0 else np.argmax(probs)
    label = "SPAM 🔥" if classes[np.argmax(probs)] == 1 else "HAM 😐"
    return label, float(probs[spam_index] * 100)


def classify_url(url: str) -> tuple[str, float, dict]:
    if USE_SKLEARN:
        extractor = URLFeatureExtractor()
        feature_summary = extractor.extract_dict(url)
        _, phishing_model = _load_sklearn_models()
        label, score = phishing_model.predict_proba(url)
        return label, score, feature_summary

    from feature_extractor import URLFeatureExtractor as LegacyURLFeatureExtractor

    extractor = LegacyURLFeatureExtractor()
    import numpy as np

    _, _, rf_model = _load_legacy_models()
    features = extractor.transform([url])
    probs = rf_model.predict_proba(features)[0]
    score = float(probs[1]) * 100
    label = "PHISHING 🔥" if score > 50 else "SAFE 😐"
    feature_summary = {f"feature_{i}": float(features[0][i]) for i in range(len(features[0]))}
    return label, score, feature_summary


def predict(input_data: str) -> dict:
    input_data = str(input_data).strip()
    if not input_data:
        return {"type": "INVALID", "label": "EMPTY INPUT", "confidence": 0.0}

    mode = safe_route(input_data)
    trusted = get_trusted_domains()
    blocked = get_blocked_domains()

    if mode == "TEXT 🧠":
        label, conf = predict_text(input_data)
        assessment = compute_risk_assessment(
            model_probability=conf,
            input_type="TEXT",
            label=label,
            trusted_domains=trusted,
            blocked_domains=blocked,
        )
        return _build_response("TEXT", label, conf, assessment)

    label, conf, feature_summary = classify_url(input_data)
    domain = ""
    try:
        from urllib.parse import urlparse

        from app.ml.utils.url_normalize import normalize_url

        normalized = normalize_url(input_data) or input_data
        domain = registered_domain(urlparse(normalized).hostname or "")
    except Exception:
        domain = ""
    assessment = compute_risk_assessment(
        model_probability=conf,
        input_type="URL",
        label=label,
        url_feature_summary=feature_summary,
        trusted_domains=trusted,
        blocked_domains=blocked,
        scanned_domain=domain,
    )
    return _build_response("URL", label, conf, assessment, feature_summary=feature_summary)


def _build_response(
    input_type: str,
    label: str,
    confidence: float,
    assessment: RiskAssessment,
    feature_summary: dict | None = None,
) -> dict:
    return {
        "type": input_type,
        "label": label,
        "confidence": confidence,
        "model_probability": assessment.model_probability,
        "risk_score": assessment.risk_score,
        "threat_level": assessment.threat_level,
        "reasons": assessment.reasons,
        "feature_summary": assessment.feature_summary if assessment.feature_summary else {"url": feature_summary or {}},
        "trusted_domain_signal": assessment.trusted_domain_signal,
    }
