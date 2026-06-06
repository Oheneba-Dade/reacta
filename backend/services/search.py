import asyncio
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.clip import Clip
from backend.models.transcript import TranscriptEmbedding
from backend.schemas.search import SearchResponse, SearchResult
from backend.services.embeddings import embedding_service


async def search_clips(
    query: str,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> SearchResponse:
    """Embed query, fan out across both signals in parallel, merge and return top 10."""
    query_vec = await asyncio.to_thread(embedding_service.embed, query)

    desc_scores, transcript_scores = await asyncio.gather(
        _search_description_embeddings(query_vec, user_id, db),
        _search_transcript_embeddings(query_vec, user_id, db),
    )

    merged = _merge_results(desc_scores, transcript_scores)

    clip_ids = [clip_id for clip_id, _, _ in merged]
    if not clip_ids:
        return SearchResponse(results=[])

    result = await db.execute(
        select(Clip)
        .where(Clip.id.in_(clip_ids))
        .options(selectinload(Clip.tags))
    )
    clips_by_id = {clip.id: clip for clip in result.scalars().all()}

    results = []
    for clip_id, score, match_source in merged:
        clip = clips_by_id.get(clip_id)
        if clip:
            results.append(SearchResult(clip=clip, score=score, match_source=match_source))

    return SearchResponse(results=results)


async def _search_description_embeddings(
    query_vec: list[float],
    user_id: uuid.UUID,
    db: AsyncSession,
    limit: int = 20,
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
        {"vec": str(query_vec), "user_id": str(user_id), "limit": limit},
    )
    return {uuid.UUID(str(row.id)): float(row.score) for row in result}


async def _search_transcript_embeddings(
    query_vec: list[float],
    user_id: uuid.UUID,
    db: AsyncSession,
    limit: int = 20,
) -> dict[uuid.UUID, float]:
    """Cosine similarity search on transcript_embeddings, grouped by clip."""
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
        {"vec": str(query_vec), "user_id": str(user_id), "limit": limit},
    )
    return {uuid.UUID(str(row.clip_id)): float(row.score) for row in result}


def _merge_results(
    desc_scores: dict[uuid.UUID, float],
    transcript_scores: dict[uuid.UUID, float],
) -> list[tuple[uuid.UUID, float, str]]:
    """Merge both score dicts, keep highest score per clip, assign match_source."""
    all_ids = set(desc_scores) | set(transcript_scores)
    merged = []
    for clip_id in all_ids:
        in_desc = clip_id in desc_scores
        in_transcript = clip_id in transcript_scores

        if in_desc and in_transcript:
            score = max(desc_scores[clip_id], transcript_scores[clip_id])
            match_source = "both"
        elif in_desc:
            score = desc_scores[clip_id]
            match_source = "description"
        else:
            score = transcript_scores[clip_id]
            match_source = "transcript"

        merged.append((clip_id, score, match_source))

    merged.sort(key=lambda x: x[1], reverse=True)
    return merged[:10]
