from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import Generator
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402
from collections.abc import AsyncGenerator  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.crud import user as user_crud  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.seed import seed_user_profiles  # noqa: E402
from app.db.session import get_engine, get_session_factory, init_engine  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.types import (  # noqa: E402
    AgentResponse,
    AgentResponseMetadata,
    ToolInteraction,
)

repo_root = project_root.parent
load_dotenv(project_root / ".env")


@pytest.fixture(scope="session", autouse=True)
def configure_test_environment() -> Generator[None, None, None]:
    # Use environment variable for database host, default to localhost for CI
    # In Docker/E2E tests, this can be set to "postgres"
    db_host = os.environ.get("TEST_DB_HOST", "localhost")
    db_port = os.environ.get("TEST_DB_PORT", "5432")
    db_url = f"postgresql+asyncpg://postgres:postgres@{db_host}:{db_port}/memagent_test"
    os.environ["DATABASE_URL"] = db_url
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"
    os.environ["PERSONA_SEED_PASSWORD"] = "changeme123"

    get_settings.cache_clear()

    async def create_test_db() -> None:
        admin_url = (
            f"postgresql+asyncpg://postgres:postgres@{db_host}:{db_port}/postgres"
        )
        admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
        async with admin_engine.begin() as conn:
            await conn.execute(text("DROP DATABASE IF EXISTS memagent_test"))
            await conn.execute(text("CREATE DATABASE memagent_test"))
        await admin_engine.dispose()

    asyncio.run(create_test_db())

    init_engine(poolclass=NullPool)

    async def setup_db() -> None:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

        init_engine(poolclass=NullPool)
        engine = get_engine()
        session_factory = get_session_factory()
        async with session_factory() as session:
            await seed_user_profiles(session)
        await engine.dispose()

    asyncio.run(setup_db())

    init_engine(poolclass=NullPool)

    yield

    try:
        engine = get_engine()
        if engine:
            engine.sync_engine.dispose(close=True)
    except Exception:
        pass
    get_settings.cache_clear()


@pytest_asyncio.fixture(scope="function")
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session for tests."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def test_user_sarah(session: AsyncSession) -> User:
    """Provide Sarah test user for tests."""
    user = await user_crud.get_user_by_email(session, "sarah@chickfilb.com")
    if not user:
        raise RuntimeError("Test user not found - seed data may not have loaded")
    return user


@pytest.fixture(scope="function")
def settings():
    """Provide settings for tests."""
    return get_settings()


async def consume_streaming_response(stream_iterator) -> AgentResponse:
    """
    Consume a streaming response from agent_service.stream_response_with_tools()
    and return an AgentResponse object for testing.
    """
    text_chunks = []
    metadata_dict = None

    async for event in stream_iterator:
        event_type = list(event.keys())[0]

        if event_type == "text":
            text_chunks.append(event.get("content", ""))
        elif event_type == "complete":
            metadata_dict = event.get("metadata", {})

    if not metadata_dict:
        raise ValueError("Stream did not complete with metadata")

    tool_interactions = [
        ToolInteraction(**ti) for ti in metadata_dict.get("tool_interactions", [])
    ]

    metadata = AgentResponseMetadata(
        tool_interactions=tool_interactions,
        iteration_count=metadata_dict.get("iteration_count", 0),
        stop_reason=metadata_dict.get("stop_reason", "unknown"),
        warning=metadata_dict.get("warning"),
    )

    return AgentResponse(text="".join(text_chunks), metadata=metadata)
