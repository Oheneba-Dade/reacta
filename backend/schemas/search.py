from typing import Literal

from pydantic import BaseModel, Field

from backend.schemas.clip import ClipResponse


class SearchRequest(BaseModel):
    query: str
    limit: int = Field(default=3, ge=1, le=10)


class SearchResult(BaseModel):
    clip: ClipResponse
    score: float
    match_source: Literal["description", "transcript", "both"]


class SearchResponse(BaseModel):
    results: list[SearchResult]
