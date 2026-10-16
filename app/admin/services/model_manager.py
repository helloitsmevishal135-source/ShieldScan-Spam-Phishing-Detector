"""Model training, versioning, and deployment for admin panel — MongoDB version."""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from app.config import BASE_DIR
from app.ml.spam.pipeline import build_spam_pipeline
from app.ml.spam.preprocess import preprocess_text
from app.ml.url_features.extractor import LOCAL_URL_FEATURE_NAMES, URLFeatureExtractor
from app.models import ModelVersion, TrainingLog
try:
    from training.metrics import evaluate_classifier, save_confusion_matrix_plot, save_training_artifacts
except ImportError:
    evaluate_classifier = None
    save_confusion_matrix_plot = None
    save_training_artifacts = None

logger = logging.getLogger(__name__)

ARTIFACT_DIR = Path(BASE_DIR) / "models" / "sklearn"
VERSIONS_DIR = Path(BASE_DIR) / "models" / "versions"
UPLOAD_DIR = Path(BASE_DIR) / "data" / "uploads"


def _version_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _register_model_version(
    *,
    model_name: str,
    version: str,
    artifact_path: str,
    metrics: dict,
    activate: bool = True,
) -> ModelVersion:
    if activate:
        # Deactivate all existing active versions for this model
        for mv in ModelVersion.objects(model_name=model_name, is_active=True):
            mv.is_active = False
            mv.save()

    row = ModelVersion(
        model_name=model_name,
        version=version,
        artifact_path=artifact_path,
        metrics_json=json.dumps(metrics),
        is_active=activate,
    )
    row.save()
    return row


def _register_training_log(
    *,
    model_name: str,
    version: str,
    metrics: dict,
    artifact_path: str,
    trained_by: str | None,
) -> TrainingLog:
    row = TrainingLog(
        model_name=model_name,
        version=version,
        metrics_json=json.dumps(metrics),
        artifact_path=artifact_path,
        trained_by=trained_by,
    )
    row.save()
    return row


def train_spam_model(dataset_path: Path | None = None, *, trained_by: str | None = None) -> dict:
    data_path = dataset_path or Path(BASE_DIR) / "spam.csv"
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path, encoding="latin-1")
    df = df[["v1", "v2"]].dropna().drop_duplicates(subset=["v2"])
    texts = df["v2"].astype(str).map(preprocess_text).tolist()
    labels = df["v1"].apply(lambda x: 1 if str(x).lower() == "spam" else 0).tolist()

    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    pipeline = build_spam_pipeline()
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    metrics = evaluate_classifier(y_test, predictions)

    version = _version_tag()
    version_dir = VERSIONS_DIR / "spam" / version
    version_dir.mkdir(parents=True, exist_ok=True)
    version_artifact = version_dir / "spam_pipeline.joblib"
    joblib.dump(pipeline, version_artifact)
    joblib.dump(pipeline, ARTIFACT_DIR / "spam_pipeline.joblib")

    save_confusion_matrix_plot(
        metrics["confusion_matrix"],
        ["ham", "spam"],
        version_dir / "confusion_matrix.png",
    )
    save_training_artifacts(
        model_name="spam_multinomial_nb",
        metrics=metrics,
        output_dir=version_dir,
        extra={"train_size": len(x_train), "test_size": len(x_test)},
    )

    _register_training_log(
        model_name="spam_multinomial_nb",
        version=version,
        metrics=metrics,
        artifact_path=str(version_artifact),
        trained_by=trained_by,
    )
    _register_model_version(
        model_name="spam_multinomial_nb",
        version=version,
        artifact_path=str(version_artifact),
        metrics=metrics,
    )

    from app.ml.inference import _load_sklearn_models
    _load_sklearn_models.cache_clear()

    return {"model_name": "spam_multinomial_nb", "version": version, "metrics": metrics}


def train_phishing_model(dataset_path: Path | None = None, *, trained_by: str | None = None) -> dict:
    data_path = dataset_path or Path(BASE_DIR) / "dataset_phishing.csv"
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path)
    df = df.dropna(subset=["url", "status"]).drop_duplicates(subset=["url"])

    extractor = URLFeatureExtractor()
    x = extractor.transform(df["url"].astype(str).tolist())

    y = (df["status"].astype(str).str.lower() == "phishing").astype(int).values
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    metrics = evaluate_classifier(y_test, predictions)

    version = _version_tag()
    version_dir = VERSIONS_DIR / "phishing" / version
    version_dir.mkdir(parents=True, exist_ok=True)
    version_artifact = version_dir / "phishing_rf.joblib"
    joblib.dump(model, version_artifact)
    joblib.dump(model, ARTIFACT_DIR / "phishing_rf.joblib")
    joblib.dump(LOCAL_URL_FEATURE_NAMES, ARTIFACT_DIR / "phishing_feature_names.joblib")

    save_confusion_matrix_plot(
        metrics["confusion_matrix"],
        ["legitimate", "phishing"],
        version_dir / "confusion_matrix.png",
    )
    save_training_artifacts(
        model_name="phishing_random_forest",
        metrics=metrics,
        output_dir=version_dir,
        extra={
            "train_size": len(x_train),
            "test_size": len(x_test),
            "feature_count": len(LOCAL_URL_FEATURE_NAMES),
        },
    )

    _register_training_log(
        model_name="phishing_random_forest",
        version=version,
        metrics=metrics,
        artifact_path=str(version_artifact),
        trained_by=trained_by,
    )
    _register_model_version(
        model_name="phishing_random_forest",
        version=version,
        artifact_path=str(version_artifact),
        metrics=metrics,
    )

    from app.ml.inference import _load_sklearn_models
    _load_sklearn_models.cache_clear()

    return {"model_name": "phishing_random_forest", "version": version, "metrics": metrics}


def save_uploaded_dataset(file_storage, dataset_type: str) -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    if dataset_type == "spam":
        dest = UPLOAD_DIR / "spam.csv"
        root_copy = Path(BASE_DIR) / "spam.csv"
    elif dataset_type == "phishing":
        dest = UPLOAD_DIR / "dataset_phishing.csv"
        root_copy = Path(BASE_DIR) / "dataset_phishing.csv"
    else:
        raise ValueError("Unknown dataset type.")

    file_storage.save(dest)
    shutil.copy(dest, root_copy)
    return dest


def deploy_model_version(version_id: str) -> ModelVersion:
    from flask import abort
    try:
        row = ModelVersion.objects(pk=version_id).first()
    except Exception:
        row = None
    if not row:
        abort(404)

    source = Path(row.artifact_path)
    if not source.exists():
        raise FileNotFoundError(f"Artifact not found: {source}")

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    if row.model_name == "spam_multinomial_nb":
        shutil.copy(source, ARTIFACT_DIR / "spam_pipeline.joblib")
    elif row.model_name == "phishing_random_forest":
        shutil.copy(source, ARTIFACT_DIR / "phishing_rf.joblib")
    else:
        raise ValueError(f"Unsupported model: {row.model_name}")

    # Deactivate other active versions
    for mv in ModelVersion.objects(model_name=row.model_name, is_active=True):
        mv.is_active = False
        mv.save()
    row.is_active = True
    row.save()

    from app.ml.inference import _load_sklearn_models
    _load_sklearn_models.cache_clear()
    return row


def get_phishing_feature_importance() -> dict[str, float]:
    path = ARTIFACT_DIR / "phishing_rf.joblib"
    if not path.exists():
        return {}
    model = joblib.load(path)
    if not hasattr(model, "feature_importances_"):
        return {}
    return {
        name: float(value)
        for name, value in zip(LOCAL_URL_FEATURE_NAMES, model.feature_importances_)
    }
