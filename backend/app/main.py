import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents import get_agent_orchestrator
from app.api.routes import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.seed import seed_personas
from app.db.session import get_engine, get_session_factory

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        session_factory = get_session_factory()
        async with session_factory() as session:
            await seed_personas(session)
        orchestrator = get_agent_orchestrator()
        await orchestrator.bootstrap()
    except Exception as exc:
        logger.error("Database connection failed", exc_info=exc)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.project_name, debug=settings.debug, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app


app = create_app()
