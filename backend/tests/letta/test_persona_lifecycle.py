from __future__ import annotations

import logging
from asyncio import sleep

import pytest

from app.core.letta_client import create_pi_agent
from app.crud.persona import assign_persona_to_user
from app.crud.user import create_user
from app.db.session import get_session
from app.models.persona import Persona
from app.services.persona_service import get_or_create_persona_shared_block

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_after_insert_event_fires_and_creates_block(letta_client):
    """Test that after_insert event fires when UserPersonaBridge created and Letta block is auto-created and attached."""
    async for session in get_session():
        persona_handle = "test_lifecycle_industry_role"

        all_blocks = letta_client.blocks.list()
        for block in all_blocks:
            if block.label == f"{persona_handle}_service_experience":
                try:
                    letta_client.blocks.delete(block.id)
                except Exception:
                    pass

        persona = Persona(
            persona_handle=persona_handle,
            industry="Test Lifecycle Industry",
            professional_role="Test Lifecycle Role",
            description="Test persona for lifecycle hook",
            typical_kpis="Test KPIs",
            typical_motivations="Test motivations",
            quintessential_queries="Test queries",
        )
        session.add(persona)
        await session.commit()
        await session.refresh(persona)

        user = await create_user(
            session,
            email="lifecycle_test_user@example.com",
            display_name="Lifecycle Test User",
            hashed_password="hashedpass",
        )

        agent_id = create_pi_agent(letta_client, user.display_name)
        user.letta_agent_id = agent_id
        await session.commit()

        await assign_persona_to_user(session, user.id, persona.id)

        await sleep(5)  # Allow time for async event to process

        try:
            all_blocks = letta_client.blocks.list()
            logger.info("All blocks in system: %s", len(all_blocks))
            persona_label = f"{persona_handle}_service_experience"
            matching_blocks = [b for b in all_blocks if b.label == persona_label]
            logger.info(
                "Blocks with label '%s': %s", persona_label, len(matching_blocks)
            )
            for b in matching_blocks:
                logger.info("  - %s (id: %s)", b.label, b.id)
        except Exception as e:
            logger.error("Error listing blocks: %s", e)

        agent_blocks = letta_client.agents.blocks.list(agent_id=agent_id)
        logger.info("Agent %s has %s blocks:", agent_id, len(agent_blocks))
        for b in agent_blocks:
            logger.info("  - %s (id: %s)", b.label, b.id)

        persona_block = next(
            (
                b
                for b in agent_blocks
                if b.label == f"{persona_handle}_service_experience"
            ),
            None,
        )

        assert persona_block is not None
        assert persona_block.label == f"{persona_handle}_service_experience"
        assert persona_handle in persona_block.value

        logger.info("UserPersonaBridge created for %s", persona_handle)
        logger.info("Lifecycle hook triggered")
        logger.info(
            "Letta block auto-created and attached: %s", persona_block.label
        )
        logger.info("Block value: %s...", persona_block.value[:80])

        break


@pytest.mark.asyncio
async def test_lifecycle_hook_creates_correct_block_properties(letta_client):
    """Test that lifecycle hook creates block with correct label, value, and description."""
    async for session in get_session():
        persona_handle = "test_lifecycle_props_industry_role"

        existing_blocks = letta_client.blocks.list()
        for block in existing_blocks:
            if block.label == f"{persona_handle}_service_experience":
                letta_client.blocks.delete(block.id)

        persona = Persona(
            persona_handle=persona_handle,
            industry="Test Props Industry",
            professional_role="Test Props Role",
            description="Test persona for property validation",
            typical_kpis="Test KPIs",
            typical_motivations="Test motivations",
            quintessential_queries="Test queries",
        )
        session.add(persona)
        await session.commit()
        await session.refresh(persona)

        agent_id = create_pi_agent(letta_client, "Test Props Agent")
        block = await get_or_create_persona_shared_block(
            letta_client, persona_handle, agent_id
        )

        assert block.label == f"{persona_handle}_service_experience"
        assert (
            f"We have not yet gained any experience commensurate of the specific servicing of queries or analytical flows for {persona_handle} users"
            == block.value
        )
        assert persona_handle in block.description
        assert "VITAL" in block.description
        assert "PII" in block.description
        assert block.limit == 8000

        logger.info("Block label correct: %s", block.label)
        logger.info("Block value correct: %s...", block.value[:60])
        logger.info("Block description contains required warnings")
        logger.info("Block limit: %s", block.limit)

        break


@pytest.mark.asyncio
async def test_lifecycle_hook_handles_errors_gracefully(letta_client):
    """Test that lifecycle hook handles errors gracefully (e.g., user without agent_id)."""
    async for session in get_session():
        persona = Persona(
            persona_handle="test_lifecycle_error_industry_role",
            industry="Test Error Industry",
            professional_role="Test Error Role",
            description="Test persona for error handling",
            typical_kpis="Test KPIs",
            typical_motivations="Test motivations",
            quintessential_queries="Test queries",
        )
        session.add(persona)
        await session.commit()
        await session.refresh(persona)

        user_without_agent = await create_user(
            session,
            email="lifecycle_error_user@example.com",
            display_name="Lifecycle Error User",
            hashed_password="hashedpass",
        )

        try:
            await assign_persona_to_user(session, user_without_agent.id, persona.id)

            assert user_without_agent.id is not None

            logger.info("UserPersonaBridge created for user without agent_id")
            logger.info("Transaction committed successfully despite hook warning")
            logger.info("User ID: %s", user_without_agent.id)

        except Exception as e:
            pytest.fail(
                f"Transaction should not fail even if user has no agent_id: {e}"
            )

        break
