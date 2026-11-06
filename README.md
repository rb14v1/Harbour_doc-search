# Doc Search

Semantic document search: React + Django REST Framework + PostgreSQL +
pgvector. Single user role (every endpoint scopes to the requesting user,
there is no admin/manager distinction beyond Django's own staff/superuser
flags for `/admin/`). No Celery/Redis - there is no background/async work.

## AI layer: stub by default

No OpenAI API key is required to run, build, or test this app. If
`OPENAI_API_KEY` is unset on the backend (the default), both AI-backed
functions in `backend/apps/common/ai.py` run in deterministic stub mode:

- `get_embedding(text)` returns a reproducible pseudo-random unit vector
  derived from a SHA-256 hash of the text. **This is NOT semantically
  meaningful** - identical text always gives the identical vector, but
  similar meaning does NOT give similar vectors. It exists purely so
  storage, similarity search, and ranking are fully exercisable without a
  key. Search results under stub mode will look arbitrary with respect to
  meaning - that's expected, not a bug.
- `generate_answer(question, context_snippets)` returns a templated string
  like `[STUB AI RESPONSE — set OPENAI_API_KEY for real output] Found N
  related document(s). Top match excerpt: ...` instead of calling a chat
  model.

Set `OPENAI_API_KEY` (plus optionally `OPENAI_EMBEDDING_MODEL`,
`OPENAI_EMBEDDING_DIMENSIONS`, `OPENAI_CHAT_MODEL`) to switch both functions
to real OpenAI API calls - no other code changes needed anywhere in the app.
The frontend Search page shows a visible banner reminding the user when
responses are stubs.

## Vector storage: dual-path by backend

`backend/apps/common/embedding_field.py` defines an `EmbeddingField()`
factory used by the `Document` model:

- **Postgres (production):** `pgvector.django.VectorField(dimensions=1536)`,
  backed by the `pgvector` extension. The first migration that touches this
  field (`apps/documents/migrations/0001_initial.py`) runs `CREATE EXTENSION
  IF NOT EXISTS vector;` via a `RunPython` step, guarded to only execute
  when `schema_editor.connection.vendor == "postgresql"`.
- **SQLite (dev/test only, `USE_SQLITE=True`):** a plain `JSONField` storing
  a list of floats. SQLite has no vector extension, so
  `backend/apps/common/vector_search.py`'s `similarity_search()` falls back
  to computing cosine similarity in pure Python (no numpy required) instead
  of pushing the computation into the database via pgvector's
  `CosineDistance`.

Both paths expose the identical model attribute name (`embedding`) and the
identical `similarity_search(queryset, query_vector, top_k)` function
signature, so no other code in the app branches on which database backend
is active.

`EMBEDDING_DIMENSIONS` defaults to 1536 (configurable via
`OPENAI_EMBEDDING_DIMENSIONS`) - `text-embedding-3-large`'s native
dimensionality is 3072, but the OpenAI API supports shortening output
vectors via the `dimensions` parameter.

## Local setup

### Backend (Postgres + pgvector, production-shaped)

```bash
cd backend
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp ../.env.example ../.env   # edit as needed; ensure USE_SQLITE=False
python manage.py migrate
python manage.py runserver
```

### Backend (SQLite dev-only fallback, no Postgres/pgvector required)

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export USE_SQLITE=True        # PowerShell: $env:USE_SQLITE="True"
python manage.py migrate      # creates demo@example.com / demo12345 + 10 seed documents
python manage.py test
python manage.py runserver
```

### Docker Compose (Postgres + pgvector + backend + frontend)

```bash
cp .env.example .env
docker compose up --build
```

### Frontend

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173
npm run build   # production build
```

## Demo data

The `apps.documents` app ships an idempotent data migration
(`0002_seed_data.py`) that creates a demo user (`demo@example.com` /
`demo12345`) and 10 sample documents spanning cooking, hiking, and personal
finance, with embeddings computed via the same `get_embedding()` function
the live API uses. Without `OPENAI_API_KEY` set, these seeded documents get
stub (non-meaningful) embeddings - set the key and re-save a document via
the API to get a real one. The migration is safe to re-run: it uses
`get_or_create()` keyed on user email / (user, title) so it never inserts
duplicates.

## API

- `POST /api/auth/register/`, `POST /api/auth/login/` (JWT),
  `POST /api/auth/refresh/`, `POST /api/auth/logout/`, `GET /api/auth/me/`
- `GET|POST /api/documents/`, `GET|PATCH|PUT|DELETE /api/documents/<id>/`
  (all scoped to the requesting user)
- `GET /api/search/?q=<query>&k=<top_k>` - embeds the query, runs
  `similarity_search` over the requesting user's own documents, and returns
  the top-k matches (`id`, `title`, `content_excerpt`, `similarity_score`)
  plus a `generated_answer` field from `generate_answer()`.

## What's NOT verified here

This environment has no live Postgres+pgvector connection (pgvector is
being built from source separately). Everything above was built and tested
against SQLite via the dual-path design, and the Postgres/pgvector code
paths (`VectorField`, `CosineDistance`, the `CREATE EXTENSION vector`
migration step) were written to be correct but could not be executed here.
Once a local Postgres with pgvector is available:

1. Create the `doc_search` role/database per `.env.example`.
2. Set `USE_SQLITE=False` and run `python manage.py migrate` - confirm the
   extension is created and the `documents_document.embedding` column is a
   real `vector(1536)` column (`\d+ documents_document` in `psql`).
3. Re-run `python manage.py test` against Postgres to confirm
   `CosineDistance`-based ranking matches the SQLite pure-Python ranking on
   the same fixtures.
4. Optionally set `OPENAI_API_KEY` to confirm the real embeddings/chat
   completion calls work end-to-end (model IDs are wired through from env
   vars but were not validated against the live OpenAI API from this
   environment).
