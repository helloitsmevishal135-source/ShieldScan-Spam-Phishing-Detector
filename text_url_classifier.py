import numpy as np
import re

from decesion_tree import DecisionTree
from random_forest import RandomForest


class TextURLFeatureExtractor:
    def __init__(self):
        # catches full URLs
        self.full_url_pattern = re.compile(r"(https?://|www\.)[^\s]+")
        
        # catches domain-only URLs like youtube.com, facebook.com
        self.domain_pattern = re.compile(r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$")

    def normalize(self, x):
        return str(x).strip().lower()

    def looks_like_url(self, x):
        x = self.normalize(x)

        # full URL check
        if self.full_url_pattern.search(x):
            return 1

        # domain-only check
        if self.domain_pattern.match(x):
            return 1

        return 0

    def extract(self, X):
        features = []

        for x in X:
            x = self.normalize(x)

            is_url = self.looks_like_url(x)

            has_spaces = 1 if " " in x else 0
            no_spaces = 1 if " " not in x else 0
            space_ratio = x.count(" ") / max(len(x), 1)

            has_dots = x.count(".")
            has_slashes = x.count("/")
            has_digits = sum(c.isdigit() for c in x)

            length = len(x)
            word_count = len(x.split())

            has_tld = 1 if re.search(r"\.[a-z]{2,}$", x) else 0
            has_query = 1 if "?" in x or "=" in x else 0

            features.append([
                is_url,
                has_spaces,
                no_spaces,
                space_ratio,
                has_dots,
                has_slashes,
                has_digits,
                has_tld,
                has_query,
                length,
                word_count
            ])

        return np.array(features)


class TextURLClassifier:
    def __init__(self, n_trees=20, max_depth=6, seed=None):
        self.extractor = TextURLFeatureExtractor()

        self.model = RandomForest(
            n_trees=n_trees,
            max_depth=max_depth,
            seed=seed
        )

        self.is_fitted = False

    def fit(self, X, y):
        X_features = self.extractor.extract(X)
        self.model.fit(X_features, y)
        self.is_fitted = True

    def predict(self, X):
        if not self.is_fitted:
            raise Exception("Bro you didn't even train the model. What are you doing.")

        X_features = self.extractor.extract(X)
        preds = self.model.predict(X_features)

        return ["URL 💀" if p == 1 else "TEXT 🧠" for p in preds]

    def predict_one(self, x):
        return self.predict([x])[0]

    def confidence(self, X):
        X_features = self.extractor.extract(X)
        return self.model.confidence(X_features)