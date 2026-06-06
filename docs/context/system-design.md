# reacta System Design (Summary)

## Architecture

React Frontend
↓ HTTP/REST
FastAPI Backend
├→ PostgreSQL + pgvector (data)
├→ sentence-transformers (embeddings)
├→ Whisper (transcription)
└→ VPS /data/clips/ (videos)

## Data Model

users
└─→ clips (owned by user)
├─→ tags (describe clip)
│ └─→ embedding (vector)
├─→ transcript_embeddings (chunks)
│ └─→ embedding (vector)
└─→ clip_access (Phase 2: sharing)

## Search Algorithm

1. Embed query (sentence-transformers)
2. Find similar tags (pgvector)
3. Find similar transcript chunks (pgvector)
4. Weight: 60% tags + 40% transcripts
5. Rank and return top-20

## Key Decisions

See `docs/ADRs/` for full rationale:

- ADR-001: Semantic search (not keywords)
- ADR-002: Local embeddings (learning goal)
- ADR-003: Multi-user architecture (day 1)
- ADR-004: pgvector (all-in-one solution)
- ADR-005: Whisper (local, free)

## Performance Targets (Phase 1)

- Search latency: <200ms
- Upload: <10s
- Memory: <1GB
- Storage: <100GB for 1000 clips


