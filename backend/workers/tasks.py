import asyncio
import json
import os
import tempfile
import uuid
from typing import Any

import httpx
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


async def _resolve_local_path(url: str, file_extension: str) -> tuple[str, bool]:
    """Return (local_path, is_temporary).

    DiskStorage returns a filesystem path — use it directly.
    S3Storage returns a presigned HTTPS URL — download to a named temp file.
    """
    if not (url.startswith("http://") or url.startswith("https://")):
        return url, False

    suffix = file_extension if file_extension.startswith(".") else f".{file_extension}"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name

    async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            with open(tmp_path, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=65536):
                    f.write(chunk)

    return tmp_path, True


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

        # Resolve file to a local path (downloads to temp file if S3/B2)
        storage = get_storage()
        file_url = storage.get_url(clip.storage_key)
        local_path, is_temp = await _resolve_local_path(file_url, clip.file_extension)

        try:
            # Steps 2–4: validate file and extract duration
            try:
                await _validate_and_extract_duration(clip, local_path, db)
            except Exception as exc:
                clip.processing_status = ProcessingStatus.failed
                clip.desc_embedding_error = f"Processing failed: {exc}"
                await db.commit()
                return

            # Step 5: transcription (skip if already completed)
            if clip.transcript_status != TranscriptStatus.completed:
                try:
                    transcript = await asyncio.to_thread(transcription_service.transcribe, local_path)
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

        finally:
            if is_temp:
                try:
                    os.unlink(local_path)
                except Exception:
                    pass


async def _validate_and_extract_duration(clip: Clip, file_path: str, db: AsyncSession) -> None:
    """Run ffprobe to get duration, update clip, set processing_status = ready."""
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
