from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.letta_client import (
    AgentTemplate,
    LettaAgentResponse,
    create_letta_client,
    create_pi_agent,
    load_agent_template,
    send_message_to_agent,
)
from app.models.persona import Persona
from app.models.user import User


class PiAgentService:
    def __init__(self) -> None:
        self._client: Any | None = None
        self._template: AgentTemplate | None = None
        self._template_path = Path(__file__).resolve().parents[1] / "core" / "templates" / "pi_agent_base.af"

    def is_configured(self) -> bool:
        settings = get_settings()
        return bool(settings.letta_base_url)

    def _get_client(self) -> Letta:
        if self._client is None:
            settings = get_settings()
            if not settings.letta_base_url:
                raise RuntimeError("Letta base URL not configured")
            self._client = create_letta_client(
                settings.letta_base_url, settings.letta_server_password
            )
        return self._client

    def _get_template(self) -> AgentTemplate:
        if self._template is None:
            self._template = load_agent_template(self._template_path)
        return self._template

    async def provision_user_agent(
        self, user: User, personas: list[Persona]
    ) -> str:
        client = self._get_client()
        template = self._get_template()
        user_profile_value = self._build_user_profile_value(user, personas)
        persona_blocks = [self._build_persona_block(persona) for persona in personas]
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: create_pi_agent(
                client,
                template,
                user_profile_value=user_profile_value,
                persona_memory_blocks=persona_blocks,
            ),
        )

    async def send_message(self, agent_id: str, message: str) -> LettaAgentResponse:
        client = self._get_client()
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, lambda: send_message_to_agent(client, agent_id, message)
        )

    async def fetch_user_profile_block(self, agent_id: str) -> str | None:
        client = self._get_client()
        loop = asyncio.get_running_loop()

        def _retrieve() -> str | None:
            block = client.agents.blocks.retrieve(
                agent_id=agent_id, block_label="user_persona_profile"
            )
            value = getattr(block, "value", None)
            if isinstance(value, str):
                return value
            if value is None:
                return None
            return json.dumps(value)

        return await loop.run_in_executor(None, _retrieve)

    def _build_persona_block(self, persona: Persona) -> dict[str, str]:
        kpis = "\n".join(f"- {item}" for item in persona.typical_kpis)
        motivations = "\n".join(f"- {item}" for item in persona.typical_motivations)
        queries = "\n".join(f"- {item}" for item in persona.quintessential_queries)
        value = (
            f"Persona handle: {persona.handle}\n"
            f"Role: {persona.professional_role}\n"
            f"Industry: {persona.industry}\n"
            f"Description: {persona.description}\n"
            f"KPIs:\n{kpis}\n"
            f"Motivations:\n{motivations}\n"
            f"Representative queries:\n{queries}"
        )
        return {
            "label": f"persona_experience_{persona.handle}",
            "value": value,
            "description": "Cross-user heuristics for this persona.",
            "read_only": True,
            "metadata": {
                "persona_handle": persona.handle,
                "type": "persona_experience",
            },
        }

    def _build_user_profile_value(
        self, user: User, personas: list[Persona]
    ) -> str:
        now = datetime.now(UTC).isoformat()
        persona_hypotheses = [
            {
                "handle": persona.handle,
                "confidence": 0.95,
                "evidence": "Signup persona handle assignment",
                "last_observed": now,
            }
            for persona in personas
        ]
        payload = {
            "persona_hypotheses": persona_hypotheses,
            "goals": [user.role] if user.role else [],
            "notes": f"Signup email: {user.email}",
        }
        return json.dumps(payload)


pi_agent_service = PiAgentService()
