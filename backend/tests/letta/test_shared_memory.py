from __future__ import annotations

import logging

import pytest
from httpx import AsyncClient

from app.main import app

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_shared_memory_blocks_between_agents(letta_client):
    """Test that multiple agents can share the same memory block by ID."""

    shared_block = letta_client.blocks.create(
        label="shared_experience",
        description="Shared learnings and experiences across all Pi agents.",
        value="Initial shared knowledge: Nothing recorded yet.",
        limit=10000,
    )

    logger.info("Created shared block with ID: %s", shared_block.id)
    logger.info("  Initial value: %s...", shared_block.value[:80])

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

        logger.info("Created two agents:")
        logger.info("  Agent 1: %s", agent_1_id)
        logger.info("  Agent 2: %s", agent_2_id)

        letta_client.agents.blocks.attach(agent_id=agent_1_id, block_id=shared_block.id)
        letta_client.agents.blocks.attach(agent_id=agent_2_id, block_id=shared_block.id)

        logger.info("Attached shared block to both agents")

        agent_1_blocks = letta_client.agents.blocks.list(agent_id=agent_1_id)
        agent_2_blocks = letta_client.agents.blocks.list(agent_id=agent_2_id)

        logger.info("Agent 1 blocks:")
        for block in agent_1_blocks:
            logger.info("  - %s (ID: %s)", block.label, block.id)

        logger.info("Agent 2 blocks:")
        for block in agent_2_blocks:
            logger.info("  - %s (ID: %s)", block.label, block.id)

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

        logger.info("VERIFIED: Both agents share the same block")
        logger.info("  Shared block ID: %s", agent_1_shared.id)
        logger.info("  Block content: %s...", agent_1_shared.value[:80])

        updated_value = "Shared knowledge updated: All agents should learn from real estate analysis patterns."
        letta_client.blocks.modify(block_id=shared_block.id, value=updated_value)

        logger.info("Updated shared block content")

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

        logger.info("VERIFIED: Both agents see the updated shared block content")
        logger.info("  Updated content: %s...", agent_1_updated.value[:80])

        agents_with_block = letta_client.blocks.agents.list(block_id=shared_block.id)
        agent_ids_with_block = {agent.id for agent in agents_with_block}

        assert (
            agent_1_id in agent_ids_with_block
        ), "Agent 1 should be listed as using the block"
        assert (
            agent_2_id in agent_ids_with_block
        ), "Agent 2 should be listed as using the block"

        logger.info(
            "VERIFIED: Block reports %s agents attached", len(agents_with_block)
        )
        logger.info("Test complete - shared memory blocks working correctly")
