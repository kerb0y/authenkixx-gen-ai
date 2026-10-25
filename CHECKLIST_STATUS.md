# Disclaimer and Checklist Status - Phase 1 (not final)

By Ade Bintang. Team A26-CS200, Asah 2026 capstone, UMKM Authenkixx.

## Final target

The final version of this project is intended to match the team's
Authenkixx use-case document and to fulfil all Main Quest checklist
items for every learning path: Full-Stack (Front End and Back End),
Gen AI, and Data Science.

Use-case core that must stay true in the final version:
- Centralized inventory for multichannel sales, one master record
  (product name, price, stock quantity, availability).
- Main user is the shop owner only.
- Instagram, Facebook, Carousell, and Shopee appear only as manual
  channel labels. There is no automatic two-way sync to those platforms.
- No orders, payments, shipping, promotions, or customer data.

## Current status: Phase 1, not final

This commit is Phase 1. It does NOT yet claim full checklist
compliance. Do not quote Phase 1 numbers or features as the final
result.

### Fulfilled in Phase 1

- Full-Stack: decoupled Express backend and Vite frontend, routes
  under /api/v1/, Joi validation, Axios networking, clear
  success/failure/loading states, Gen AI accessed only via the
  backend, Gen AI history stored, API contract agreed across repos,
  GitHub history for all three repos.
- Full-Stack + Data Science integration: GET /api/v1/insights now
  serves Data Science business summary and baseline model metrics,
  with a graceful fallback when those files are missing.
- Gen AI: problem explained in README, preprocessing before the
  model, 4-intent classifier, comparison of 3 models/configurations
  with the same metrics and a selection reason in README, structured
  prompts, out-of-context refusal tested (24/24 refused, 12/12
  in-scope not refused in Phase 1), invalid-input and service-failure
  handling, Swagger/OpenAPI docs.
- Data Science: data wrangling, business questions, findings and
  recommendations, data dictionary, labelled dummy dataset,
  train/test split with no leakage for the baseline model, interactive
  Streamlit dashboard with filters and file upload, outputs provided
  in a form other teams can consume.

### Partial in Phase 1

- Tailwind CSS is loaded via CDN in the prototype; a proper install
  is still needed for production.
- Prototype persistence is a JSON file, not a production database.
- Gen AI history is stored in a JSON file, not a database.
- Data Science outputs are served as JSON through /api/v1/insights,
  but the Streamlit dashboard itself is not yet embedded in the
  Full-Stack web app.
- The Gen AI intent model is trained on dummy intent examples, not
  yet on data supplied by the Data Science team in the checklist sense.
- Data Science has one baseline classification model only; a
  regression/forecasting model and a multi-model comparison for Data
  Science are not yet built.
- The generative AI code path exists but is disabled without an API
  key, so no proprietary generative call has been demonstrated yet.

### Not yet built

- Public deployment to a free tier (frontend, backend, production
  database). Phase 1 runs locally only.
- Real embedding model plus vector database RAG (ChromaDB, FAISS,
  Pinecone, or Weaviate). Phase 1 uses TF-IDF retrieval only.
- Login or multi-user authentication. Phase 1 is owner-only and
  single-user by design.
- Optional side quests, if the team chooses them: sentiment
  classification model, and Telegram/WhatsApp integration.
- Replacement of dummy data with owner-decided data, and retraining
  plus re-comparison of models on that larger data.

## Data warning

All figures are dummy, labelled dummy. Since the Nike dummy
update, inventory and Data Science use the SAME product set:
120 Nike dummy products (NK-DUMMY-001 to NK-DUMMY-120) and
86,400 dummy sales rows (2026-01-01 to 2026-06-29). The old
Phase 1 mismatch (6-product inventory vs 600-row September 2026
summary) no longer applies to the current outputs; do not mix
old and new figures in one summary.
