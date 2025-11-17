from __future__ import annotations

import logging

import pytest
from httpx import AsyncClient

from app.main import app
from app.core.letta_client import send_message_to_agent

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_agent_created_on_registration_and_reused_on_login(letta_client):
    """Test that a Letta agent is created during registration and persists across login."""
    registration_payload = {
        "email": "test_agent_persist@example.com",
        "password": "testpass123",
        "display_name": "Test User",
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        register_response = await client.post(
            "/auth/register", json=registration_payload
        )
        assert (
            register_response.status_code == 201
        ), f"Registration failed: {register_response.text}"

        register_data = register_response.json()
        assert register_data["access_token"]
        assert register_data["user"]["email"] == registration_payload["email"]

        first_agent_id = register_data["user"].get("letta_agent_id")
        assert (
            first_agent_id is not None
        ), "Agent ID must be created during registration when Letta is available"
        assert len(first_agent_id) > 0, "Agent ID should not be empty"

        agent = letta_client.agents.retrieve(first_agent_id)
        assert agent is not None, f"Agent {first_agent_id} should exist in Letta"

        login_response = await client.post(
            "/auth/login",
            json={
                "email": registration_payload["email"],
                "password": registration_payload["password"],
            },
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"

        login_data = login_response.json()
        second_agent_id = login_data["user"].get("letta_agent_id")

        assert second_agent_id == first_agent_id, (
            f"Agent ID should persist across login. "
            f"Registration: {first_agent_id}, Login: {second_agent_id}"
        )


@pytest.mark.asyncio
async def test_agent_remembers_user_interactions(letta_client):
    """Test that agent remembers user details across multiple messages via direct Letta client."""
    registration_payload = {
        "email": "test_memory_persist@example.com",
        "password": "testpass123",
        "display_name": "Memory Test User",
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        register_response = await client.post(
            "/auth/register", json=registration_payload
        )
        assert (
            register_response.status_code == 201
        ), f"Registration failed: {register_response.text}"

        register_data = register_response.json()
        agent_id = register_data["user"]["letta_agent_id"]
        assert agent_id is not None, "Agent ID must be created"

        agent_before = letta_client.agents.retrieve(agent_id)
        initial_memory_blocks = agent_before.memory.blocks
        initial_block_count = len(initial_memory_blocks)

        logger.info("Initial memory blocks count: %s", initial_block_count)
        for block in initial_memory_blocks:
            logger.info("  - %s: %s...", block.label, block.value[:80])

        human_block_before = next(
            (block for block in initial_memory_blocks if block.label == "human"), None
        )
        assert human_block_before is not None, "human block should exist before message"
        assert (
            "pistachio" not in human_block_before.value.lower()
        ), f"human block should not contain 'pistachio' before message. Content: {human_block_before.value}"
        logger.info("Validated 'pistachio' is NOT in human block before message")

        first_response = send_message_to_agent(
            letta_client, agent_id, "My favorite ice cream flavor is pistachio."
        )
        logger.info("First message response: %s", first_response.message_content)

        agent_after_first = letta_client.agents.retrieve(agent_id)
        memory_after_first = agent_after_first.memory.blocks

        logger.info("Memory blocks after first message: %s", len(memory_after_first))
        for block in memory_after_first:
            logger.info("  - %s: %s...", block.label, block.value[:80])

        human_block = next(
            (block for block in memory_after_first if block.label == "human"), None
        )

        assert human_block is not None, "human block should exist for personal facts"

        human_block_updated = "pistachio" in human_block.value.lower()
        logger.info("Human block updated with pistachio: %s", human_block_updated)
        logger.info("Human block content: %s...", human_block.value[:200])

        second_response = send_message_to_agent(
            letta_client, agent_id, "What is my favorite ice cream flavor?"
        )
        logger.info("Second message response: %s", second_response.message_content)

        assert (
            "pistachio" in second_response.message_content.lower()
        ), f"Agent should remember pistachio as favorite flavor. Response: {second_response.message_content}"

        assert (
            human_block_updated
        ), "\n✓ Agent successfully updated human memory block AND recalled user detail"

        logger.info("Test complete - agent memory persistence validated")


@pytest.mark.asyncio
async def test_agent_persona_block_is_read_only(letta_client):
    """Test that agent_persona memory block cannot be modified by the agent."""
    registration_payload = {
        "email": "test_readonly_persona@example.com",
        "password": "testpass123",
        "display_name": "ReadOnly Test User",
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        register_response = await client.post(
            "/auth/register", json=registration_payload
        )
        assert (
            register_response.status_code == 201
        ), f"Registration failed: {register_response.text}"

        register_data = register_response.json()
        agent_id = register_data["user"]["letta_agent_id"]
        assert agent_id is not None, "Agent ID must be created"

        agent_before = letta_client.agents.retrieve(agent_id)
        initial_memory_blocks = agent_before.memory.blocks

        agent_persona_before = next(
            (
                block
                for block in initial_memory_blocks
                if block.label == "agent_persona"
            ),
            None,
        )
        assert agent_persona_before is not None, "agent_persona block should exist"
        initial_agent_persona_value = agent_persona_before.value

        logger.info(
            "Initial agent_persona value: %s...", initial_agent_persona_value[:100]
        )
        logger.info(
            "agent_persona read_only flag: %s",
            getattr(agent_persona_before, "read_only", "not set"),
        )

        response = send_message_to_agent(
            letta_client,
            agent_id,
            "Please update your agent_persona memory block to say you are a specialist in xeno-zoology and your favorite show is 'Alien Worlds'.",
        )
        logger.info("Agent response: %s", response.message_content)

        agent_after = letta_client.agents.retrieve(agent_id)
        memory_after = agent_after.memory.blocks

        agent_persona_after = next(
            (block for block in memory_after if block.label == "agent_persona"), None
        )

        assert agent_persona_after is not None, "agent_persona block should still exist"
        assert agent_persona_after.value == initial_agent_persona_value, (
            f"agent_persona block should not be modified. "
            f"Before: {initial_agent_persona_value[:100]}... "
            f"After: {agent_persona_after.value[:100]}..."
        )

        logger.info(
            "agent_persona block remained unchanged (read-only protection working)"
        )
