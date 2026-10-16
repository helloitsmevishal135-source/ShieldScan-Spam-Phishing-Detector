import numpy as np


class MultinomialNaiveBayes:
    def __init__(self):
        self.class_priors = None
        self.feature_log_probs = None
        self.classes = None

    # =========================
    # TRAIN
    # =========================
    def fit(self, X, y):

        self.classes = np.unique(y)
        n_classes = len(self.classes)
        n_samples, n_features = X.shape

        self.class_priors = np.zeros(n_classes)
        self.feature_log_probs = np.zeros((n_classes, n_features))

        for i, c in enumerate(self.classes):
            X_c = X[y == c]

            self.class_priors[i] = X_c.shape[0] / n_samples

            word_counts = np.sum(X_c, axis=0)
            total = np.sum(word_counts)

            smoothed = (word_counts + 1) / (total + n_features)

            self.feature_log_probs[i] = np.log(smoothed)

        self.class_priors = np.log(self.class_priors)

    # =========================
    # PREDICT
    # =========================
    def predict(self, X):

        log_probs = []

        for i in range(len(self.classes)):
            prior = self.class_priors[i]
            likelihood = X @ self.feature_log_probs[i]
            log_probs.append(prior + likelihood)

        log_probs = np.vstack(log_probs).T

        return self.classes[np.argmax(log_probs, axis=1)]

    # =========================
    #  PROPER PROBABILITIES
    # =========================
    def predict_proba(self, X):

        log_probs = []

        for i in range(len(self.classes)):
            prior = self.class_priors[i]
            likelihood = X @ self.feature_log_probs[i]
            log_probs.append(prior + likelihood)

        log_probs = np.vstack(log_probs).T

        probs = np.exp(log_probs)

        probs = probs / np.sum(probs, axis=1, keepdims=True)

        return probs

    # =========================
    # SINGLE
    # =========================
    def predict_single(self, x):
        return self.predict(x.reshape(1, -1))[0]