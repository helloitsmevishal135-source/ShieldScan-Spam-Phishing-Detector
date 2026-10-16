"""Spam text preprocessing for sklearn pipeline."""

from __future__ import annotations

import re
import string

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

_LEMMATIZER: WordNetLemmatizer | None = None
_STOPWORDS: set[str] | None = None


def _ensure_nltk_data() -> None:
    global _LEMMATIZER, _STOPWORDS
    if _LEMMATIZER is not None:
        return
    for resource, path in (
        ("stopwords", "corpora/stopwords"),
        ("wordnet", "corpora/wordnet"),
        ("omw-1.4", "corpora/omw-1.4"),
    ):
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(resource, quiet=True)
    _LEMMATIZER = WordNetLemmatizer()
    _STOPWORDS = set(stopwords.words("english"))


def preprocess_text(text: str) -> str:
    """Lowercase, remove punctuation, stopwords, and lemmatize."""
    _ensure_nltk_data()
    assert _LEMMATIZER is not None
    assert _STOPWORDS is not None

    value = str(text or "").lower()
    value = re.sub(r"https?://\S+|www\.\S+", " ", value)
    value = value.translate(str.maketrans("", "", string.punctuation))
    tokens = re.findall(r"\b[a-z0-9]+\b", value)
    cleaned = [
        _LEMMATIZER.lemmatize(token)
        for token in tokens
        if token not in _STOPWORDS and len(token) > 1
    ]
    return " ".join(cleaned)
