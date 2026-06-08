# CLAUDE.md — Reacta

> Standing instructions for Claude Code. Read this at the start of every session.
> Last updated: June 2026

---

## What is Reacta

Reacta is a personal reaction video clip library with semantic search. Users upload short reaction clips (2–7 seconds), write a description, select categorical tags, and can later find clips by searching in natural language — even if the search wording differs completely from how the clip was described.

The core problem being solved is a **vocabulary gap**: you tag a clip one way, you search for it another way. The embedding model (`all-MiniLM-L6-v2`) bridges that gap.

---

## Stack

| Layer           | Choice                                                              |
| --------------- | ------------------------------------------------------------------- |
| Language        | Python 3.11+                                                        |
| Framework       | FastAPI (async)                                                     |
| Database        | PostgreSQL + pgvector                                               |
| ORM             | SQLAlchemy (async) + asyncpg                                        |
| Auth            | JWT via python-jose                                                 |
| Embeddings      | sentence-transformers (`all-MiniLM-L6-v2`) — local, no external API |
| Transcription   | OpenAI Whisper (local)                                              |
| Background jobs | ARQ (async Redis queue)                                             |
| File storage    | DiskStorage v1, S3-compatible via abstraction later                 |
| Infrastructure  | Self-hosted VPS (DigitalOcean or Linode)                            |

---

## Project structure

```
reacta/
  main.py
  config.py
  database.py
  models/
    user.py
    clip.py
    tag.py
    transcript.py
  schemas/
    auth.py
    clip.py
    search.py
    tag.py
  routers/
    auth.py
    clips.py
    search.py
    tags.py
  services/
    storage.py       # StorageBackend abstraction
    embeddings.py    # sentence-transformers wrapper
    transcription.py # Whisper wrapper
    search.py        # fan-out search logic
  workers/
    tasks.py         # ARQ background tasks
  migrations/
    001_initial.sql
  seeds/
    tags.sql
docs/
  ADRs/
  context/
```

---

## Database schema

Five tables. Do not add, rename, or restructure without flagging it first.

```sql
-- Enums
CREATE TYPE processing_status AS ENUM ('pending', 'processing', 'ready', 'failed');
CREATE TYPE transcript_status AS ENUM ('pending', 'completed', 'failed');
CREATE TYPE embedding_status  AS ENUM ('pending', 'completed', 'failed');

-- users
CREATE TABLE users (
  id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  username      VARCHAR(255) UNIQUE NOT NULL,
  email         VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at    TIMESTAMPTZ  DEFAULT NOW(),
  updated_at    TIMESTAMPTZ  DEFAULT NOW()
);

-- clips
CREATE TABLE clips (
  id                    UUID              PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id              UUID              NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title                 VARCHAR(255),
  description           TEXT,
  original_filename     VARCHAR(255)      NOT NULL,
  file_extension        VARCHAR(10)       NOT NULL,
  storage_key           VARCHAR(500)      NOT NULL,
  duration_seconds      FLOAT             NOT NULL,
  file_size_bytes       BIGINT            NOT NULL,
  is_public             BOOLEAN           DEFAULT FALSE,
  processing_status     processing_status NOT NULL DEFAULT 'pending',
  description_embedding VECTOR(384),
  desc_embedding_status embedding_status  DEFAULT 'pending',
  desc_embedding_error  TEXT,
  transcript            TEXT,
  transcript_status     transcript_status DEFAULT 'pending',
  transcript_error      TEXT,
  created_at            TIMESTAMPTZ       DEFAULT NOW(),
  updated_at            TIMESTAMPTZ       DEFAULT NOW()
);

-- tag_definitions (global predefined vocabulary, seeded at deploy time)
CREATE TABLE tag_definitions (
  id         UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  label      VARCHAR(100) UNIQUE NOT NULL,
  created_at TIMESTAMPTZ  DEFAULT NOW()
);

-- clip_tags (join table — no embeddings, tags are filters not search signals)
CREATE TABLE clip_tags (
  clip_id UUID NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
  tag_id  UUID NOT NULL REFERENCES tag_definitions(id) ON DELETE CASCADE,
  PRIMARY KEY (clip_id, tag_id)
);

-- transcript_embeddings (one row per chunk per clip)
CREATE TABLE transcript_embeddings (
  id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  clip_id          UUID        NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
  transcript_chunk TEXT        NOT NULL,
  chunk_index      INT         NOT NULL,
  embedding        VECTOR(384) NOT NULL,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);
```

### Critical schema decisions

- **Tags have no embeddings.** Tags are browsing filters handled client-side. They are not semantic search signals. Do not add an `embedding` column to `tag_definitions`.
- **description_embedding lives on clips.** Not in a separate table. One clip = one description = one embedding.
- **Three independent async status columns.** `processing_status`, `transcript_status`, `desc_embedding_status` are separate because they fail separately. Never merge them.
- **TIMESTAMPTZ everywhere.** Never plain TIMESTAMP.
- **HNSW indexes** on `clips.description_embedding` and `transcript_embeddings.embedding`, both with `vector_cosine_ops`.

---

## API endpoints

All routes prefixed `/api/v1`. All protected routes require `Authorization: Bearer <access_token>`.

```
POST   /auth/register
POST   /auth/login
POST   /auth/refresh

GET    /clips                    — full list with tags, for client-side filtering
GET    /clips/{clip_id}
POST   /clips                    — multipart upload, returns 202
PATCH  /clips/{clip_id}          — re-queues embedding if description changes
DELETE /clips/{clip_id}
GET    /clips/{clip_id}/status   — lightweight poll endpoint
POST   /clips/{clip_id}/reprocess — reset failed clip state and re-queue job (400 if not failed)

POST   /search                   — semantic search, always queries both signals

GET    /tags                     — full tag vocabulary, load once on startup
```

### Error response shape

```json
{ "error": "snake_case_code", "message": "Human readable explanation" }
```

Common codes: `unauthorized`, `forbidden`, `not_found`, `conflict`, `validation_error`, `processing_error`

---

## Search logic

Search always fans out across **both** signals in parallel. Never query only one.

```
query → embed (all-MiniLM-L6-v2)
  → cosine search on clips.description_embedding WHERE owner_id = user
  → cosine search on transcript_embeddings.embedding JOIN clips WHERE owner_id = user
  → merge, deduplicate by clip_id, keep highest score
  → set match_source: "description" | "transcript" | "both"
  → return top 10 sorted by score descending
```

Search response includes `match_source` per result — useful for debugging and UI display.

---

## Background job: process_clip(clip_id)

Triggered after every upload and whenever description changes. Implemented as an ARQ task.

Steps in order:

1. Set `processing_status = 'processing'`
2. Validate file exists on disk
3. Extract `duration_seconds` via ffprobe
4. Set `processing_status = 'ready'`
5. Run Whisper → update `transcript` + `transcript_status`
6. Chunk transcript (~100 words, ~20 word overlap)
7. Embed each chunk → insert rows into `transcript_embeddings`
8. Embed description → update `description_embedding` + `desc_embedding_status = 'completed'`

On failure at any step: update the relevant status column to `'failed'`, write error to the error column, do not crash the worker. Each step fails independently.

**Transient errors** (`httpx.HTTPStatusError`, `httpx.TimeoutException`, `httpx.ConnectError`) are re-raised so ARQ retries the job (up to `max_tries=3`, `retry_delay=5s`). The clip is reset to `pending` before re-raising.

**Permanent errors** (`FileNotFoundError`, ffprobe failure, Whisper failure) are caught, logged, and written to the error columns — the job ends as failed with no retry.

**Logging**: `reacta.worker` logger emits INFO on each step completion and ERROR on each failure. `main.py` configures `logging.basicConfig` at startup.

---

## Storage abstraction

Storage is abstracted from day one to allow migration from VPS disk to S3-compatible object storage without changing application code.

```python
class StorageBackend:
    def save(self, key: str, file_bytes: bytes) -> str: ...
    def get_url(self, key: str) -> str: ...
    def delete(self, key: str) -> None: ...

class DiskStorage(StorageBackend): ...   # active in v1
class S3Storage(StorageBackend): ...     # stub, NotImplementedError
```

Storage key format: `{user_id}/{clip_uuid}{ext}`

Switch backend via `STORAGE_BACKEND` env var (`"disk"` or `"s3"`).

---

## Tag management

Tags are managed via seed script only. No admin API endpoint.

```sql
-- seeds/tags.sql
INSERT INTO tag_definitions (label) VALUES
  ('shock'), ('joy'), ('disgust'), ('fear'),
  ('anger'), ('surprise'), ('confusion'), ('excitement')
ON CONFLICT (label) DO NOTHING;
```

Run once at deploy. Add new tags by editing the file and re-running. Do not build an admin endpoint for this.

---

## Auth

- Passwords hashed with bcrypt
- Access token: 30 minute expiry
- Refresh token: 30 day expiry
- All protected routes resolve current user from JWT
- 401 for missing/expired/invalid token
- 403 for valid token but wrong owner

---

## Config (environment variables)

```
DATABASE_URL
SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
MEDIA_ROOT
STORAGE_BACKEND=disk
REDIS_URL
WHISPER_MODEL=base
```

---

## Code standards

- Type hints required on all functions and class attributes
- Google-style docstrings on all public functions and classes
- Black formatter, line length 100
- Async throughout — use `async def` and `await`, never blocking calls in route handlers
- No wildcard imports
- All DB queries go through SQLAlchemy — no raw SQL in routers or services

---

## What is NOT in scope for v1

Do not implement these unless explicitly asked:

- `S3Storage` full implementation (leave stub with `NotImplementedError`)
- Public clip sharing (`is_public` exists in schema but no public endpoints)
- Admin endpoints for tag management
- Any frontend or HTML responses
- Rate limiting
- Email verification

---

## Key design decisions (summarised)

| Decision          | Choice                      | Reason                                    |
| ----------------- | --------------------------- | ----------------------------------------- |
| Embeddings        | Local sentence-transformers | Learning value, no API cost               |
| Vector DB         | pgvector on Postgres        | Avoid extra infrastructure                |
| Tags in search    | No                          | Tags are filters, not semantic signals    |
| Tag embeddings    | None                        | Not needed for filter-only tags           |
| Transcript search | Yes (Whisper)               | Catches spoken content description misses |
| Multi-user        | Yes from day one            | Right architecture even for personal tool |
| Storage           | Abstracted from day one     | Easy migration to S3 later                |
| Tag management    | Seed script only            | No scope for admin UI in v1               |
| Background jobs   | ARQ                         | Async-native, fits FastAPI well           |

---

## When you are unsure

1. Check this file first
2. Check `docs/ADRs/` for relevant decisions
3. Check `docs/context/` for system design notes
4. Ask before making architectural changes — do not silently restructure
