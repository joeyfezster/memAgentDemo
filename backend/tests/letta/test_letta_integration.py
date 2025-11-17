import os
import pytest
from app.core.letta_client import (
    create_letta_client,
    create_simple_agent,
    send_message_to_agent,
)


@pytest.fixture
def letta_client():
    base_url = os.getenv("LETTA_BASE_URL", "http://localhost:8283")
    token = os.getenv("LETTA_SERVER_PASSWORD")
    return create_letta_client(base_url, token)


@pytest.fixture
def letta_agent_id(letta_client):
    agent_id = create_simple_agent(letta_client)
    yield agent_id
    try:
        letta_client.agents.delete(agent_id)
    except Exception:
        pass


def test_letta_server_connection(letta_client):
    agents = letta_client.agents.list()
    assert agents is not None


def test_create_agent(letta_client):
    agent_id = create_simple_agent(letta_client, model="openai/gpt-4o")

    assert agent_id is not None
    assert isinstance(agent_id, str)
    assert len(agent_id) > 0

    letta_client.agents.delete(agent_id)


@pytest.mark.skip(reason="Local dev only")
def test_mem_block_impacts_agent_behavior(letta_client):
    import subprocess
    import json

    memory_blocks = [
        {"label": "human", "value": "The user is testing the agent."},
        {
            "label": "persona",
            "value": "I ALWAYS respond by putting the word BANANA in my responses.",
        },
    ]
    agent_id = create_simple_agent(
        letta_client, model="openai/gpt-4o", memory_blocks=memory_blocks
    )

    try:
        response = send_message_to_agent(
            letta_client, agent_id, "tell me something interesting"
        )

        preview_payload = {
            "messages": [{"role": "user", "content": "tell me something interesting"}]
        }

        result = subprocess.run(
            [
                "docker",
                "exec",
                "memagent_letta",
                "curl",
                "-s",
                "-X",
                "POST",
                f"http://localhost:8283/v1/agents/{agent_id}/messages/preview-raw-payload",
                "-H",
                "Content-Type: application/json",
                "-d",
                json.dumps(preview_payload),
            ],
            capture_output=True,
            text=True,
        )

        print("\n=== COMPILED CONTEXT WINDOW ===")
        print(result.stdout)
        print("=== END CONTEXT WINDOW ===\n")

        assert "banana" in response.message_content.lower()
    finally:
        try:
            letta_client.agents.delete(agent_id)
        except Exception:
            pass


def test_agent_conversation_continuity(letta_client, letta_agent_id):
    first_message = "My name is Alice."
    first_response = send_message_to_agent(letta_client, letta_agent_id, first_message)
    assert first_response.message_content

    second_message = "What is my name?"
    second_response = send_message_to_agent(
        letta_client, letta_agent_id, second_message
    )
    assert second_response.message_content
    assert "alice" in second_response.message_content.lower()
