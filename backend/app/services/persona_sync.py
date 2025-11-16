from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import get_settings
from app.crud import user as user_crud
from app.crud import persona as persona_crud
from app.db.session import get_session_factory
from app.services.pi_agent import pi_agent_service

logger = logging.getLogger(__name__)


class PersonaSyncWorker:
    def __init__(self) -> None:
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._session_factory: async_sessionmaker | None = None

    def start(self) -> None:
        if self._task or not pi_agent_service.is_configured():
            return
        self._session_factory = get_session_factory()
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if not self._task:
            return
        self._stop_event.set()
        await self._task
        self._task = None

    async def _run(self) -> None:
        settings = get_settings()
        interval = max(60, settings.persona_sync_interval_seconds)
        while not self._stop_event.is_set():
            try:
                await self._sync_once()
            except Exception as exc:
                logger.exception("Persona sync failed", exc_info=exc)
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                continue

    async def _sync_once(self) -> None:
        if not self._session_factory:
            return
        async with self._session_factory() as session:
            users = await user_crud.list_users(session)
            for user in users:
                if not user.letta_agent_id:
                    continue
                profile_value = await pi_agent_service.fetch_user_profile_block(
                    user.letta_agent_id
                )
                if not profile_value:
                    continue
                persona_confidences = self._parse_persona_confidences(profile_value)
                if not persona_confidences:
                    continue
                await persona_crud.sync_user_personas(
                    session, user.id, persona_confidences
                )

    def _parse_persona_confidences(self, raw_value: str) -> dict[str, float]:
        try:
            payload: dict[str, Any] = json.loads(raw_value)
        except json.JSONDecodeError:
            return {}
        personas = payload.get("persona_hypotheses")
        if not isinstance(personas, list):
            return {}
        confidences: dict[str, float] = {}
        for entry in personas:
            if not isinstance(entry, dict):
                continue
            handle = entry.get("handle")
            confidence = entry.get("confidence")
            if isinstance(handle, str) and isinstance(confidence, (int, float)):
                confidences[handle] = float(confidence)
        return confidences


def create_persona_sync_worker() -> PersonaSyncWorker:
    return PersonaSyncWorker()
