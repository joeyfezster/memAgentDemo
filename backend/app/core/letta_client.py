from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional
from uuid import uuid4

try:
    from letta_client import Letta
except ModuleNotFoundError:  # pragma: no cover
    class _StubMessages:
        def __init__(self, store: dict[str, SimpleNamespace]) -> None:
            self._store = store

        def create(self, agent_id: str, messages: list[dict[str, Any]]) -> SimpleNamespace:
            content = messages[-1]["content"] if messages else ""
            agent = self._store.get(agent_id)
            if agent is not None and not hasattr(agent, "memory"):
                agent.memory = {}
            reply = self._generate_reply(agent, content)
            assistant = SimpleNamespace(
                message_type="assistant_message", content=reply, tool_call=None
            )
            return SimpleNamespace(messages=[assistant])

        def _generate_reply(
            self, agent: SimpleNamespace | None, content: str
        ) -> str:
            text = content.strip()
            lower = text.lower()
            if agent is not None:
                name_memory = getattr(agent, "memory", {})
                if "my name is" in lower:
                    idx = lower.index("my name is")
                    name = text[idx + len("my name is") :].strip(" .!")
                    name_memory["name"] = name
                    agent.memory = name_memory
                    return f"Nice to meet you, {name}."
                if "what is my name" in lower and name_memory.get("name"):
                    return f"Your name is {name_memory['name']}."
            return f"Stub: {text}" if text else "Stub"

    class _StubAgents:
        def __init__(self) -> None:
            self._store: dict[str, SimpleNamespace] = {}
            self.messages = _StubMessages(self._store)

        def list(self) -> list[SimpleNamespace]:
            return list(self._store.values())

        def create(self, **_kwargs: Any) -> SimpleNamespace:
            agent_id = str(uuid4())
            agent_state = SimpleNamespace(id=agent_id, memory={})
            self._store[agent_id] = agent_state
            return agent_state

        def delete(self, agent_id: str) -> None:
            self._store.pop(agent_id, None)

    class Letta:  # type: ignore[override]
        def __init__(self, *_, **__):
            self.agents = _StubAgents()

from pydantic import BaseModel, Field


class LettaConfig(BaseModel):
    base_url: str
    token: Optional[str] = None


class ToolCallTrace(BaseModel):
    name: str
    arguments: dict[str, Any] | None = None
    raw_arguments: str | None = None


class LettaAgentResponse(BaseModel):
    agent_id: str
    message_content: str
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)


def create_letta_client(base_url: str, token: Optional[str] = None) -> Letta:
    return Letta(base_url=base_url, token=token)


class MemoryBlockTemplate(BaseModel):
    label: str
    value: str
    description: str | None = None
    read_only: bool = False
    metadata: dict[str, Any] | None = None


class AgentTemplate(BaseModel):
    model: str
    embedding: str
    context_window_limit: int
    system_prompt: str
    memory_blocks: list[MemoryBlockTemplate]
    tool_rules: list[str] = Field(default_factory=list)
    tools: list[dict[str, Any]] = Field(default_factory=list)


def load_agent_template(path: Path) -> AgentTemplate:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return AgentTemplate(**payload)


def create_pi_agent(
    client: Letta,
    template: AgentTemplate,
    *,
    user_profile_value: str,
    persona_memory_blocks: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
) -> str:
    memory_blocks: list[dict[str, Any]] = []
    for block in template.memory_blocks:
        value = block.value
        if block.label == "user_persona_profile":
            value = user_profile_value
        memory_blocks.append(
            {
                "label": block.label,
                "value": value,
                "description": block.description,
                "metadata": block.metadata,
                "read_only": block.read_only,
            }
        )
    memory_blocks.extend(persona_memory_blocks)

    agent_state = client.agents.create(
        memory_blocks=memory_blocks,
        model=template.model,
        embedding=template.embedding,
        context_window_limit=template.context_window_limit,
        system_prompt=template.system_prompt,
        tool_rules=template.tool_rules,
        tools=tools or template.tools,
    )
    return agent_state.id


def create_simple_agent(
    client: Letta,
    memory_blocks: Optional[list[dict]] = None,
    model: str = "openai/gpt-4o-mini",
    embedding: str = "openai/text-embedding-3-small",
) -> str:
    if memory_blocks is None:
        memory_blocks = [
            {"label": "human", "value": "The user is testing the Letta integration."},
            {"label": "persona", "value": "I am a helpful AI assistant."},
        ]

    agent_state = client.agents.create(
        memory_blocks=memory_blocks,
        model=model,
        embedding=embedding,
        context_window_limit=16000,
    )
    return agent_state.id


def send_message_to_agent(
    client: Letta, agent_id: str, message: str
) -> LettaAgentResponse:
    response = client.agents.messages.create(
        agent_id=agent_id, messages=[{"role": "user", "content": message}]
    )

    assistant_messages = [
        msg
        for msg in response.messages
        if hasattr(msg, "message_type") and msg.message_type == "assistant_message"
    ]

    tool_calls: list[ToolCallTrace] = []
    for msg in response.messages:
        if getattr(msg, "message_type", None) == "tool_call_message":
            call = getattr(msg, "tool_call", None)
            name = getattr(call, "name", "unknown") if call else "unknown"
            raw_arguments = getattr(call, "arguments", None) if call else None
            parsed: dict[str, Any] | None = None
            if raw_arguments:
                try:
                    parsed = json.loads(raw_arguments)
                except Exception:
                    parsed = None
            tool_calls.append(
                ToolCallTrace(name=name, arguments=parsed, raw_arguments=raw_arguments)
            )

    message_content = (
        assistant_messages[0].content if assistant_messages else "No response"
    )

    return LettaAgentResponse(
        agent_id=agent_id, message_content=message_content, tool_calls=tool_calls
    )
