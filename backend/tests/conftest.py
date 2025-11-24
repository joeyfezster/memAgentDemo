from __future__ import annotations

import os
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest_asyncio  # noqa: E402
import testing.postgresql  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.seed import seed_user_profiles  # noqa: E402
from app.db.session import get_engine, get_session_factory, init_engine  # noqa: E402

repo_root = project_root.parent
load_dotenv(repo_root / ".env")


@pytest_asyncio.fixture(scope="session", autouse=True)
async def configure_test_environment() -> AsyncGenerator[None, None]:
    postgresql = testing.postgresql.Postgresql()
    os.environ["DATABASE_URL"] = postgresql.url().replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"
    os.environ["PERSONA_SEED_PASSWORD"] = "changeme123"

    get_settings.cache_clear()
    init_engine()

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    session_factory = get_session_factory()
    async with session_factory() as session:
        await seed_user_profiles(session)

    await engine.dispose()

    yield
    get_settings.cache_clear()
    postgresql.stop()
