import pandas as pd
import numpy as np
import pickle

from random_forest import RandomForest
from feature_extractor import URLFeatureExtractor


# -------------------------
# LOAD DATA
# -------------------------
data = pd.read_csv("dataset_phishing.csv")

print("Loaded:", data.shape)


# -------------------------
# FEATURES + LABELS
# -------------------------
extractor = URLFeatureExtractor()

# CHANGE THIS COLUMN NAME IF NEEDED
X = extractor.transform(data["url"])

y = (data["status"] == "phishing").astype(int).values


print("Feature shape:", X.shape)


# -------------------------
# TRAIN
# -------------------------
rf = RandomForest(n_trees=10, max_depth=6, seed=42)
rf.fit(X, y)

print("Training complete")


# -------------------------
# SAVE
# -------------------------
with open("models/rf_model.pkl", "wb") as f:
    pickle.dump(rf, f)

print("Saved RF model")