import pickle
import numpy as np

nb_model = pickle.load(open("models/nb_model.pkl", "rb"))
vectorizer = pickle.load(open("models/vectorizer.pkl", "rb"))


def predict(text):

    text = str(text).strip()

    vec = vectorizer.transform([text])

    probs = nb_model.predict_proba(vec)[0]

    spam_index = np.where(nb_model.classes == 1)[0][0]

    spam_prob = probs[spam_index] * 100

    pred = nb_model.classes[np.argmax(probs)]

    label = "SPAM 🔥" if pred == 1 else "HAM 😐"

    return label, spam_prob


if __name__ == "__main__":
    import sys

    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    test_texts = [
        "I will go to college tomorrow",
        "You won a free iPhone click now",
        "Urgent your account is suspended",
    ]

    for t in test_texts:
        label, prob = predict(t)
        print(t, "=>", label, f"({prob:.2f}%)")