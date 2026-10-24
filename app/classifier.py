"""Intent classifier trained at startup on dummy labelled data only.

Intents (4): tanya_produk, pemesanan, keluhan, cek_stok_harga.
Model: TF-IDF + LogisticRegression (class_weight='balanced' as a
safeguard; the dummy set itself is balanced, see train_compare.py).
The classifier only routes a question; it never processes an order,
a payment, a shipment, or customer data.
"""
import csv
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .preprocessing import preprocess

_DATA = os.path.join(os.path.dirname(__file__), "..", "data", "dummy_intents.csv")


def load_training_data(path: str = _DATA):
    texts, labels = [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            texts.append(preprocess(row["text"]))
            labels.append(row["intent"])
    return texts, labels


def build_classifier() -> Pipeline:
    texts, labels = load_training_data()
    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer()),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000, class_weight="balanced", C=10.0
                ),
            ),
        ]
    )
    model.fit(texts, labels)
    return model


def classify(model: Pipeline, message: str):
    """Return (intent, confidence). Confidence is the max class proba."""
    cleaned = preprocess(message)
    proba = model.predict_proba([cleaned])[0]
    idx = int(proba.argmax())
    return str(model.classes_[idx]), float(proba[idx])
