"""Production spam detection using scikit-learn."""

from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

DEFAULT_ARTIFACT_DIR = Path("models/sklearn")


class SpamModel:
    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline

    @classmethod
    def load(cls, artifact_dir: Path | str = DEFAULT_ARTIFACT_DIR) -> "SpamModel":
        path = Path(artifact_dir) / "spam_pipeline.joblib"
        if not path.exists():
            raise FileNotFoundError(f"Spam model not found at {path}")
        return cls(joblib.load(path))

    def predict_proba(self, text: str) -> tuple[str, float]:
        probs = self.pipeline.predict_proba([text])[0]
        classes = self.pipeline.classes_
        spam_idx = int(np.where(classes == 1)[0][0]) if 1 in classes else int(np.argmax(probs))
        spam_prob = float(probs[spam_idx]) * 100.0
        label = "SPAM 🔥" if classes[np.argmax(probs)] == 1 else "HAM 😐"
        return label, spam_prob


def build_spam_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(max_features=20000, ngram_range=(1, 2), min_df=2)),
            ("clf", MultinomialNB(alpha=0.1)),
        ]
    )
