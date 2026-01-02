# Compass 🔍

A minimal yet extensible web search engine prototype. Compass aims to provide a **neutral, fast, privacy-respecting** search experience. This MVP uses existing search APIs (stubbed for now) but is architected so that real crawling, indexing and ranking modules can be attached later.

---

## Folder structure

```
Compass/
 ├─ backend/               # FastAPI service
 │   ├─ app/
 │   │   ├─ adapters/      # Pluggable search adapters
 │   │   ├─ schemas.py     # Pydantic models shared across API
 │   │   ├─ config.py      # Global settings
 │   │   └─ main.py        # FastAPI entry-point
 │   └─ requirements.txt
 ├─ frontend/              # Vite + React single-page front-end
 │   ├─ src/
 │   │   ├─ App.tsx
 │   │   └─ main.tsx
 │   ├─ index.html
 │   ├─ package.json
 │   ├─ vite.config.ts
 │   └─ tsconfig.json
 └─ README.md              # THIS FILE
```

## Quick start (local development)

### 1. Backend

```bash
# from project root
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

# Run FastAPI with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir backend
```

The API is now available at **http://localhost:8000**

### 2. Frontend

```bash
cd frontend
npm install    # or pnpm / yarn

# Optional: point the UI to a different backend
# echo "VITE_COMPASS_API=http://localhost:8000" > .env.local

npm run dev
```

Open **http://localhost:5173** in your browser. Type a query and see stubbed results.

## How to extend Compass

Compass is intentionally modular:

- **Adapters** (`backend/app/adapters/*`) wrap external search APIs or future in-house index. Add a new class inheriting `SearchAdapter` and list it in `COMPASS_ADAPTERS`.
- **Ranking** logic currently just deduplicates. Replace `_aggregate_results` with sophisticated scoring.
- **Crawling / Indexing** modules can be introduced as separate micro-services writing to a search index (e.g. Elasticsearch); then create an adapter that queries that index.

### Next milestones (suggested)

1. **Real API adapters** – integrate Bing, Google Custom Search, Brave Search…
2. **Basic crawler** – crawl a whitelist of sites, store pages in a lightweight index (Whoosh/Lucene/Elastic).
3. **Indexer & Ranker** – implement BM25 / semantic ranking using vector embeddings.
4. **Auth & preferences** – allow users to pick preferred engines, safe-search, etc.
5. **Analytics without tracking** – aggregate usage anonymously to improve relevance.

## Philosophy

Compass respects user privacy by default, performing **no tracking** or identifying cookies. Future telemetry should be opt-in and aggregated.

---

© 2025 Compass Project. MIT License.
