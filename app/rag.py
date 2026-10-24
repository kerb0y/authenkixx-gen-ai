"""Prototype RAG-style retrieval over dummy FAQ/product documents.

This is TF-IDF cosine retrieval over the labelled dummy CSV files in
data/. It is NOT a ChromaDB / FAISS / Pinecone / Weaviate vector
database and NOT a real proprietary integration. A production RAG with
an embedding model and a vector store is listed as tomorrow's work.
"""
import csv
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .preprocessing import preprocess

_BASE = os.path.join(os.path.dirname(__file__), "..", "data")


def load_documents():
    docs = []
    with open(os.path.join(_BASE, "dummy_faq.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            docs.append(f"{row['question']} {row['answer']}")
    with open(os.path.join(_BASE, "dummy_products.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            docs.append(
                f"{row['product_name_dummy']} harga contoh "
                f"{row['price_dummy_idr']} stok contoh {row['stock_dummy']} "
                f"ketersediaan {row['availability_dummy']} kanal "
                f"{row['channels_dummy']}"
            )
    return docs


class PrototypeRetriever:
    def __init__(self):
        self.docs = load_documents()
        cleaned = [preprocess(d) for d in self.docs]
        self.vectorizer = TfidfVectorizer()
        self.matrix = self.vectorizer.fit_transform(cleaned)

    def retrieve(self, query: str, top_k: int = 2):
        """Return [(doc, score)] sorted by cosine similarity."""
        cleaned = preprocess(query)
        vec = self.vectorizer.transform([cleaned])
        scores = cosine_similarity(vec, self.matrix)[0]
        order = scores.argsort()[::-1][:top_k]
        return [(self.docs[int(i)], float(scores[int(i)])) for i in order]

    def best_score(self, query: str) -> float:
        results = self.retrieve(query, top_k=1)
        return results[0][1] if results else 0.0
