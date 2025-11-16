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
    agent_id = create_simple_agent(letta_client)

    assert agent_id is not None
    assert isinstance(agent_id, str)
    assert len(agent_id) > 0

    letta_client.agents.delete(agent_id)


def test_mem_block_impacts_agent_behavior(letta_client):
    memory_blocks = [
        {"label": "human", "value": "The user is testing the agent."},
        {"label": "persona", "value": "I iNtErChAnGe uPpEr cAsE aNd lOwEr CaSeS."},
    ]
    agent_id = create_simple_agent(letta_client, memory_blocks=memory_blocks)

    try:
        message = "respond with 3 words at least 5 chars long each"
        response = send_message_to_agent(letta_client, agent_id, message)

        assert response is not None
        assert response.agent_id == agent_id
        assert isinstance(response.message_content, str)
        assert len(response.message_content) > 0

        longest_word = max(response.message_content.split(), key=len)
        ct_lowercase = sum(1 for c in longest_word if c.islower())
        ct_uppercase = sum(1 for c in longest_word if c.isupper())
        assert (
            ct_lowercase >= 2 and ct_uppercase >= 2
        ), f"Expected at least 2 lowercase and 2 uppercase letters in the longest word but got: {longest_word}"
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
