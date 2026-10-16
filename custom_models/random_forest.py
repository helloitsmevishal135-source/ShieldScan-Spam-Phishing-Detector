import numpy as np
from custom_models.decesion_tree import DecisionTree


class RandomForest:

    def __init__(self, n_trees=10, max_depth=5, min_samples=2, seed=None):

        self.n_trees = n_trees
        self.max_depth = max_depth
        self.min_samples = min_samples
        self.seed = seed

        self.trees = []
        self.classes_ = None
        self.n_classes_ = None

        if seed is not None:
            np.random.seed(seed)

  
    def fit(self, X, y):

        X = np.array(X)
        y = np.array(y)

        self.classes_ = np.unique(y)
        self.n_classes_ = len(self.classes_)

        n_features = X.shape[1]
        feature_subset = max(1, int(np.sqrt(n_features)))

        self.trees = []

        for _ in range(self.n_trees):

            idx = np.random.choice(len(X), len(X), replace=True)

            X_s, y_s = X[idx], y[idx]

            tree = DecisionTree(
                max_depth=self.max_depth,
                min_samples=self.min_samples,
                n_features=feature_subset
            )

            tree.fit(X_s, y_s)
            self.trees.append(tree)

 
    def predict_proba(self, X):

        X = np.array(X)

        tree_preds = np.array([t.predict(X) for t in self.trees])
        n_samples = X.shape[0]

        probs = np.zeros((n_samples, self.n_classes_))

        for i in range(n_samples):
            votes = tree_preds[:, i]

            for j, cls in enumerate(self.classes_):
                probs[i, j] = np.sum(votes == cls)

            probs[i] /= self.n_trees

        return probs


    def predict(self, X):

        probs = self.predict_proba(X)
        return self.classes_[np.argmax(probs, axis=1)]