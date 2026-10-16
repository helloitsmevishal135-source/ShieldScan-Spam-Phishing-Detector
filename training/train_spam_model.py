"""Train production spam model with scikit-learn."""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ml.spam.pipeline import build_spam_pipeline
from app.ml.spam.preprocess import preprocess_text
from training.metrics import evaluate_classifier, save_confusion_matrix_plot, save_training_artifacts


def load_spam_dataset(path: Path) -> tuple[list[str], list[int]]:
    df = pd.read_csv(path, encoding="latin-1")
    df = df[["v1", "v2"]].dropna()
    df = df.drop_duplicates(subset=["v2"])
    texts = df["v2"].astype(str).map(preprocess_text).tolist()
    labels = df["v1"].apply(lambda x: 1 if str(x).lower() == "spam" else 0).tolist()
    return texts, labels


def main() -> None:
    data_path = ROOT / "spam.csv"
    artifact_dir = ROOT / "models" / "sklearn"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    texts, labels = load_spam_dataset(data_path)
    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    pipeline = build_spam_pipeline()
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    metrics = evaluate_classifier(y_test, predictions)

    joblib.dump(pipeline, artifact_dir / "spam_pipeline.joblib")
    save_confusion_matrix_plot(
        metrics["confusion_matrix"],
        ["ham", "spam"],
        artifact_dir / "spam_confusion_matrix.png",
    )
    report = save_training_artifacts(
        model_name="spam_multinomial_nb",
        metrics=metrics,
        output_dir=artifact_dir,
        extra={"train_size": len(x_train), "test_size": len(x_test)},
    )

    print("Spam model trained.")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1 Score: {metrics['f1_score']:.4f}")
    print(f"Metrics saved to {report}")


if __name__ == "__main__":
    main()
