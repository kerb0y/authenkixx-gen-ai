"""FastAPI serving for the prototype Gen AI service.

Run: uvicorn app.main:app --reload --port 8000
Docs: http://127.0.0.1:8000/docs (Swagger / OpenAPI, auto-generated)
All data is dummy. No real UMKM data, no customer data, no passwords.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.classifier import build_classifier, classify
from app.generative import (
    GenerativeServiceError,
    NotConfiguredError,
    call_generative,
    generative_configured,
)
from app.prompts import (
    INTENT_ROUTES,
    MANUAL_ORDER_REPLY,
    OUT_OF_CONTEXT_REPLY,
    OWNER_ROUTE_REPLY,
    build_prompt,
)
from app.rag import PrototypeRetriever
from app.preprocessing import preprocess

# Out-of-context rule (tuned on dummy data, documented in README):
# 1) Explicit out-of-scope topic guardrail (prototype keyword list, not
#    a production out-of-distribution detector).
# 2) Fallback: refuse when the question barely matches any dummy
#    document AND the classifier is not confident. Thresholds are
#    prototype values, not production guarantees.
OUT_OF_SCOPE_KEYWORDS = {
    "presiden", "politik", "cuaca", "sepak", "bola", "rendang", "masak",
    "resep", "dongeng", "cpns", "skripsi", "tesis", "relativitas",
    "einstein", "saham", "crypto", "blockchain", "investasi", "film",
    "musik", "lagu", "game", "anime", "selebriti", "gosip",
}
RAG_SIMILARITY_THRESHOLD = 0.10
CLASSIFIER_CONFIDENCE_THRESHOLD = 0.35

app = FastAPI(
    title="Authenkixx Prototype Gen AI Service",
    description=(
        "Prototype only. Intent classification + prototype TF-IDF retrieval "
        "over dummy FAQ/product documents. No real UMKM data, no automatic "
        "platform sync, no orders/payments/shipping/customer data."
    ),
    version="0.1.0-prototype",
)

_MODEL = build_classifier()
_RETRIEVER = PrototypeRetriever()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


class ChatResponse(BaseModel):
    intent: str | None
    intent_confidence: float | None
    route: str
    answer: str
    retrieved_docs: list[str]
    rag_best_score: float
    generative_ai: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "gen-ai-prototype",
        "generative_ai_configured": generative_configured(),
        "note": "Prototype only, dummy data only.",
    }


@app.post("/classify", response_model=ChatResponse)
def classify_only(payload: ChatRequest):
    return _answer(payload.message, generative=False)


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    return _answer(payload.message, generative=True)


def _answer(message: str, generative: bool) -> ChatResponse:
    try:
        cleaned = preprocess(message)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Explicit out-of-scope topic guardrail, checked first.
    if set(cleaned.split()) & OUT_OF_SCOPE_KEYWORDS:
        return ChatResponse(
            intent=None,
            intent_confidence=None,
            route="refused_out_of_context",
            answer=OUT_OF_CONTEXT_REPLY,
            retrieved_docs=[],
            rag_best_score=0.0,
            generative_ai="not_used_refused",
        )

    intent, confidence = classify(_MODEL, message)
    retrieved = _RETRIEVER.retrieve(message, top_k=2)
    best_score = retrieved[0][1] if retrieved else 0.0
    docs = [doc for doc, _ in retrieved if _ >= 0.05]

    # Out-of-context refusal.
    if best_score < RAG_SIMILARITY_THRESHOLD and confidence < CLASSIFIER_CONFIDENCE_THRESHOLD:
        return ChatResponse(
            intent=None,
            intent_confidence=round(confidence, 4),
            route="refused_out_of_context",
            answer=OUT_OF_CONTEXT_REPLY,
            retrieved_docs=[],
            rag_best_score=round(best_score, 4),
            generative_ai="not_used_refused",
        )

    route = INTENT_ROUTES.get(intent, "rag")
    if route == "owner":
        answer, gen_status = OWNER_ROUTE_REPLY, "not_used_routed_to_owner"
    elif route == "manual_order":
        answer, gen_status = MANUAL_ORDER_REPLY, "not_used_manual_order"
    else:
        answer = (
            docs[0]
            if docs
            else "Data contoh yang relevan tidak ditemukan. "
            "Silakan tanyakan soal produk contoh, stok contoh, atau harga contoh."
        )
        gen_status = "not_used_rag_answer"
        if generative:
            try:
                gen_answer = call_generative(build_prompt(message, docs))
                answer, gen_status = gen_answer, "used"
            except NotConfiguredError:
                gen_status = "disabled_no_api_key"
            except GenerativeServiceError:
                gen_status = "failed_fell_back_to_rag"

    return ChatResponse(
        intent=intent,
        intent_confidence=round(confidence, 4),
        route=route,
        answer=answer,
        retrieved_docs=docs,
        rag_best_score=round(best_score, 4),
        generative_ai=gen_status,
    )
