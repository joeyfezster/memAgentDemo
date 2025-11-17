from __future__ import annotations

import logging

import pytest

from app.crud.persona import get_user_personas
from app.crud.user import get_user_by_email
from app.db.session import get_session

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_sarah_associated_with_qsr_real_estate(letta_client):
    """Test that Sarah is associated with qsr_real_estate persona after seeding."""
    async for session in get_session():
        sarah = await get_user_by_email(session, "sarah.director@fastfoodchain.com")

        if sarah is None:
            pytest.skip("Sarah not found - seed data not loaded")

        user_personas = await get_user_personas(session, sarah.id)

        persona_handles = [up.persona.persona_handle for up in user_personas]

        assert "qsr_real_estate" in persona_handles

        logger.info("Sarah found: %s", sarah.display_name)
        logger.info("Sarah's personas: %s", persona_handles)
        logger.info("qsr_real_estate persona assigned")

        break


@pytest.mark.asyncio
async def test_shared_blocks_attached_to_sarah_agent(letta_client):
    """Test that Sarah's agent has qsr_real_estate_service_experience block attached."""
    async for session in get_session():
        sarah = await get_user_by_email(session, "sarah.director@fastfoodchain.com")

        if sarah is None or not sarah.letta_agent_id:
            pytest.skip("Sarah or her agent not found")

        agent_blocks = letta_client.agents.blocks.list(agent_id=sarah.letta_agent_id)

        qsr_block = next(
            (
                b
                for b in agent_blocks
                if b.label == "qsr_real_estate_service_experience"
            ),
            None,
        )

        assert qsr_block is not None
        assert "qsr_real_estate" in qsr_block.value

        logger.info("Sarah's agent ID: %s", sarah.letta_agent_id)
        logger.info("Persona block found: %s", qsr_block.label)
        logger.info("Block value: %s...", qsr_block.value[:80])

        break


@pytest.mark.asyncio
async def test_shared_blocks_attached_to_daniel_agent(letta_client):
    """Test that Daniel's agent has tobacco_consumer_insights_service_experience block attached."""
    async for session in get_session():
        daniel = await get_user_by_email(session, "daniel.insights@goldtobacco.com")

        if daniel is None or not daniel.letta_agent_id:
            pytest.skip("Daniel or his agent not found")

        agent_blocks = letta_client.agents.blocks.list(agent_id=daniel.letta_agent_id)

        tobacco_block = next(
            (
                b
                for b in agent_blocks
                if b.label == "tobacco_consumer_insights_service_experience"
            ),
            None,
        )

        assert tobacco_block is not None
        assert "tobacco_consumer_insights" in tobacco_block.value

        logger.info("Daniel's agent ID: %s", daniel.letta_agent_id)
        logger.info("Persona block found: %s", tobacco_block.label)
        logger.info("Block value: %s...", tobacco_block.value[:80])

        break


@pytest.mark.asyncio
async def test_sarah_and_daniel_have_different_persona_blocks(letta_client):
    """Test that Sarah and Daniel have different persona blocks (not shared between personas)."""
    async for session in get_session():
        sarah = await get_user_by_email(session, "sarah@chickfilb.com")
        daniel = await get_user_by_email(session, "daniel.insights@goldtobacco.com")

        if sarah is None or daniel is None:
            pytest.skip("Sarah or Daniel not found")

        if not sarah.letta_agent_id or not daniel.letta_agent_id:
            pytest.skip("Agents not found for Sarah or Daniel")

        sarah_blocks = letta_client.agents.blocks.list(agent_id=sarah.letta_agent_id)
        daniel_blocks = letta_client.agents.blocks.list(agent_id=daniel.letta_agent_id)

        sarah_persona_blocks = [
            b for b in sarah_blocks if "service_experience" in b.label
        ]
        daniel_persona_blocks = [
            b for b in daniel_blocks if "service_experience" in b.label
        ]

        sarah_block_ids = {b.id for b in sarah_persona_blocks}
        daniel_block_ids = {b.id for b in daniel_persona_blocks}

        assert len(sarah_block_ids & daniel_block_ids) == 0

        logger.info(
            "Sarah's persona blocks: %s", [b.label for b in sarah_persona_blocks]
        )
        logger.info(
            "Daniel's persona blocks: %s", [b.label for b in daniel_persona_blocks]
        )
        logger.info("No shared persona blocks between different personas")

        break
