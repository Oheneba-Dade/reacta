from typing import Literal

from pydantic import BaseModel

from backend.schemas.clip import ClipResponse


class SearchRequest(BaseModel):
    query: str


class SearchResult(BaseModel):
    clip: ClipResponse
    score: float
    match_source: Literal["description", "transcript", "both"]


class SearchResponse(BaseModel):
    results: list[SearchResult]
