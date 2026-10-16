"""Train production phishing model with scikit-learn RandomForest."""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ml.url_features.extractor import LOCAL_URL_FEATURE_NAMES, URLFeatureExtractor
from training.metrics import evaluate_classifier, save_confusion_matrix_plot, save_training_artifacts


def load_phishing_dataset(path: Path) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(path)
    df = df.dropna(subset=["url", "status"])
    df = df.drop_duplicates(subset=["url"])

    # Always extract features with the same runtime extractor so train/infer match.
    extractor = URLFeatureExtractor()
    x = extractor.transform(df["url"].astype(str).tolist())
    y = (df["status"].astype(str).str.lower() == "phishing").astype(int).values
    return x, y


def main() -> None:
    data_path = ROOT / "dataset_phishing.csv"
    artifact_dir = ROOT / "models" / "sklearn"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    x, y = load_phishing_dataset(data_path)
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

    joblib.dump(model, artifact_dir / "phishing_rf.joblib")
    joblib.dump(LOCAL_URL_FEATURE_NAMES, artifact_dir / "phishing_feature_names.joblib")
    save_confusion_matrix_plot(
        metrics["confusion_matrix"],
        ["legitimate", "phishing"],
        artifact_dir / "phishing_confusion_matrix.png",
    )
    report = save_training_artifacts(
        model_name="phishing_random_forest",
        metrics=metrics,
        output_dir=artifact_dir,
        extra={
            "train_size": len(x_train),
            "test_size": len(x_test),
            "feature_count": len(LOCAL_URL_FEATURE_NAMES),
        },
    )

    print("Phishing model trained.")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1 Score: {metrics['f1_score']:.4f}")
    print(f"Metrics saved to {report}")


if __name__ == "__main__":
    main()
