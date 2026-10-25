# Gen AI Prototype (Authenkixx Capstone)

Prototype only. By Ade Bintang. All data is dummy. No real UMKM data,
no customer data, no passwords, no automatic platform sync.

## Phase 1 (2026-10-25): what changed

- Out-of-context refusal strengthened beyond the keyword guardrail
  (see the new section below). Test results on dummy data:
  24/24 out-of-context questions refused (10 v1 + 14 new Phase 1
  questions), 12/12 in-scope questions NOT refused, API smoke
  tests 4/4. New code: `app/refusal.py`; new tests:
  `tests/test_in_scope.py` and the expanded
  `tests/test_out_of_context.py`.
- `ChatResponse` now includes `refusal_layer` (null for answered
  questions; `keyword`, `product_reference`, `domain_coverage`,
  or `low_evidence_fallback` for refusals), so the demo can show
  which layer fired.
- TF-IDF RAG was NOT replaced with a vector store in Phase 1;
  that decision (TF-IDF vs ChromaDB/FAISS) is still open for
  Ade/the team.
- Phase 1 changes are local only and have NOT been pushed yet.

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
owner-decided data and update this table.

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

## Out-of-context refusal (Phase 1: strengthened, still a prototype)

The chatbot refuses questions outside the dummy shop context with a
polite message. Refusal now uses four layers, in order (see
`app/refusal.py` for the data-driven layers):

1. Keyword guardrail (v1, kept): an explicit out-of-scope topic
   keyword list in `app/main.py`. This is a prototype layer, not a
   production out-of-distribution detector.
2. Product-reference check (Phase 1, new): if the predicted intent
   is `cek_stok_harga` but the question names no shop product (no
   "sepatu" and no dummy product-name token), refuse. This catches
   price questions about non-shop items that otherwise score high
   confidence from the word "harga" alone. Measured in Phase 1:
   "Berapa harga tiket pesawat ke Singapura?" reached classifier
   confidence 0.944 in v1, because it mimics the "harga sepatu"
   training example, and is now refused by this layer.
3. Domain-coverage gate (Phase 1, new, data-driven): refuse when
   ALL of these hold for a question with no product anchor:
   vocabulary coverage <= 0.50 (at most half of its preprocessed
   tokens appear in the in-scope TF-IDF vocabulary, classifier
   vocabulary plus retriever vocabulary, both trained on dummy
   data only), RAG best score < 0.40, nearest-training-example
   cosine similarity < 0.60, and classifier confidence < 0.85.
   The product-anchor exception is deliberate: a question that
   mentions "sepatu" (or a dummy product name) is in the shop's
   product domain, so this gate does not refuse it even when its
   coverage is low (measured: "Sepatu apa saja yang dijual di
   sini?" has coverage 0.33 but confidence 0.87 and a clear
   product anchor, and is correctly answered).
4. Low-evidence fallback (v1, kept): refuse when RAG best score
   < 0.10 AND classifier confidence < 0.35.

Thresholds are prototype values tuned on dummy data, not
production guarantees. Remaining limitation, stated honestly: this
is still a prototype guardrail, NOT a production
out-of-distribution detector. A question that mentions a shop
product but is really about something else, and a bare price
question with no product named ("Berapa harganya?" with no product
context), can still be mis-routed or refused, because this service
is stateless and has no conversation history. Do not claim
production-grade OOD detection for this service.

Tested out-of-context questions (24/24 refused in Phase 1,
verified by running `tests/test_out_of_context.py`):

1. Siapa presiden Indonesia saat ini? -> refused
2. Bagaimana cara memasak rendang yang enak? -> refused
3. Berapa skor pertandingan sepak bola semalam? -> refused
4. Apa ramalan cuaca besok di Jakarta? -> refused
5. Jelaskan teori relativitas Einstein secara detail -> refused
6. Berapa harga saham perusahaan teknologi hari ini? -> refused
7. Ceritakan dongeng sebelum tidur untuk anak -> refused
8. Bagaimana cara mendaftar CPNS tahun ini? -> refused
9. Apa itu blockchain dan bagaimana cara investasi crypto? -> refused
10. Tolong buatkan skripsi saya dari awal sampai akhir -> refused (keyword)

Phase 1 set (14 new, none contains a v1 keyword; these are the
proof the data-driven layers add coverage):
11. Bagaimana cara mengurus paspor baru? -> refused (domain_coverage)
12. Berapa biaya kuliah semester ini di kampus? -> refused (domain_coverage)
13. Tolong jelaskan cara kerja mesin mobil diesel -> refused (domain_coverage)
14. Apa jadwal kereta api ke Bandung besok pagi? -> refused (domain_coverage)
15. Bagaimana cara daftar SIM online? -> refused (domain_coverage)
16. Berapa gaji rata-rata programmer di Jakarta? -> refused (domain_coverage)
17. Tolong buatkan itinerary liburan ke Bali 3 hari -> refused (domain_coverage)
18. Siapa pemenang lomba menyanyi tadi malam? -> refused (domain_coverage)
19. Bagaimana cara beternak ayam petelur di rumah? -> refused (domain_coverage)
20. Berapa harga tiket pesawat ke Singapura? -> refused (product_reference)
21. Jelaskan sejarah kerajaan Majapahit secara singkat -> refused (domain_coverage)
22. Apa manfaat olahraga lari pagi untuk jantung? -> refused (domain_coverage)
23. Bagaimana cara mengajukan KPR rumah pertama? -> refused (domain_coverage)
24. Berapa tarif parkir di mal Jakarta Selatan? -> refused (domain_coverage)

In-scope counter-tests (Phase 1, must NOT be refused, verified by
running `tests/test_in_scope.py`): 12/12 not refused. The questions
cover stock, price, product availability, ordering steps, and
complaints, all naming a shop product or a clear shop context
(for example "Berapa stok sepatu sneakers putih?",
"Bagaimana cara memesan sepatu sneakers hitam?", and "Sepatu saya
rusak setelah dipakai seminggu, bagaimana komplainnya?"). This
file exists to prove the stronger refusal did not simply refuse
everything.

## Invalid input and service failure handling

- Empty message: HTTP 422 with a clear message.
- Invalid JSON / wrong types: FastAPI/Pydantic validation errors.
- Generative service down or slow: fallback answer, clear status in
  `generative_ai` field, no crash.
- Backend proxy down: the Full-Stack backend returns HTTP 502 with a
  clear message (see fullstack README).

## Tests

```bash
python tests/test_out_of_context.py   # 24/24 refused (Phase 1, verified)
python tests/test_in_scope.py         # 12/12 not refused (Phase 1, verified)
python -c "from tests.test_api import *; ..."  # see test_api.py (4 smoke tests, verified)
```

Note: `tests/test_api.py` uses FastAPI TestClient, which needs the
`httpx` package listed in requirements.txt.

## Disclaimer

See CHECKLIST_STATUS.md in this repo. Phase 1 is not the final version. The final target is to match the Authenkixx use-case document and fulfil all Main Quest checklist items for Full-Stack, Gen AI, and Data Science. Phase 1 does not yet claim full checklist compliance.
