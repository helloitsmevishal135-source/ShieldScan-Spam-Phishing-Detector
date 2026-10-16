"""
Hybrid phishing/spam inference facade.

Production path prefers scikit-learn artifacts in models/sklearn/.
Falls back to legacy custom models in models/*.pkl for compatibility.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def predict(input_data: str) -> dict:
    from app.ml.inference import predict as _predict

    return _predict(input_data)


def safe_route(text: str) -> str:
    from app.ml.inference import safe_route as _safe_route

    return _safe_route(text)


def predict_text(text: str) -> tuple[str, float]:
    from app.ml.inference import predict_text as _predict_text

    return _predict_text(text)


def classify_url(url: str) -> tuple[str, float]:
    from app.ml.inference import classify_url as _classify_url

    label, score, _features = _classify_url(url)
    return label, score


def main() -> None:
    print("Hybrid phishing/spam detector")
    print("Type 'exit' to quit\n")
    while True:
        user_input = input("Enter text or URL: ")
        if user_input.lower() == "exit":
            break
        result = predict(user_input)
        print("\nRESULT:")
        print("Type:", result.get("type"))
        print("Label:", result.get("label"))
        print("Model probability:", result.get("model_probability", result.get("confidence")))
        print("Risk score:", result.get("risk_score"))
        print("Threat level:", result.get("threat_level"))
        if result.get("reasons"):
            print("Reasons:")
            for reason in result["reasons"]:
                print(" -", reason)
        print("-" * 40)


if __name__ == "__main__":
    import sys

    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    main()
