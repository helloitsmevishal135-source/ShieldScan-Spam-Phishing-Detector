import pandas as pd
import pickle
import numpy as np

from preprocessor import TextVectorizer
from naivebayes import MultinomialNaiveBayes
from sklearn.model_selection import train_test_split


def load_data(path):
    df = pd.read_csv(path, encoding="latin-1")
    df = df[['v1', 'v2']].dropna()

    texts = df['v2'].astype(str).tolist()
    labels = df['v1'].apply(lambda x: 1 if str(x).lower() == 'spam' else 0).values

    return texts, labels


def main():

    texts, labels = load_data("spam.csv")

    print("Loading data:", len(texts))

    X_train_text, X_test_text, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42
    )

    vectorizer = TextVectorizer()

    X_train = vectorizer.fit_transform(X_train_text)
    X_test = np.array([vectorizer.transform(t) for t in X_test_text])

    model = MultinomialNaiveBayes()
    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    acc = (preds == y_test).mean()
    print("Accuracy:", round(acc * 100, 2), "%")

    # 🔥 IMPORTANT: clean save
    with open("models/nb_model.pkl", "wb") as f:
        pickle.dump(model, f)

    with open("models/vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)

    print("Saved clean model.")


if __name__ == "__main__":
    main()