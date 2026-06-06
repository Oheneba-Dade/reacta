from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.tag import TagDefinition
from backend.schemas.tag import TagResponse

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagResponse])
async def list_tags(db: AsyncSession = Depends(get_db)) -> list[TagResponse]:
    result = await db.execute(select(TagDefinition).order_by(TagDefinition.label))
    tags = result.scalars().all()
    return [TagResponse.model_validate(t) for t in tags]
