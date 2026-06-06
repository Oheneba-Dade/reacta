import os
import uuid

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Override DATABASE_URL before the app (and its config) loads.
TEST_DB_URL = "postgresql+asyncpg://postgres:lookatcurryman@localhost:5433/reacta_test"
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("MEDIA_ROOT", "/tmp/reacta_test_media")
os.environ.setdefault("STORAGE_BACKEND", "disk")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("WHISPER_MODEL", "base")

MIGRATIONS = [
    os.path.join(os.path.dirname(__file__), "../backend/migrations/001_initial.sql"),
    os.path.join(os.path.dirname(__file__), "../backend/migrations/002_hybrid_search.sql"),
]
SEEDS_SQL = os.path.join(os.path.dirname(__file__), "../backend/seeds/tags.sql")


async def _run_sql_file(conn: asyncpg.Connection, path: str) -> None:
    with open(path) as f:
        sql = f.read()
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            try:
                await conn.execute(stmt)
            except Exception:
                pass  # ignore "already exists" on re-runs


@pytest_asyncio.fixture(scope="session", autouse=True)
async def db_setup():
    """Run migrations + seeds against reacta_test once per session; tear down after."""
    conn = await asyncpg.connect(
        host="localhost", port=5433, user="postgres",
        password="lookatcurryman", database="reacta_test",
    )
    for migration in MIGRATIONS:
        await _run_sql_file(conn, migration)
    await _run_sql_file(conn, SEEDS_SQL)
    await conn.close()

    # Patch the SQLAlchemy engine to use NullPool so tests on different event loops
    # don't share pooled connections (avoids "attached to a different loop" errors).
    import backend.database as db_module
    test_engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    db_module.engine = test_engine
    db_module.AsyncSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

    yield

    await test_engine.dispose()

    # Teardown: drop all tables so next session starts fresh
    conn = await asyncpg.connect(
        host="localhost", port=5433, user="postgres",
        password="lookatcurryman", database="reacta_test",
    )
    await conn.execute(
        """
        DROP TABLE IF EXISTS transcript_embeddings, clip_tags, clips,
                             tag_definitions, users CASCADE;
        DROP TYPE IF EXISTS processing_status, transcript_status, embedding_status CASCADE;
        """
    )
    await conn.close()


@pytest_asyncio.fixture
async def client():
    """Async HTTP client wired directly to the ASGI app."""
    from backend.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_token(client: AsyncClient) -> str:
    """Register a fresh user and return a valid access token."""
    unique = uuid.uuid4().hex[:8]
    await client.post(
        "/api/v1/auth/register",
        json={"username": f"user_{unique}", "email": f"{unique}@test.com", "password": "password123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": f"{unique}@test.com", "password": "password123"},
    )
    return resp.json()["access_token"]


@pytest.fixture(autouse=True)
def mock_embedding(monkeypatch):
    """Replace embedding calls with instant zero-vectors (no model load)."""
    from backend.services import embeddings as emb_module

    monkeypatch.setattr(emb_module.embedding_service, "embed", lambda text: [0.0] * 384)
    monkeypatch.setattr(
        emb_module.embedding_service,
        "embed_batch",
        lambda texts: [[0.0] * 384 for _ in texts],
    )


@pytest.fixture(autouse=True)
def mock_ffprobe(monkeypatch):
    """Replace ffprobe+file validation with a no-op that sets duration=3.0."""
    import backend.workers.tasks as tasks_module

    async def _fake_validate(clip, file_path, db):
        from backend.models.clip import ProcessingStatus
        clip.duration_seconds = 3.0
        clip.processing_status = ProcessingStatus.ready
        await db.commit()

    monkeypatch.setattr(tasks_module, "_validate_and_extract_duration", _fake_validate)
