"""Production phishing URL detection using scikit-learn."""

from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from app.ml.url_features.extractor import URLFeatureExtractor

logger = logging.getLogger(__name__)

DEFAULT_ARTIFACT_DIR = Path("models/sklearn")


class PhishingModel:
    def __init__(self, model: RandomForestClassifier, extractor: URLFeatureExtractor | None = None):
        self.model = model
        self.extractor = extractor or URLFeatureExtractor()

    @classmethod
    def load(cls, artifact_dir: Path | str = DEFAULT_ARTIFACT_DIR) -> "PhishingModel":
        path = Path(artifact_dir) / "phishing_rf.joblib"
        if not path.exists():
            raise FileNotFoundError(f"Phishing model not found at {path}")
        return cls(joblib.load(path))

    def predict_proba(self, url: str) -> tuple[str, float]:
        features = self.extractor.extract(url).reshape(1, -1)
        probs = self.model.predict_proba(features)[0]
        classes = self.model.classes_
        phish_idx = int(np.where(classes == 1)[0][0]) if 1 in classes else int(np.argmax(probs))
        score = float(probs[phish_idx]) * 100.0
        label = "PHISHING 🔥" if score > 50 else "SAFE 😐"
        return label, score

    def feature_importances(self) -> dict[str, float]:
        if not hasattr(self.model, "feature_importances_"):
            return {}
        return {
            name: float(value)
            for name, value in zip(self.extractor.feature_names, self.model.feature_importances_)
        }
