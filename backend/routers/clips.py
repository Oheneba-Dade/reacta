import logging
import time
import uuid

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.config import settings
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.clip import Clip, EmbeddingStatus, ProcessingStatus, TranscriptStatus
from backend.models.tag import TagDefinition
from backend.models.user import User
from backend.schemas.clip import ClipCreateResponse, ClipResponse, ClipStatusResponse, ClipUpdateRequest
from backend.services.storage import get_storage

router = APIRouter(prefix="/clips", tags=["clips"])
logger = logging.getLogger("reacta.clips")


async def _enqueue_process_clip(clip_id: str) -> None:
    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    await redis.enqueue_job("process_clip", clip_id)
    await redis.aclose()


async def _get_owned_clip(clip_id: uuid.UUID, user: User, db: AsyncSession) -> Clip:
    result = await db.execute(
        select(Clip).where(Clip.id == clip_id).options(selectinload(Clip.tags))
    )
    clip = result.scalar_one_or_none()
    if clip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Clip not found"},
        )
    if clip.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "You do not own this clip"},
        )
    return clip


@router.get("", response_model=list[ClipResponse])
async def list_clips(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ClipResponse]:
    result = await db.execute(
        select(Clip)
        .where(Clip.owner_id == current_user.id)
        .options(selectinload(Clip.tags))
        .order_by(Clip.created_at.desc())
    )
    clips = result.scalars().all()
    return [ClipResponse.model_validate(c) for c in clips]


@router.get("/{clip_id}", response_model=ClipResponse)
async def get_clip(
    clip_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClipResponse:
    clip = await _get_owned_clip(clip_id, current_user, db)
    return ClipResponse.model_validate(clip)


@router.post("", status_code=202, response_model=ClipCreateResponse)
async def upload_clip(
    file: UploadFile = File(...),
    description: str = Form(...),
    title: str | None = Form(None),
    tag_ids: list[uuid.UUID] = Form(default=[]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClipCreateResponse:
    file_bytes = await file.read()
    filename = file.filename or "upload"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    clip_id = uuid.uuid4()
    storage_key = f"{current_user.id}/{clip_id}{ext}"

    storage = get_storage()
    upload_start = time.time()
    storage.save(storage_key, file_bytes)
    upload_duration_ms = round((time.time() - upload_start) * 1000)

    tags: list[TagDefinition] = []
    if tag_ids:
        tag_result = await db.execute(
            select(TagDefinition).where(TagDefinition.id.in_(tag_ids))
        )
        tags = list(tag_result.scalars().all())

    clip = Clip(
        id=clip_id,
        owner_id=current_user.id,
        title=title,
        description=description,
        original_filename=filename,
        file_extension=ext,
        storage_key=storage_key,
        duration_seconds=0.0,
        file_size_bytes=len(file_bytes),
        processing_status=ProcessingStatus.pending,
        desc_embedding_status=EmbeddingStatus.pending,
        transcript_status=TranscriptStatus.pending,
        tags=tags,
    )
    db.add(clip)
    await db.commit()
    logger.info(
        f"clip uploaded: clip_id={clip_id}, owner_id={current_user.id}, "
        f"file_size_bytes={len(file_bytes)}, duration_ms={upload_duration_ms}"
    )

    await _enqueue_process_clip(str(clip_id))

    return ClipCreateResponse(id=clip_id, processing_status=ProcessingStatus.pending.value)


@router.patch("/{clip_id}", response_model=ClipResponse)
async def update_clip(
    clip_id: uuid.UUID,
    body: ClipUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClipResponse:
    clip = await _get_owned_clip(clip_id, current_user, db)

    description_changed = body.description is not None and body.description != clip.description

    if body.title is not None:
        clip.title = body.title
    if body.description is not None:
        clip.description = body.description
    if body.tag_ids is not None:
        tag_result = await db.execute(
            select(TagDefinition).where(TagDefinition.id.in_(body.tag_ids))
        )
        clip.tags = list(tag_result.scalars().all())

    if description_changed:
        clip.description_embedding = None
        clip.desc_embedding_status = EmbeddingStatus.pending
        clip.desc_embedding_error = None

    await db.commit()
    await db.refresh(clip)

    if description_changed:
        await _enqueue_process_clip(str(clip_id))

    return ClipResponse.model_validate(clip)


@router.delete("/{clip_id}", status_code=204)
async def delete_clip(
    clip_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    clip = await _get_owned_clip(clip_id, current_user, db)

    storage = get_storage()
    try:
        storage.delete(clip.storage_key)
    except Exception as exc:
        logger.warning(f"clip {clip_id}: storage cleanup failed — {exc}")

    await db.delete(clip)
    await db.commit()
    logger.info(f"clip deleted: clip_id={clip_id}, owner_id={current_user.id}")


@router.get("/{clip_id}/status", response_model=ClipStatusResponse)
async def get_clip_status(
    clip_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClipStatusResponse:
    clip = await _get_owned_clip(clip_id, current_user, db)
    return ClipStatusResponse.model_validate(clip)


@router.post("/{clip_id}/reprocess", status_code=202, response_model=ClipCreateResponse)
async def reprocess_clip(
    clip_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClipCreateResponse:
    clip = await _get_owned_clip(clip_id, current_user, db)

    if clip.processing_status != ProcessingStatus.failed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": "Only clips with processing_status 'failed' can be reprocessed"},
        )

    clip.processing_status = ProcessingStatus.pending
    clip.desc_embedding_status = EmbeddingStatus.pending
    clip.desc_embedding_error = None
    clip.transcript_status = TranscriptStatus.pending
    clip.transcript_error = None
    clip.description_embedding = None
    await db.commit()

    await _enqueue_process_clip(str(clip_id))
    logger.info(f"clip reprocess requested: clip_id={clip_id}, owner_id={current_user.id}")

    return ClipCreateResponse(id=clip_id, processing_status=ProcessingStatus.pending.value)
