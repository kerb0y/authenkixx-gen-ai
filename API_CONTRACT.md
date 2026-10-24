# Shared API Contract (Prototype)

Agreed across Full-Stack, Gen AI, and Data Science repos. Prototype
only, dummy data only. Version: v1, 2026-10-24.

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
| GET | `/insights` | - | `{ total_products, total_stock, low_stock_count, low_stock_products[], by_availability, data_label: "dummy" }` |
| POST | `/ai/chat` | `{ message: string (1-500 chars) }` | Gen AI ChatResponse, wrapped, plus `history_id` |
| GET | `/ai/history` | - | Chat history entries `{ message, intent, route, answer, created_at }` |

Product shape:
```json
{
  "id": "DUMMY-001",
  "name": "Sepatu Sneakers Putih (Contoh)",
  "price": 299000,
  "stock": 12,
  "availability": "tersedia",
  "channels": ["Instagram", "Shopee"],
  "data_label": "dummy"
}
```
`availability` is one of `tersedia`, `menipis`, `habis`. On stock
updates the backend recomputes it: stock 0 = `habis`, stock <= 5 =
`menipis`, otherwise `tersedia`. `channels` are labels only; there is
NO automatic synchronisation with any platform.

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
- `pemesanan` (order questions) and `keluhan` (complaints) are
  routing only: the prototype does NOT create orders, payments,
  shipments, or returns.

## Data Science Outputs (consumed as files, not live API in prototype)

- `data-science/outputs/business_summary.json`: totals, units by
  channel/product, low-stock counts, findings, recommendations
  (all labelled dummy).
- `data-science/outputs/baseline_model.json`: baseline model metrics
  and split description.
- `data-science/data/dummy_inventory_sales.csv`: see
  `data-science/data/data_dictionary.md` for columns.
- Final-version integration point (tomorrow): the backend
  `/api/v1/insights` endpoint is where Data Science outputs should be
  served once real data is confirmed; the Streamlit dashboard remains
  the interactive view.

## Out of scope (all repos)

Automatic two-way sync to Instagram, Facebook, Carousell, or Shopee;
orders, payments, shipping, promotions, customer data, price
recommendations, stock forecasting as a production feature, and any
real UMKM data until the PIC confirms it.
