"""Phase 1 out-of-context refusal, beyond the keyword guardrail.

Layers (in the order applied by app/main.py):
1. Keyword guardrail (kept from v1, documented as a prototype layer):
   an explicit out-of-scope topic word list. It is NOT a production
   out-of-distribution detector.
2. Product-reference check (new, Phase 1): a cek_stok_harga answer is
   only meaningful for a shop product. If the predicted intent is
   cek_stok_harga but the question mentions no shop product (no
   "sepatu" and no dummy product-name token), refuse. This catches
   price questions about non-shop items that otherwise score high
   confidence from the word "harga" alone (measured in Phase 1: a
   flight-ticket price question reached classifier confidence 0.944
   in v1, because it mimics the "harga sepatu" training example).
3. Domain-coverage gate (new, Phase 1, data-driven): refuse when ALL
   of the following hold for a question with no product anchor:
   - vocabulary coverage <= 0.50: at most half of its preprocessed
     tokens appear in the in-scope TF-IDF vocabulary (classifier
     vocabulary plus retriever vocabulary, both trained on dummy
     data only);
   - RAG best score < 0.40: no dummy FAQ/product document matches
     strongly;
   - nearest-training-example cosine similarity < 0.60: no dummy
     intent example is close in TF-IDF space;
   - classifier confidence < 0.85.
   The product-anchor exception is deliberate and documented: a
   question that mentions "sepatu" (or a dummy product name) is in
   the shop's product domain, so it is not refused by this gate even
   when its coverage is low (for example a generic "Sepatu apa saja
   yang dijual di sini?" has coverage 0.33 in Phase 1 measurements
   but confidence 0.87 and a clear product anchor).
4. Low-evidence fallback (kept from v1): refuse when RAG best score
   < 0.10 AND classifier confidence < 0.35.

Thresholds are prototype values tuned on dummy data, not production
guarantees. Known remaining limitation, stated honestly in the
README: a question that mentions a shop product but is really about
something else, and a bare price question with no product named
("Berapa harganya?" with no product context), can still be
mis-routed or refused, because this service is stateless and has no
conversation history. This is still a prototype guardrail, NOT a
production out-of-distribution detector. TF-IDF RAG is NOT replaced
by a vector store in Phase 1; that decision is still open.
"""
from sklearn.metrics.pairwise import cosine_similarity

from .classifier import load_training_data
from .preprocessing import preprocess

PRODUCT_ANCHOR_TOKENS = {"sepatu", "sneakers", "kasual", "slip"}

# Since the Nike dummy catalogue update, a question that names a
# Nike model (for example "Berapa stok Nike Air Force 1?") must
# also count as a product anchor, even without the word "sepatu".
# Anchor tokens are therefore extended at runtime with distinctive
# tokens from data/dummy_products.csv. Only tokens with at least
# 4 letters are used, and the common word "air" is excluded, so a
# stray digit like "3" in an out-of-context question (for example
# "itinerary liburan ke Bali 3 hari") does not accidentally count
# as a product anchor.
import csv as _csv
import os as _os

_EXCLUDED_ANCHOR_TOKENS = {"contoh", "air"}

def _product_anchor_tokens():
    tokens = set(PRODUCT_ANCHOR_TOKENS)
    tokens.update({"nike", "running", "trail", "basketball", "training", "sandal", "clogs"})
    path = _os.path.join(
        _os.path.dirname(__file__), "..", "data", "dummy_products.csv"
    )
    try:
        with open(path, encoding="utf-8") as f:
            for row in _csv.DictReader(f):
                for tok in preprocess(row["product_name_dummy"]).split():
                    if len(tok) >= 4 and tok not in _EXCLUDED_ANCHOR_TOKENS:
                        tokens.add(tok)
    except OSError:
        pass
    return tokens

PRODUCT_ANCHOR_TOKENS = _product_anchor_tokens()

COVERAGE_THRESHOLD = 0.50
RAG_THRESHOLD = 0.40
NEAREST_TRAINING_THRESHOLD = 0.60
CONFIDENCE_THRESHOLD = 0.85
FALLBACK_RAG_THRESHOLD = 0.10
FALLBACK_CONFIDENCE_THRESHOLD = 0.35


class RefusalChecker:
    """Data-driven refusal signals, computed from dummy training data."""

    def __init__(self, model, retriever):
        self.model = model
        self.retriever = retriever
        texts, _labels = load_training_data()
        self.training_texts = texts
        tfidf = model.named_steps["tfidf"]
        self.training_matrix = tfidf.transform(texts)
        self.vocabulary = set(tfidf.vocabulary_.keys()) | set(
            retriever.vectorizer.vocabulary_.keys()
        )

    def token_coverage(self, cleaned: str) -> float:
        tokens = cleaned.split()
        if not tokens:
            return 0.0
        return sum(1 for t in tokens if t in self.vocabulary) / len(tokens)

    def nearest_training_similarity(self, cleaned: str) -> float:
        tfidf = self.model.named_steps["tfidf"]
        vec = tfidf.transform([cleaned])
        scores = cosine_similarity(vec, self.training_matrix)[0]
        return float(scores.max()) if len(scores) else 0.0

    def has_product_anchor(self, cleaned: str) -> bool:
        return bool(set(cleaned.split()) & PRODUCT_ANCHOR_TOKENS)

    def check(self, message: str, intent, confidence: float, rag_best: float):
        """Return (layer_or_None, metrics_dict).

        layer is one of "product_reference", "domain_coverage",
        "low_evidence_fallback", or None when the question is not
        refused by these data-driven layers (the keyword layer is
        checked separately in app/main.py, before this is called).
        """
        cleaned = preprocess(message)
        coverage = self.token_coverage(cleaned)
        nearest = self.nearest_training_similarity(cleaned)
        anchor = self.has_product_anchor(cleaned)
        metrics = {
            "coverage": round(coverage, 4),
            "nearest_training_similarity": round(nearest, 4),
            "rag_best_score": round(rag_best, 4),
            "classifier_confidence": round(confidence, 4),
            "has_product_anchor": anchor,
        }
        if intent == "cek_stok_harga" and not anchor:
            return "product_reference", metrics
        if (
            not anchor
            and coverage <= COVERAGE_THRESHOLD
            and rag_best < RAG_THRESHOLD
            and nearest < NEAREST_TRAINING_THRESHOLD
            and confidence < CONFIDENCE_THRESHOLD
        ):
            return "domain_coverage", metrics
        if (
            rag_best < FALLBACK_RAG_THRESHOLD
            and confidence < FALLBACK_CONFIDENCE_THRESHOLD
        ):
            return "low_evidence_fallback", metrics
        return None, metrics
