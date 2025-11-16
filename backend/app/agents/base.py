from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class AgentProfile:
    slug: str
    name: str
    description: str
    system_prompt: str
    tags: tuple[str, ...] = ()
    specialization_keywords: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentRequestContext:
    user_id: str
    persona_handle: str
    display_name: str

    def conversation_key(self, profile: AgentProfile) -> str:
        return f"{self.user_id}:{profile.slug}"


@dataclass
class AgentResult:
    profile: AgentProfile
    text: str
    raw_messages: Sequence[str]


@dataclass
class AgentReply:
    reply: str
    agent_slug: str
    agent_name: str
    reasoning: str


@dataclass
class RoutingDecision:
    target_slug: str
    confidence: float
    reason: str
