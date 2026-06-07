from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.config import settings

# Railway's Postgres provides DATABASE_URL with postgresql:// scheme.
# SQLAlchemy's async engine requires the +asyncpg dialect prefix.
_db_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
engine = create_async_engine(_db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
