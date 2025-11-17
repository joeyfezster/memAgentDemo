import os
import pytest
from app.core.letta_client import create_letta_client, create_simple_agent


@pytest.fixture(scope="session", autouse=True)
def enable_letta_for_integration_tests():
    """Enable Letta integration for letta test suite (override root conftest)."""
    # Remove SKIP_LETTA_USE set by root conftest so seed_personas creates agents
    os.environ.pop("SKIP_LETTA_USE", None)
    yield
    # Restore it after tests
    os.environ["SKIP_LETTA_USE"] = "1"


@pytest.fixture
def letta_client():
    """
    Provide a Letta client and automatically clean up any agents created during tests.

    Usage:
        def test_my_feature(letta_client):
            agent = create_simple_agent(letta_client)
            # Test logic...
            # Agent automatically cleaned up after test
    """
    base_url = os.getenv("LETTA_BASE_URL", "http://localhost:8283")
    token = os.getenv("LETTA_SERVER_PASSWORD")

    if not base_url or not token:
        pytest.fail(
            "Letta server must be configured. Set LETTA_BASE_URL and LETTA_SERVER_PASSWORD environment variables."
        )

    client = create_letta_client(base_url, token, timeout=180.0)

    try:
        client.agents.list()
    except Exception as e:
        pytest.fail(
            f"Letta server not accessible at {base_url}. Ensure docker-compose services are running. Error: {e}"
        )

    agents_before = {agent.id for agent in client.agents.list()}

    yield client

    try:
        agents_after = client.agents.list()
        test_created_agents = [
            agent for agent in agents_after if agent.id not in agents_before
        ]
        for agent in test_created_agents:
            try:
                client.agents.delete(agent.id)
            except Exception:
                pass
    except Exception:
        pass


@pytest.fixture
def letta_agent_id(letta_client):
    """
    Create a test agent and automatically clean it up after the test.

    Usage:
        def test_conversation(letta_agent_id):
            # letta_agent_id is already created
            send_message_to_agent(letta_client, letta_agent_id, "Hello")
            # Agent automatically deleted after test
    """
    agent_id = create_simple_agent(letta_client)
    yield agent_id
    try:
        letta_client.agents.delete(agent_id)
    except Exception:
        pass
