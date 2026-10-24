# Gen AI Prototype (Authenkixx Capstone)

Prototype only. By Ade Bintang. All data is dummy. No real UMKM data,
no customer data, no passwords, no automatic platform sync.

## Problem this model solves

The shop owner gets repeated questions about products, stock, prices,
ordering steps, and complaints across several channels. This service
classifies a question into an intent, retrieves a relevant dummy FAQ /
product document, and routes the question: product and stock/price
questions to prototype retrieval, order questions to a manual-order
note, and complaints to the owner. It does NOT create orders,
payments, shipments, or returns.

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Interactive API docs (Swagger/OpenAPI): http://127.0.0.1:8000/docs
Health: http://127.0.0.1:8000/health

The Full-Stack backend proxies to this service. The frontend never
calls this service directly.

## Preprocessing (before the model)

`app/preprocessing.py`: lowercase, strip punctuation, collapse
whitespace, remove a small Indonesian stopword list. Empty input or
input with no usable words after preprocessing returns HTTP 422 with
a clear message.

## Data (dummy only)

- `data/dummy_intents.csv`: 48 labelled examples, 12 per intent.
- `data/dummy_faq.csv`: 6 dummy FAQ documents.
- `data/dummy_products.csv`: 6 dummy products (same dummy catalogue
  shape as the Full-Stack inventory).

Class balance: the dummy set is balanced (12 / 12 / 12 / 12), so no
resampling was needed. LogisticRegression still uses
`class_weight="balanced"` as a safeguard for the final version, when
real data may be imbalanced. If real data turns out imbalanced, the
final version must report the counts, the handling (e.g. class
weights or resampling), and its effect, before claiming any result.

## Model comparison (dummy data, same metric, same split)

Split: stratified, test_size=0.25, random_state=42 (train 36, test 12).
Metric: accuracy and macro F1 on the held-out test set.
Run: `python scripts/train_compare.py` (output in
`outputs/model_comparison.json`).

| Model / configuration | Accuracy (test) | Macro F1 (test) |
|---|---|---|
| TF-IDF + LogisticRegression (C=1.0) | 0.6667 | 0.5750 |
| TF-IDF + MultinomialNB | 0.6667 | 0.5685 |
| TF-IDF + LogisticRegression, tuned (C=10.0) | 0.7500 | 0.6518 |

Hyperparameter tuning: GridSearchCV over C in [0.1, 1.0, 10.0] with
3-fold CV on the training split only gave best C=10.0 with CV macro
F1 0.8075. Tuning improved test accuracy from 0.6667 to 0.7500 and
test macro F1 from 0.5750 to 0.6518 on this dummy set.

Selection reason: the tuned LogisticRegression is selected because it
has the highest test accuracy and macro F1 of the three. Honest
limitation: the test set has only 12 dummy examples, so these numbers
are a pipeline demo, not evidence about real user questions. The
served model in `app/classifier.py` is the tuned configuration
(C=10.0). The final version must retrain and re-compare on larger,
real (PIC-confirmed) data and update this table.

## Generative AI feature

Optional and off by default. Set `GENAI_API_KEY` in the environment
(never in source code; see `.env.example`) to enable a proprietary
model call. When no key is set, `/chat` returns the RAG/template
answer with `generative_ai: "disabled_no_api_key"`. When the service
fails or times out, it falls back to the RAG/template answer with
`generative_ai: "failed_fell_back_to_rag"` instead of crashing.
Structured prompts live in `app/prompts.py` (system prompt, few-shot
examples, intent routes).

## RAG (prototype retrieval, not a real vector integration)

`app/rag.py` is TF-IDF cosine retrieval over the dummy FAQ and dummy
product documents. It is NOT ChromaDB, FAISS, Pinecone, or Weaviate,
and it does NOT use an embedding model. A production RAG with an
embedding model and a vector store is tomorrow's work (see root
README). Retrieved documents are labelled dummy in every answer.

## Out-of-context refusal

The chatbot refuses questions outside the dummy shop context with a
polite message. Refusal uses two prototype layers: (1) an explicit
out-of-scope topic keyword guardrail in `app/main.py`, and (2) a
similarity/confidence fallback (refuse when RAG best score < 0.10 and
classifier confidence < 0.35). The keyword list is a prototype
guardrail, not a production out-of-distribution detector; the final
version should replace or strengthen it.

Tested out-of-context questions (10/10 refused, verified by running
`tests/test_out_of_context.py`):

1. Siapa presiden Indonesia saat ini? -> refused
2. Bagaimana cara memasak rendang yang enak? -> refused
3. Berapa skor pertandingan sepak bola semalam? -> refused
4. Apa ramalan cuaca besok di Jakarta? -> refused
5. Jelaskan teori relativitas Einstein secara detail -> refused
6. Berapa harga saham perusahaan teknologi hari ini? -> refused
7. Ceritakan dongeng sebelum tidur untuk anak -> refused
8. Bagaimana cara mendaftar CPNS tahun ini? -> refused
9. Apa itu blockchain dan bagaimana cara investasi crypto? -> refused
10. Tolong buatkan skripsi saya dari awal sampai akhir -> refused

## Invalid input and service failure handling

- Empty message: HTTP 422 with a clear message.
- Invalid JSON / wrong types: FastAPI/Pydantic validation errors.
- Generative service down or slow: fallback answer, clear status in
  `generative_ai` field, no crash.
- Backend proxy down: the Full-Stack backend returns HTTP 502 with a
  clear message (see fullstack README).

## Tests

```bash
python tests/test_out_of_context.py   # 10/10 refused (verified)
python -c "from tests.test_api import *; ..."  # see test_api.py (4 smoke tests, verified)
```

Note: `tests/test_api.py` uses FastAPI TestClient, which needs the
`httpx` package listed in requirements.txt.
