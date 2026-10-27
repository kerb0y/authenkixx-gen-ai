# Shared API Contract (Prototype)

Agreed across Full-Stack, Gen AI, and Data Science repos. Prototype
only, dummy data only. Version: Phase 1, 2026-10-25 (v1 was
2026-10-24; Phase 1 changes are local only and have not been pushed
yet; the main agent pushes after verification).

## General rules

- All responses from the Full-Stack backend use:
  - Success: `{ "status": "success", "data": ... }`
  - Error: `{ "status": "error", "message": "..." }`
- Gen AI service responses use its own ChatResponse shape below, and
  the backend wraps it in the success envelope.
- Error codes:
  - 400: invalid input (Joi validation in backend, Pydantic in Gen AI)
  - 404: product or route not found
  - 422: Gen AI message empty after preprocessing
  - 502: Gen AI service unavailable or returned an error (backend proxy)
  - 500: internal server error
- No endpoint accepts or returns: customer names, customer contacts,
  passwords, payment data, shipping data, or real UMKM data. All
  prototype values are labelled `dummy`.

## Full-Stack Backend (Express, port 3001)

Base URL: `/api/v1/`

| Method | Endpoint | Request | Response `data` |
|---|---|---|---|
| GET | `/health` | - | `{ service }` |
| GET | `/products?search=&availability=&channel=` | query params (optional) | Product list |
| GET | `/products/:id` | - | One product |
| POST | `/products` | `{ name, price, stock, availability, channels[] }` | Created product (201) |
| PUT | `/products/:id` | Any subset of product fields (min 1) | Updated product |
| DELETE | `/products/:id` | - | Deleted product |
| GET | `/movements?product_id=` | query param (optional) | Stock movement list |
| POST | `/products/:id/stock` | `{ type: "in" \| "out", quantity: int >= 1, note?: string }` | `{ product, movement }` (201) |
| GET | `/insights` | - | `{ total_products, total_stock, low_stock_count, low_stock_products[], by_availability, data_label: "dummy", data_science, data_science_note }` (Phase 1: see Insights shape below) |
| POST | `/ai/chat` | `{ message: string (1-500 chars) }` | Gen AI ChatResponse, wrapped, plus `history_id` |
| GET | `/ai/history` | - | Chat history entries `{ message, intent, route, answer, created_at }` |

Product shape:
```json
{
  "id": "NK-DUMMY-001",
  "name": "Nike Air Force 1 '07 (Contoh)",
  "price": 1401000,
  "stock": 25,
  "availability": "tersedia",
  "channels": ["Facebook", "Instagram"],
  "data_label": "dummy"
}
```
`availability` is one of `tersedia`, `menipis`, `habis`. On stock
updates the backend recomputes it: stock 0 = `habis`, stock <= 5 =
`menipis`, otherwise `tersedia`. `channels` are labels only; there is
NO automatic synchronisation with any platform.

## Insights shape (Phase 1)

`GET /api/v1/insights` now includes a Data Science section, read
from files (not a live Data Science API):

- Source files: `data-science/outputs/business_summary.json` and
  `data-science/outputs/baseline_model.json`.
- Directory: configurable via the `DS_OUTPUTS_DIR` environment
  variable. Default: `../../data-science/outputs` relative to
  `fullstack/backend` (i.e. the prototype root's
  `data-science/outputs` folder).
- When the files are present:
  ```json
  {
    "data_science": {
      "business_summary": { "data_label": "dummy", "rows": 86400, "total_units_sold_dummy": 82526, "total_revenue_dummy_idr": 186375340000, "units_by_channel_dummy": {}, "units_by_product_dummy": {}, "low_stock_rows_dummy": 21600, "final_stock_dummy": {} },
      "baseline_model": { "data_label": "dummy", "accuracy": 0.75, "macro_f1": 0.4286, "train_rows": 96, "test_rows": 24 },
      "source_dir": "<DS outputs directory>",
      "data_label": "dummy"
    },
    "data_science_note": "Data Science outputs loaded from DS_OUTPUTS_DIR; all figures are dummy data."
  }
  ```
- When either file is missing or unreadable, the endpoint NEVER
  crashes. It returns the inventory-only insights with
  `"data_science": null` plus a clear `data_science_note` naming the
  directory that was tried.
- The frontend business summary page displays the Data Science
  totals, units by channel, low-stock summary, and baseline model
  metrics from this section, all labelled dummy. When
  `data_science` is null it shows the note instead.

## Gen AI Service (FastAPI, port 8000)

Base URL: `http://127.0.0.1:8000` (backend only; frontend never calls
this directly). Interactive docs: `/docs` (Swagger/OpenAPI).

| Method | Endpoint | Request | Response |
|---|---|---|---|
| GET | `/health` | - | `{ status, service, generative_ai_configured, note }` |
| POST | `/chat` | `{ message: string }` | ChatResponse |
| POST | `/classify` | `{ message: string }` | ChatResponse (generative step skipped) |

ChatResponse:
```json
{
  "intent": "tanya_produk",
  "intent_confidence": 0.51,
  "route": "rag",
  "answer": "...",
  "retrieved_docs": ["..."],
  "rag_best_score": 0.44,
  "generative_ai": "disabled_no_api_key"
}
```
- `intent`: one of `tanya_produk`, `pemesanan`, `keluhan`,
  `cek_stok_harga`, or `null` when refused.
- `route`: `rag`, `manual_order`, `owner`, or
  `refused_out_of_context`.
- `generative_ai`: `used`, `disabled_no_api_key`,
  `failed_fell_back_to_rag`, `not_used_rag_answer`,
  `not_used_routed_to_owner`, `not_used_manual_order`, or
  `not_used_refused`.
- `refusal_layer` (Phase 1, null for answered questions):
  `keyword`, `product_reference`, `domain_coverage`, or
  `low_evidence_fallback`. See the Gen AI README for thresholds and
  the remaining limitation: this is a prototype guardrail, NOT a
  production out-of-distribution detector.
- `pemesanan` (order questions) and `keluhan` (complaints) are
  routing only: the prototype does NOT create orders, payments,
  shipments, or returns.

## Data Science Outputs (consumed as files, not live API in prototype)

- `data-science/outputs/business_summary.json`: totals, units by
  channel/product, low-stock counts, findings, recommendations
  (all labelled dummy).
- `data-science/outputs/baseline_model.json`: baseline model metrics
  and split description.
- `data-science/data/nike_dummy/nike_sales_dummy.csv` and
  `data-science/data/nike_dummy/nike_products_dummy.csv`: see
  `data-science/data/nike_dummy/nike_data_dictionary.md` for
  columns. The old 600-row `dummy_inventory_sales.csv` stays in
  `data-science/data/` as an archive only and is no longer the
  dashboard source.
- Phase 1 integration (done): the backend `/api/v1/insights`
  endpoint now serves these outputs in its `data_science` section
  (see Insights shape above); the Streamlit dashboard remains the
  interactive view.

## Out of scope (all repos)

Automatic two-way sync to Instagram, Facebook, Carousell, or Shopee;
orders, payments, shipping, promotions, customer data, price
recommendations, stock forecasting as a production feature, and any
real UMKM data until the owner (Ade) decides to use it. There is no
external approver to wait for; data choices are the owner's decision.
