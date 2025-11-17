from __future__ import annotations

import os

import pytest
from httpx import AsyncClient

from app.main import app
from app.core.letta_client import create_letta_client


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


@pytest.mark.asyncio
async def test_shared_memory_blocks_between_agents(letta_client):
    """Test that multiple agents can share the same memory block by ID."""

    shared_block = letta_client.blocks.create(
        label="shared_experience",
        description="Shared learnings and experiences across all Pi agents.",
        value="Initial shared knowledge: Nothing recorded yet.",
        limit=10000,
    )

    print(f"\n✓ Created shared block with ID: {shared_block.id}")
    print(f"  Initial value: {shared_block.value[:80]}...")

    registration_payload_1 = {
        "email": "shared_agent_user1@example.com",
        "password": "testpass123",
        "display_name": "Shared Agent User 1",
    }

    registration_payload_2 = {
        "email": "shared_agent_user2@example.com",
        "password": "testpass123",
        "display_name": "Shared Agent User 2",
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        register_response_1 = await client.post(
            "/auth/register", json=registration_payload_1
        )
        assert (
            register_response_1.status_code == 201
        ), f"Registration 1 failed: {register_response_1.text}"

        register_response_2 = await client.post(
            "/auth/register", json=registration_payload_2
        )
        assert (
            register_response_2.status_code == 201
        ), f"Registration 2 failed: {register_response_2.text}"

        agent_1_id = register_response_1.json()["user"]["letta_agent_id"]
        agent_2_id = register_response_2.json()["user"]["letta_agent_id"]

        assert agent_1_id is not None, "Agent 1 must be created"
        assert agent_2_id is not None, "Agent 2 must be created"
        assert agent_1_id != agent_2_id, "Agents should have different IDs"

        print("\n✓ Created two agents:")
        print(f"  Agent 1: {agent_1_id}")
        print(f"  Agent 2: {agent_2_id}")

        letta_client.agents.blocks.attach(agent_id=agent_1_id, block_id=shared_block.id)
        letta_client.agents.blocks.attach(agent_id=agent_2_id, block_id=shared_block.id)

        print("\n✓ Attached shared block to both agents")

        agent_1_blocks = letta_client.agents.blocks.list(agent_id=agent_1_id)
        agent_2_blocks = letta_client.agents.blocks.list(agent_id=agent_2_id)

        print("\n✓ Agent 1 blocks:")
        for block in agent_1_blocks:
            print(f"  - {block.label} (ID: {block.id})")

        print("\n✓ Agent 2 blocks:")
        for block in agent_2_blocks:
            print(f"  - {block.label} (ID: {block.id})")

        agent_1_shared = next(
            (b for b in agent_1_blocks if b.label == "shared_experience"), None
        )
        agent_2_shared = next(
            (b for b in agent_2_blocks if b.label == "shared_experience"), None
        )

        assert agent_1_shared is not None, "Agent 1 should have shared_experience block"
        assert agent_2_shared is not None, "Agent 2 should have shared_experience block"

        assert agent_1_shared.id == agent_2_shared.id, (
            f"Both agents should reference the SAME block ID. "
            f"Agent 1: {agent_1_shared.id}, Agent 2: {agent_2_shared.id}"
        )

        assert (
            agent_1_shared.value == agent_2_shared.value
        ), "Both agents should see the same block content"

        print("\n✓ VERIFIED: Both agents share the same block")
        print(f"  Shared block ID: {agent_1_shared.id}")
        print(f"  Block content: {agent_1_shared.value[:80]}...")

        updated_value = "Shared knowledge updated: All agents should learn from real estate analysis patterns."
        letta_client.blocks.modify(block_id=shared_block.id, value=updated_value)

        print("\n✓ Updated shared block content")

        agent_1_updated = letta_client.agents.blocks.retrieve(
            agent_id=agent_1_id, block_label="shared_experience"
        )
        agent_2_updated = letta_client.agents.blocks.retrieve(
            agent_id=agent_2_id, block_label="shared_experience"
        )

        assert (
            agent_1_updated.value == updated_value
        ), "Agent 1 should see updated value"
        assert (
            agent_2_updated.value == updated_value
        ), "Agent 2 should see updated value"
        assert (
            agent_1_updated.value == agent_2_updated.value
        ), "Both agents should see same updated value"

        print("\n✓ VERIFIED: Both agents see the updated shared block content")
        print(f"  Updated content: {agent_1_updated.value[:80]}...")

        agents_with_block = letta_client.blocks.agents.list(block_id=shared_block.id)
        agent_ids_with_block = {agent.id for agent in agents_with_block}

        assert (
            agent_1_id in agent_ids_with_block
        ), "Agent 1 should be listed as using the block"
        assert (
            agent_2_id in agent_ids_with_block
        ), "Agent 2 should be listed as using the block"

        print(f"\n✓ VERIFIED: Block reports {len(agents_with_block)} agents attached")
        print("\n✓ Test complete - shared memory blocks working correctly")
