from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.tag import TagDefinition
from backend.models.user import User
from backend.schemas.search import SearchRequest, SearchResponse
from backend.services.search import search_clips

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(
    body: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    result = await db.execute(select(TagDefinition.label))
    tag_labels = list(result.scalars().all())
    return await search_clips(
        query=body.query,
        user_id=current_user.id,
        db=db,
        tag_labels=tag_labels,
        limit=body.limit,
    )
