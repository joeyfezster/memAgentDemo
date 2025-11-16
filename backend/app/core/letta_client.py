from typing import Optional

from agent.tools import build_toolkit
from letta_client import Letta
from pydantic import BaseModel


class LettaConfig(BaseModel):
    base_url: str
    token: Optional[str] = None


class LettaAgentResponse(BaseModel):
    agent_id: str
    message_content: str


def create_letta_client(base_url: str, token: Optional[str] = None) -> Letta:
    return Letta(base_url=base_url, token=token)


def create_simple_agent(
    client: Letta,
    memory_blocks: Optional[list[dict]] = None,
    model: str = "openai/gpt-4o-mini",
    embedding: str = "openai/text-embedding-3-small",
    tools: Optional[list[str]] = None,
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
        tools=tools,
    )
    return agent_state.id


def register_mock_tools(client: Letta) -> list[str]:
    registered = []
    for tool in build_toolkit():
        created = client.tools.add(tool=tool)
        registered.append(created.name)
    return registered


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

    message_content = (
        assistant_messages[0].content if assistant_messages else "No response"
    )

    return LettaAgentResponse(agent_id=agent_id, message_content=message_content)
