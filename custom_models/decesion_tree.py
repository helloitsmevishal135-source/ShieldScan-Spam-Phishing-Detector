import numpy as np

class DecisionTree:

    def __init__(self, max_depth=5, min_samples=2, n_features=None):
        self.max_depth = max_depth
        self.min_samples = min_samples
        self.n_features = n_features
        self.tree = None

    def fit(self, X, y):
        self.n_features = X.shape[1] if not self.n_features else self.n_features
        self.tree = self._grow_tree(X, y, depth=0)

    def predict(self, X):
        return np.array([self._traverse_tree(x, self.tree) for x in X])

    # -------------------------
    # Build tree
    # -------------------------

    def _grow_tree(self, X, y, depth):

        # 🔥 FIX 1: empty safety
        if len(y) == 0:
            return 0

        n_samples, n_features = X.shape

        # stopping conditions
        if (depth >= self.max_depth or
            len(set(y)) == 1 or
            n_samples < self.min_samples):

            return self._most_common_label(y)

        # random feature selection
        feat_count = min(self.n_features, n_features)
        feat_idxs = np.random.choice(n_features, feat_count, replace=False)

        best_feat, best_thresh = self._best_split(X, y, feat_idxs)

        if best_feat is None:
            return self._most_common_label(y)

        left_idxs = X[:, best_feat] <= best_thresh
        right_idxs = X[:, best_feat] > best_thresh

        # 🔥 FIX 2: prevent empty splits crash
        if np.sum(left_idxs) == 0 or np.sum(right_idxs) == 0:
            return self._most_common_label(y)

        left = self._grow_tree(X[left_idxs], y[left_idxs], depth + 1)
        right = self._grow_tree(X[right_idxs], y[right_idxs], depth + 1)

        return {
            "feature": best_feat,
            "threshold": best_thresh,
            "left": left,
            "right": right
        }

    # -------------------------
    # Find best split
    # -------------------------

    def _best_split(self, X, y, feat_idxs):

        best_gain = -1
        split_idx, split_thresh = None, None

        for feat_idx in feat_idxs:
            thresholds = np.unique(X[:, feat_idx])

            for thr in thresholds:
                gain = self._information_gain(y, X[:, feat_idx], thr)

                if gain > best_gain:
                    best_gain = gain
                    split_idx = feat_idx
                    split_thresh = thr

        return split_idx, split_thresh

    def _information_gain(self, y, feature, threshold):

        parent_entropy = self._entropy(y)

        left_idxs = feature <= threshold
        right_idxs = feature > threshold

        # 🔥 FIX 3: safe empty check
        if np.sum(left_idxs) == 0 or np.sum(right_idxs) == 0:
            return 0

        n = len(y)
        n_l, n_r = np.sum(left_idxs), np.sum(right_idxs)

        e_l = self._entropy(y[left_idxs])
        e_r = self._entropy(y[right_idxs])

        child_entropy = (n_l / n) * e_l + (n_r / n) * e_r

        return parent_entropy - child_entropy

    def _entropy(self, y):
        if len(y) == 0:
            return 0

        hist = np.bincount(y)
        probs = hist / len(y)

        return -np.sum([p * np.log2(p) for p in probs if p > 0])

    def _most_common_label(self, y):
        # 🔥 FIX 4: safe fallback
        if len(y) == 0:
            return 0
        return np.bincount(y.astype(int)).argmax()

    # -------------------------
    # Traverse tree
    # -------------------------

    def _traverse_tree(self, x, node):

        if not isinstance(node, dict):
            return node

        if x[node["feature"]] <= node["threshold"]:
            return self._traverse_tree(x, node["left"])
        else:
            return self._traverse_tree(x, node["right"])