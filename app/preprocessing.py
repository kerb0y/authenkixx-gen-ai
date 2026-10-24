"""Preprocessing for the prototype intent classifier and RAG retrieval.

All text here is Indonesian dummy text. No real UMKM data is used.
"""
import re

_STOPWORDS = {
    "yang", "dan", "di", "ke", "dari", "untuk", "dengan", "saya", "tolong",
    "dong", "ya", "kah", "apakah", "bagaimana", "berapa", "apa", "ini",
    "itu", "saja", "masih", "sudah", "belum", "satu", "dua",
}

_PUNCT = re.compile(r"[^a-z0-9\s]")


def preprocess(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace, drop stopwords.

    Raises ValueError on empty / non-string input so the API can return
    a clear 422-style validation error instead of crashing.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("message must be a non-empty string")
    text = text.lower()
    text = _PUNCT.sub(" ", text)
    tokens = [t for t in text.split() if t not in _STOPWORDS]
    cleaned = " ".join(tokens)
    if not cleaned:
        raise ValueError("message contains no usable words after preprocessing")
    return cleaned
