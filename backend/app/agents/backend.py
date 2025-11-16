from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict

from letta_client import AsyncLetta
from letta_client.types import LettaResponse, MessageCreate, TextContent

from app.agents.base import AgentProfile, AgentRequestContext, AgentResult
from app.agents.routing import KeywordRoutingModel


def _extract_response_text(payload: LettaResponse) -> list[str]:
    output: list[str] = []
    for message in payload.messages:
        if message.role != "assistant":
            continue
        for content in message.content:
            if isinstance(content, TextContent):
                output.append(content.text)
    return output


@dataclass
class ManagedAgent:
    profile: AgentProfile
    remote_id: str | None


class AgentBackend:
    async def ensure(self, profile: AgentProfile) -> ManagedAgent:
        raise NotImplementedError

    async def run(
        self, agent: ManagedAgent, message: str, context: AgentRequestContext
    ) -> AgentResult:
        raise NotImplementedError


class LettaAgentBackend(AgentBackend):
    def __init__(self, client: AsyncLetta, project_id: str | None):
        self._client = client
        self._project_id = project_id
        self._agents: Dict[str, ManagedAgent] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    async def ensure(self, profile: AgentProfile) -> ManagedAgent:
        if profile.slug in self._agents:
            return self._agents[profile.slug]
        lock = self._locks.setdefault(profile.slug, asyncio.Lock())
        async with lock:
            if profile.slug in self._agents:
                return self._agents[profile.slug]
            tag = f"agent::{profile.slug}"
            existing = await self._client.agents.list(tags=(tag,))
            state = next((item for item in existing if item.metadata and item.metadata.get("slug") == profile.slug), None)
            if not state:
                state = await self._client.agents.create(
                    name=profile.name,
                    system=profile.system_prompt,
                    tags=tuple({*profile.tags, tag}),
                    description=profile.description,
                    metadata={"slug": profile.slug},
                    project_id=self._project_id,
                )
            managed = ManagedAgent(profile=profile, remote_id=state.id)
            self._agents[profile.slug] = managed
            return managed

    async def run(
        self, agent: ManagedAgent, message: str, context: AgentRequestContext
    ) -> AgentResult:
        if not agent.remote_id:
            raise ValueError("Remote agent identifier missing")
        payload = MessageCreate(
            role="user",
            content=[TextContent(text=message)],
            name=context.persona_handle,
            group_id=context.conversation_key(agent.profile),
        )
        response = await self._client.agents.messages.create(
            agent_id=agent.remote_id,
            messages=[payload],
        )
        messages = _extract_response_text(response)
        reply = messages[-1] if messages else ""
        return AgentResult(profile=agent.profile, text=reply, raw_messages=messages)


class LocalSimulationBackend(AgentBackend):
    def __init__(
        self,
        router_model: KeywordRoutingModel,
        routing_slug: str,
        specialized_slug: str,
        generalist_slug: str,
    ):
        self.router_model = router_model
        self.routing_slug = routing_slug
        self.specialized_slug = specialized_slug
        self.generalist_slug = generalist_slug
        self._agents: Dict[str, ManagedAgent] = {}

    async def ensure(self, profile: AgentProfile) -> ManagedAgent:
        if profile.slug not in self._agents:
            self._agents[profile.slug] = ManagedAgent(profile=profile, remote_id=None)
        return self._agents[profile.slug]

    async def run(
        self, agent: ManagedAgent, message: str, context: AgentRequestContext
    ) -> AgentResult:
        if agent.profile.slug == self.routing_slug:
            decision = self.router_model.decide(message)
            route_token = "specialized" if decision.target_slug == self.specialized_slug else "generalist"
            text = f"target={route_token} confidence={decision.confidence:.2f} reason={decision.reason}"
            return AgentResult(profile=agent.profile, text=text, raw_messages=[text])
        prefix = "Specialized" if agent.profile.slug == self.specialized_slug else "Generalist"
        text = f"{prefix} response for {context.display_name}: {message}"
        return AgentResult(profile=agent.profile, text=text, raw_messages=[text])
