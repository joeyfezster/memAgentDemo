from __future__ import annotations

from app.agents.base import AgentProfile
from app.core.config import Settings


def build_agent_profiles(settings: Settings) -> tuple[AgentProfile, AgentProfile, AgentProfile]:
    routing = AgentProfile(
        slug=settings.letta_routing_agent_identifier,
        name="Routing Analyst",
        description="Evaluates every request and selects the best analyst path",
        system_prompt=(
            "You receive user requests and decide whether the specialized analyst or the generalist analyst should respond. "
            "Answer with 'target=<specialized|generalist> confidence=<0-1> reason=<short rationale>'."
        ),
        tags=("router", "dispatcher", settings.environment),
    )
    specialized = AgentProfile(
        slug=settings.letta_specialized_agent_identifier,
        name="Specialized Analyst",
        description="Delivers quantitative breakdowns and structured analysis",
        system_prompt=(
            "You are a quantitative analyst. Provide step-by-step reasoning, structured breakdowns, and data-aware narratives. "
            "Use bullet lists when presenting multi-step logic and highlight assumptions."
        ),
        tags=("specialized", "analysis", settings.environment),
        specialization_keywords=(
            "analysis",
            "analytics",
            "dataset",
            "metric",
            "kpi",
            "trend",
            "forecast",
            "variance",
            "regression",
            "statistical",
            "distribution",
            "quantitative",
            "table",
            "chart",
        ),
    )
    generalist = AgentProfile(
        slug=settings.letta_generalist_agent_identifier,
        name="Generalist Analyst",
        description="Responds to broad or mixed user questions",
        system_prompt=(
            "You are a generalist product analyst who crafts concise answers across strategy, UX, and execution. "
            "Summaries should be actionable and reference the user's persona when relevant."
        ),
        tags=("generalist", "analysis", settings.environment),
    )
    return routing, specialized, generalist
