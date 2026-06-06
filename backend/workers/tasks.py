import asyncio
import json
import uuid
from typing import Any

from arq.connections import RedisSettings
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import AsyncSessionLocal
from backend.models.clip import Clip, EmbeddingStatus, ProcessingStatus, TranscriptStatus
from backend.models.transcript import TranscriptEmbedding
from backend.services.embeddings import embedding_service
from backend.services.transcription import transcription_service
from backend.services.storage import get_storage


def chunk_transcript(text: str, max_words: int = 100, overlap: int = 20) -> list[str]:
    """Sliding window word chunker. Returns at least one chunk even for short transcripts."""
    words = text.split()
    if not words:
        return []
    if len(words) <= max_words:
        return [text]

    chunks = []
    step = max_words - overlap
    for start in range(0, len(words), step):
        chunk_words = words[start : start + max_words]
        chunks.append(" ".join(chunk_words))
        if start + max_words >= len(words):
            break
    return chunks


async def process_clip(ctx: dict[str, Any], clip_id: str) -> None:
    """
    Background job: transcribe audio, embed transcript chunks, embed description.
    Each step fails independently — failures are written to the relevant error column.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Clip).where(Clip.id == uuid.UUID(clip_id)))
        clip = result.scalar_one_or_none()
        if clip is None:
            return

        # Step 1: mark as processing
        clip.processing_status = ProcessingStatus.processing
        await db.commit()

        # Steps 2–4: validate file and extract duration
        storage = get_storage()
        file_path = storage.get_url(clip.storage_key)

        try:
            await _validate_and_extract_duration(clip, file_path, db)
        except Exception as exc:
            clip.processing_status = ProcessingStatus.failed
            clip.desc_embedding_error = f"Processing failed: {exc}"
            await db.commit()
            return

        # Step 5: transcription (skip if already completed)
        if clip.transcript_status != TranscriptStatus.completed:
            try:
                transcript = await asyncio.to_thread(transcription_service.transcribe, file_path)
                clip.transcript = transcript
                clip.transcript_status = TranscriptStatus.completed
                clip.transcript_error = None
                await db.commit()
            except Exception as exc:
                clip.transcript_status = TranscriptStatus.failed
                clip.transcript_error = str(exc)
                await db.commit()

        # Steps 6–7: chunk and embed transcript
        if clip.transcript and clip.transcript_status == TranscriptStatus.completed:
            try:
                chunks = chunk_transcript(clip.transcript)
                embeddings = await asyncio.to_thread(embedding_service.embed_batch, chunks)

                await db.execute(
                    delete(TranscriptEmbedding).where(TranscriptEmbedding.clip_id == clip.id)
                )
                for idx, (chunk, vec) in enumerate(zip(chunks, embeddings)):
                    db.add(TranscriptEmbedding(
                        clip_id=clip.id,
                        transcript_chunk=chunk,
                        chunk_index=idx,
                        embedding=vec,
                    ))
                await db.commit()
            except Exception as exc:
                await db.rollback()

        # Step 8: embed description
        if clip.description:
            try:
                vec = await asyncio.to_thread(embedding_service.embed, clip.description)
                clip.description_embedding = vec
                clip.desc_embedding_status = EmbeddingStatus.completed
                clip.desc_embedding_error = None
                await db.commit()
            except Exception as exc:
                clip.desc_embedding_status = EmbeddingStatus.failed
                clip.desc_embedding_error = str(exc)
                await db.commit()


async def _validate_and_extract_duration(clip: Clip, file_path: str, db: AsyncSession) -> None:
    """Run ffprobe to get duration, update clip, set processing_status = ready."""
    import os
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    proc = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        file_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError("ffprobe failed")

    data = json.loads(stdout)
    duration = 0.0
    for stream in data.get("streams", []):
        if "duration" in stream:
            duration = float(stream["duration"])
            break

    clip.duration_seconds = duration
    clip.processing_status = ProcessingStatus.ready
    await db.commit()


class WorkerSettings:
    functions = [process_clip]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
