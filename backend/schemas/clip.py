import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.schemas.tag import TagResponse


class ClipResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    title: str | None
    description: str | None
    original_filename: str
    file_extension: str
    storage_key: str
    duration_seconds: float
    file_size_bytes: int
    is_public: bool
    processing_status: str
    desc_embedding_status: str
    transcript_status: str
    tags: list[TagResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClipCreateResponse(BaseModel):
    id: uuid.UUID
    processing_status: str


class ClipStatusResponse(BaseModel):
    id: uuid.UUID
    processing_status: str
    desc_embedding_status: str
    transcript_status: str

    model_config = ConfigDict(from_attributes=True)


class ClipUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    tag_ids: list[uuid.UUID] | None = None
