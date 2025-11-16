from __future__ import annotations

import asyncio
from functools import lru_cache

from letta_client import AsyncLetta
from letta_client.environment import LettaEnvironment

from app.agents.backend import AgentBackend, LettaAgentBackend, LocalSimulationBackend
from app.agents.base import AgentProfile, AgentReply, AgentRequestContext, RoutingDecision
from app.agents.profiles import build_agent_profiles
from app.agents.routing import KeywordRoutingModel, RoutingSignalParser
from app.core.config import Settings, get_settings


class AgentOrchestrator:
    def __init__(
        self,
        backend: AgentBackend,
        routing_profile: AgentProfile,
        specialized_profile: AgentProfile,
        generalist_profile: AgentProfile,
        router_model: KeywordRoutingModel,
        signal_parser: RoutingSignalParser,
    ):
        self._backend = backend
        self._routing_profile = routing_profile
        self._specialized_profile = specialized_profile
        self._generalist_profile = generalist_profile
        self._router_model = router_model
        self._signal_parser = signal_parser
        self._route_tokens = {
            "specialized": self._specialized_profile.slug,
            "generalist": self._generalist_profile.slug,
        }
        self._profiles = (
            self._routing_profile,
            self._specialized_profile,
            self._generalist_profile,
        )
        self._profile_map = {profile.slug: profile for profile in self._profiles}
        self._bootstrap_lock = asyncio.Lock()
        self._bootstrapped = False

    async def bootstrap(self) -> None:
        if self._bootstrapped:
            return
        async with self._bootstrap_lock:
            if self._bootstrapped:
                return
            for profile in self._profiles:
                await self._backend.ensure(profile)
            self._bootstrapped = True

    async def route(self, context: AgentRequestContext, message: str) -> AgentReply:
        await self.bootstrap()
        routing_agent = await self._backend.ensure(self._routing_profile)
        routing_result = await self._backend.run(routing_agent, message, context)
        decision = self._resolve_decision(routing_result.text, message)
        target_profile = self._profile_map.get(decision.target_slug, self._generalist_profile)
        target_agent = await self._backend.ensure(target_profile)
        analyst_result = await self._backend.run(target_agent, message, context)
        return AgentReply(
            reply=analyst_result.text,
            agent_slug=target_profile.slug,
            agent_name=target_profile.name,
            reasoning=decision.reason,
        )

    def _resolve_decision(self, payload: str, original_message: str) -> RoutingDecision:
        parsed = self._signal_parser.parse(payload, self._route_tokens)
        if parsed:
            return parsed
        return self._router_model.decide(original_message)

    def profiles(self) -> tuple[AgentProfile, AgentProfile, AgentProfile]:
        return self._profiles


def _build_backend(
    settings: Settings,
    router_model: KeywordRoutingModel,
    routing_profile: AgentProfile,
    specialized_profile: AgentProfile,
    generalist_profile: AgentProfile,
) -> AgentBackend:
    if settings.letta_enabled and settings.letta_api_token:
        base_url = settings.letta_base_url or LettaEnvironment.SELF_HOSTED.value
        client = AsyncLetta(
            base_url=base_url,
            token=settings.letta_api_token,
            project=settings.letta_project_id,
        )
        return LettaAgentBackend(client=client, project_id=settings.letta_project_id)
    return LocalSimulationBackend(
        router_model=router_model,
        routing_slug=routing_profile.slug,
        specialized_slug=specialized_profile.slug,
        generalist_slug=generalist_profile.slug,
    )


@lru_cache
def get_agent_orchestrator() -> AgentOrchestrator:
    settings = get_settings()
    routing, specialized, generalist = build_agent_profiles(settings)
    router_model = KeywordRoutingModel(
        keyword_mapping={specialized.slug: specialized.specialization_keywords},
        default_slug=generalist.slug,
    )
    backend = _build_backend(settings, router_model, routing, specialized, generalist)
    return AgentOrchestrator(
        backend=backend,
        routing_profile=routing,
        specialized_profile=specialized,
        generalist_profile=generalist,
        router_model=router_model,
        signal_parser=RoutingSignalParser(),
    )
