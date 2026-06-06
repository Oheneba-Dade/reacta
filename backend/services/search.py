import asyncio
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from backend.models.clip import Clip
from backend.schemas.search import SearchResponse, SearchResult

# ---------------------------------------------------------------------------
# Scoring weights — tune these without touching any other logic
# ---------------------------------------------------------------------------
W_DESC_VEC  = 0.45   # semantic similarity to description embedding
W_TRANS_VEC = 0.20   # semantic similarity to transcript embedding
W_LEXICAL   = 0.25   # ts_rank keyword match in transcript chunks
W_EXACT     = 0.10   # verbatim word/phrase found in transcript
W_TAG       = 0.05   # query contains a tag label word
W_RECENCY   = 0.00   # linear recency decay (disabled; set to 0.05 to enable)
RECENCY_MAX_DAYS = 90

# Stage 1 candidate limits — union of both signals before merge
_VECTOR_LIMIT = 30

# ---------------------------------------------------------------------------
# Query preprocessing
# ---------------------------------------------------------------------------
_FILLER = re.compile(
    r"\b(video|clip|footage|of|someone|a person|they|them|him|her|"
    r"saying|reacting|reacts|reaction|when|where|watching|sees?|"
    r"who|that|this|with|and|the|just)\b",
    re.IGNORECASE,
)


def preprocess_query(query: str) -> tuple[str, str]:
    """Return (embed_query, search_terms).

    embed_query  — original query for the embedding model (full context matters)
    search_terms — filler stripped, used for tsquery and exact match checks
    """
    embed_query = query.strip().lower()
    cleaned = _FILLER.sub("", query).strip()
    search_terms = " ".join(cleaned.split())
    # Fall back to full query if stripping removed everything
    if not search_terms:
        search_terms = embed_query
    return embed_query, search_terms


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
async def search_clips(
    query: str,
    user_id: uuid.UUID,
    db: AsyncSession,
    tag_labels: list[str] | None = None,
) -> SearchResponse:
    """Two-stage hybrid search: vector retrieval → lexical rerank → top 10."""
    embed_query, search_terms = preprocess_query(query)

    # Stage 1: vector candidate retrieval (HNSW indexes)
    query_vec = await asyncio.to_thread(_embed, embed_query)

    desc_scores, trans_scores = await asyncio.gather(
        _search_description_embeddings(query_vec, user_id, db),
        _search_transcript_embeddings(query_vec, user_id, db),
    )

    candidate_ids = list(set(desc_scores) | set(trans_scores))
    if not candidate_ids:
        return SearchResponse(results=[])

    # Stage 2: lexical scoring on the candidate set (GIN indexes)
    lexical_data = await _fetch_lexical_scores(candidate_ids, search_terms, db)

    # Fetch full clip objects for the candidates
    result = await db.execute(
        select(Clip)
        .where(Clip.id.in_(candidate_ids))
        .options(selectinload(Clip.tags))
    )
    clips_by_id = {clip.id: clip for clip in result.scalars().all()}

    # Stage 3: compute final scores and rank in Python
    ranked = _compute_final_scores(
        desc_scores=desc_scores,
        trans_scores=trans_scores,
        lexical_data=lexical_data,
        clips_by_id=clips_by_id,
        tag_labels=tag_labels or [],
        search_terms=search_terms,
    )

    results = []
    for clip_id, score, match_source in ranked:
        clip = clips_by_id.get(clip_id)
        if clip:
            results.append(SearchResult(clip=clip, score=round(score, 4), match_source=match_source))

    return SearchResponse(results=results)


# ---------------------------------------------------------------------------
# Stage 1: vector retrieval
# ---------------------------------------------------------------------------
def _embed(text_input: str) -> list[float]:
    from backend.services.embeddings import embedding_service
    return embedding_service.embed(text_input)


async def _search_description_embeddings(
    query_vec: list[float],
    user_id: uuid.UUID,
    db: AsyncSession,
) -> dict[uuid.UUID, float]:
    """Cosine similarity search on clips.description_embedding."""
    stmt = text(
        """
        SELECT id, 1 - (description_embedding <=> CAST(:vec AS vector)) AS score
        FROM clips
        WHERE owner_id = :user_id
          AND description_embedding IS NOT NULL
          AND desc_embedding_status = 'completed'
        ORDER BY description_embedding <=> CAST(:vec AS vector)
        LIMIT :limit
        """
    )
    result = await db.execute(
        stmt,
        {"vec": str(query_vec), "user_id": str(user_id), "limit": _VECTOR_LIMIT},
    )
    return {uuid.UUID(str(row.id)): float(row.score) for row in result}


async def _search_transcript_embeddings(
    query_vec: list[float],
    user_id: uuid.UUID,
    db: AsyncSession,
) -> dict[uuid.UUID, float]:
    """Cosine similarity search on transcript_embeddings, best chunk per clip."""
    stmt = text(
        """
        SELECT te.clip_id, MAX(1 - (te.embedding <=> CAST(:vec AS vector))) AS score
        FROM transcript_embeddings te
        JOIN clips c ON c.id = te.clip_id
        WHERE c.owner_id = :user_id
        GROUP BY te.clip_id
        ORDER BY score DESC
        LIMIT :limit
        """
    )
    result = await db.execute(
        stmt,
        {"vec": str(query_vec), "user_id": str(user_id), "limit": _VECTOR_LIMIT},
    )
    return {uuid.UUID(str(row.clip_id)): float(row.score) for row in result}


# ---------------------------------------------------------------------------
# Stage 2: lexical scoring on candidate set
# ---------------------------------------------------------------------------
async def _fetch_lexical_scores(
    candidate_ids: list[uuid.UUID],
    search_terms: str,
    db: AsyncSession,
) -> dict[uuid.UUID, dict]:
    """Run ts_rank + exact match checks on the candidate clip IDs only."""
    if not search_terms:
        return {}

    # Build a safe ilike pattern for the first significant term
    first_term = search_terms.split()[0] if search_terms.split() else ""
    ilike_pattern = f"%{first_term.lower()}%"

    try:
        stmt = text(
            """
            SELECT
                te.clip_id,
                MAX(ts_rank(te.chunk_tsv,
                    plainto_tsquery('english', :terms)))      AS lexical_score,
                BOOL_OR(te.chunk_tsv @@
                    plainto_tsquery('english', :terms))        AS has_tsquery_match,
                BOOL_OR(LOWER(te.transcript_chunk) LIKE :ilike) AS has_ilike_match
            FROM transcript_embeddings te
            WHERE te.clip_id = ANY(:ids)
            GROUP BY te.clip_id
            """
        )
        result = await db.execute(
            stmt,
            {
                "terms": search_terms,
                "ilike": ilike_pattern,
                "ids": [str(cid) for cid in candidate_ids],
            },
        )
        return {
            uuid.UUID(str(row.clip_id)): {
                "lexical_score": float(row.lexical_score or 0.0),
                "has_exact_match": bool(row.has_tsquery_match or row.has_ilike_match),
            }
            for row in result
        }
    except Exception:
        # tsquery can fail on malformed input (e.g. bare operators); degrade gracefully
        return {}


# ---------------------------------------------------------------------------
# Stage 3: final scoring
# ---------------------------------------------------------------------------
def _tag_boost(search_terms: str, tag_labels: list[str]) -> float:
    q = search_terms.lower()
    return 1.0 if any(t.lower() in q for t in tag_labels) else 0.0


def _recency_score(created_at: datetime) -> float:
    age_days = (datetime.now(timezone.utc) - created_at).days
    return max(0.0, 1.0 - age_days / RECENCY_MAX_DAYS)


def _compute_final_scores(
    desc_scores: dict[uuid.UUID, float],
    trans_scores: dict[uuid.UUID, float],
    lexical_data: dict[uuid.UUID, dict],
    clips_by_id: dict[uuid.UUID, Clip],
    tag_labels: list[str],
    search_terms: str,
) -> list[tuple[uuid.UUID, float, str]]:
    """Apply weighted formula, assign match_source, return top 10 by score."""
    tag_score = _tag_boost(search_terms, tag_labels)
    all_ids = set(desc_scores) | set(trans_scores)
    ranked = []

    for clip_id in all_ids:
        d = desc_scores.get(clip_id, 0.0)
        t = trans_scores.get(clip_id, 0.0)
        lex = lexical_data.get(clip_id, {})
        lexical = lex.get("lexical_score", 0.0)
        exact   = 1.0 if lex.get("has_exact_match") else 0.0

        clip = clips_by_id.get(clip_id)
        recency = _recency_score(clip.created_at) if (W_RECENCY > 0 and clip) else 0.0

        score = (
            d       * W_DESC_VEC
            + t     * W_TRANS_VEC
            + lexical * W_LEXICAL
            + exact * W_EXACT
            + tag_score * W_TAG
            + recency   * W_RECENCY
        )

        in_desc = clip_id in desc_scores
        in_trans = clip_id in trans_scores
        if in_desc and in_trans:
            match_source = "both"
        elif in_desc:
            match_source = "description"
        else:
            match_source = "transcript"

        ranked.append((clip_id, score, match_source))

    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked[:10]
