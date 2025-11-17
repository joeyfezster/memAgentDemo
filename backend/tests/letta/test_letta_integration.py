import os
import pytest
from app.core.letta_client import (
    create_letta_client,
    create_simple_agent,
    register_mock_tools,
    send_message_to_agent,
)


pytestmark = pytest.mark.usefixtures("skip_persona_seed")


@pytest.fixture(scope="module", autouse=True)
def skip_persona_seed():
    os.environ["SKIP_PERSONA_SEED"] = "1"
    yield
    os.environ.pop("SKIP_PERSONA_SEED", None)


@pytest.fixture
def letta_client():
    """Ensure Letta server is available for tests."""
    base_url = os.getenv("LETTA_BASE_URL", "http://localhost:8283")
    token = os.getenv("LETTA_SERVER_PASSWORD")

    if not base_url or not token:
        pytest.fail(
            "Letta server must be configured. Set LETTA_BASE_URL and LETTA_SERVER_PASSWORD environment variables."
        )

    client = create_letta_client(base_url, token)

    try:
        client.agents.list()
    except Exception as e:
        pytest.fail(
            f"Letta server not accessible at {base_url}. Ensure docker-compose services are running. Error: {e}"
        )

    return client


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


def test_agent_uses_multiple_tools(letta_client):
    """Test that agent can successfully use at least 2 different registered tools."""
    tool_names = register_mock_tools(letta_client)

    assert (
        len(tool_names) >= 2
    ), f"Expected at least 2 tools registered, got {len(tool_names)}"

    memory_blocks = [
        {"label": "human", "limit": 3000, "value": "The user is testing tool usage."},
        {
            "label": "agent_persona",
            "limit": 2000,
            "value": "You are a test assistant. Always use the available tools to answer user questions.",
        },
    ]
    agent_id = create_simple_agent(
        letta_client,
        memory_blocks=memory_blocks,
        tools=tool_names,
    )
    try:
        prompt = (
            "First, search for malls in Paramus, NJ. "
            "Then get the summary for Garden State Plaza for Q1 2024 (January to March 2024)."
        )
        response = letta_client.agents.messages.create(
            agent_id=agent_id,
            messages=[{"role": "user", "content": prompt}],
            include_return_message_types=[
                "tool_call_message",
                "tool_return_message",
                "assistant_message",
            ],
        )

        tool_calls = [
            _tool_call_name(message)
            for message in response.messages
            if getattr(message, "message_type", "") == "tool_call_message"
        ]
        tool_calls = [name for name in tool_calls if name]

        unique_tools_used = set(tool_calls)

        assert (
            len(unique_tools_used) >= 2
        ), f"Expected agent to use at least 2 different tools, but it used {len(unique_tools_used)}: {unique_tools_used}"

        assert "search_places" in tool_calls, "Expected agent to call search_places"
        assert (
            "get_place_summary" in tool_calls
        ), "Expected agent to call get_place_summary"

    finally:
        try:
            letta_client.agents.delete(agent_id)
        except Exception:
            pass


def _tool_call_name(message):
    """Extract tool name from a tool call message."""
    tool_call = getattr(message, "tool_call", None)
    if tool_call is None:
        return None
    name = getattr(tool_call, "name", None)
    if name:
        return name
    return None
