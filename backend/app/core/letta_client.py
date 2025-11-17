from typing import Optional
from letta_client import Letta
from pydantic import BaseModel
import os


class LettaConfig(BaseModel):
    base_url: str
    token: Optional[str] = None


class LettaAgentResponse(BaseModel):
    agent_id: str
    message_content: str


def create_letta_client(base_url: str, token: Optional[str] = None) -> Letta:
    return Letta(base_url=base_url, token=token)


def _load_pi_agent_config() -> dict:
    """Load and parse the Pi agent configuration from AF file."""
    import json

    current_dir = os.path.dirname(os.path.abspath(__file__))
    agent_file_path = os.path.join(current_dir, "pi_agent_base.af")
    with open(agent_file_path, "r") as f:
        return json.load(f)


def create_pi_agent(
    client: Letta,
    user_display_name: str = "User",
    initial_user_persona_info: str = "",
    shared_block_ids: Optional[list[str]] = None,
    model: Optional[str] = None,
    embedding: Optional[str] = None,
) -> str:
    agent_config = _load_pi_agent_config()

    memory_blocks = []
    for block in agent_config["core_memory"]:
        if block["label"] == "human":
            if initial_user_persona_info:
                value = f"User name: {user_display_name}\n{initial_user_persona_info}"
            else:
                value = f"User name: {user_display_name}\nPersonal facts about the user to be discovered through interaction."
            memory_blocks.append({**block, "value": value})
        else:
            memory_blocks.append(block)

    llm_config = agent_config["llm_config"]
    embedding_config = agent_config["embedding_config"]

    agent_state = client.agents.create(
        memory_blocks=memory_blocks,
        block_ids=shared_block_ids or [],
        model=model or llm_config["model"],
        embedding=embedding
        or f"{embedding_config['embedding_endpoint_type']}/{embedding_config['embedding_model']}",
        context_window_limit=llm_config["context_window"],
        system=agent_config["system"],
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

    message_content = (
        assistant_messages[0].content if assistant_messages else "No response"
    )

    return LettaAgentResponse(agent_id=agent_id, message_content=message_content)
