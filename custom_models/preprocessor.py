import re
import string
import numpy as np
from collections import Counter

class TextVectorizer:
    def __init__(self):
        self.vocab = {}

        self.url_pattern = re.compile(
            r'https?://(?:www\.)?\S+|www\.\S+'
        )

    # -----------------------
    # TOKENIZATION (FIXED)
    # -----------------------
    def tokenize(self, text):

        # 🔥 SAFE TYPE HANDLING (FIX)
        if text is None:
            return [], []

        text = str(text)

        if text.strip() == "":
            return [], []

        # Extract URLs
        urls = self.url_pattern.findall(text)

        # Remove URLs
        text = self.url_pattern.sub(' ', text)

        # Normalize
        text = text.lower()

        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))

        # Extract tokens
        tokens = re.findall(r'\b\w+\b', text)

        return tokens, urls

    # -----------------------
    # BUILD VOCAB
    # -----------------------
    def fit(self, texts):

        vocab_set = set()

        for text in texts:
            tokens, _ = self.tokenize(text)
            vocab_set.update(tokens)

        self.vocab = {
            word: idx for idx, word in enumerate(sorted(vocab_set))
        }

        print(f"Vocabulary size: {len(self.vocab)}")

    # -----------------------
    # TRANSFORM
    # -----------------------
    def transform(self, text):

        tokens, _ = self.tokenize(text)

        vector = np.zeros(len(self.vocab), dtype=int)
        counts = Counter(tokens)

        for token, count in counts.items():
            if token in self.vocab:
                vector[self.vocab[token]] = count

        return vector

    # -----------------------
    # FIT + TRANSFORM
    # -----------------------
    def fit_transform(self, texts):

        self.fit(texts)
        return np.array([self.transform(text) for text in texts])