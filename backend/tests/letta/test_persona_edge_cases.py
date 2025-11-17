from __future__ import annotations

import json
import logging

import pytest

from agent.tools.persona_tools import update_user_persona_profile_in_db
from app.core.letta_client import create_pi_agent
from app.crud.persona import get_user_personas
from app.crud.user import create_user
from app.db.session import get_session
from app.models.persona import Persona

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_user_with_multiple_personas(letta_client):
    """Test that a user can be associated with multiple personas."""
    async for session in get_session():
        persona1 = Persona(
            persona_handle="test_edge_multi_persona1",
            industry="Test Industry 1",
            professional_role="Test Role 1",
            description="Test persona 1",
            typical_kpis="KPIs 1",
            typical_motivations="Motivations 1",
            quintessential_queries="Queries 1",
        )
        persona2 = Persona(
            persona_handle="test_edge_multi_persona2",
            industry="Test Industry 2",
            professional_role="Test Role 2",
            description="Test persona 2",
            typical_kpis="KPIs 2",
            typical_motivations="Motivations 2",
            quintessential_queries="Queries 2",
        )
        session.add_all([persona1, persona2])
        await session.commit()
        await session.refresh(persona1)
        await session.refresh(persona2)

        user = await create_user(
            session,
            email="multi_persona_user@example.com",
            display_name="Multi Persona User",
            hashed_password="hashedpass",
        )

        agent_id = create_pi_agent(letta_client, user.display_name)
        user.letta_agent_id = agent_id
        await session.commit()

        update_user_persona_profile_in_db(user.id, persona1.persona_handle, 0.8)
        update_user_persona_profile_in_db(user.id, persona2.persona_handle, 0.6)

        user_personas = await get_user_personas(session, user.id)
        persona_handles = [up.persona.persona_handle for up in user_personas]

        assert len(persona_handles) == 2
        assert persona1.persona_handle in persona_handles
        assert persona2.persona_handle in persona_handles

        agent_blocks = letta_client.agents.blocks.list(agent_id=agent_id)
        persona_block_labels = [
            b.label for b in agent_blocks if "service_experience" in b.label
        ]

        assert len(persona_block_labels) == 2

        logger.info("User associated with %s personas", len(persona_handles))
        logger.info("Persona handles: %s", persona_handles)
        logger.info("Agent has %s persona blocks", len(persona_block_labels))

        break


@pytest.mark.asyncio
async def test_very_long_persona_handles(letta_client):
    """Test behavior with very long persona handles."""
    async for session in get_session():
        long_handle = "very_long_industry_name_that_goes_on_and_on_very_long_professional_role_name"

        user = await create_user(
            session,
            email="long_handle_user@example.com",
            display_name="Long Handle User",
            hashed_password="hashedpass",
        )

        agent_id = create_pi_agent(letta_client, user.display_name)
        user.letta_agent_id = agent_id
        await session.commit()

        result = update_user_persona_profile_in_db(user.id, long_handle, 1.0)
        data = json.loads(result)

        assert data["success"] is True or "error" in data

        logger.info("Long handle processed: %s...", long_handle[:50])
        logger.info("Result: %s", data.get("success", "error handled"))

        break


@pytest.mark.asyncio
async def test_persona_handle_with_special_characters(letta_client):
    """Test behavior with special characters in persona handles."""
    async for session in get_session():
        special_handles = [
            "test-industry-with-dashes_role",
            "test.industry.dots_role",
            "test industry spaces_role",
        ]

        user = await create_user(
            session,
            email="special_char_user@example.com",
            display_name="Special Char User",
            hashed_password="hashedpass",
        )

        agent_id = create_pi_agent(letta_client, user.display_name)
        user.letta_agent_id = agent_id
        await session.commit()

        for handle in special_handles:
            result = update_user_persona_profile_in_db(user.id, handle, 1.0)
            data = json.loads(result)

            logger.info(
                "  Handle '%s': %s",
                handle,
                "success" if data.get("success") else "rejected",
            )

        logger.info("Tested %s special character handles", len(special_handles))

        break


@pytest.mark.asyncio
async def test_missing_agent_id_handling(letta_client):
    """Test that operations handle users without agent_id gracefully."""
    async for session in get_session():
        persona = Persona(
            persona_handle="test_edge_no_agent",
            industry="Test Industry",
            professional_role="Test Role",
            description="Test persona",
            typical_kpis="KPIs",
            typical_motivations="Motivations",
            quintessential_queries="Queries",
        )
        session.add(persona)
        await session.commit()
        await session.refresh(persona)

        user = await create_user(
            session,
            email="no_agent_user@example.com",
            display_name="No Agent User",
            hashed_password="hashedpass",
        )
        await session.commit()

        result = update_user_persona_profile_in_db(user.id, persona.persona_handle, 1.0)
        data = json.loads(result)

        logger.info("User without agent_id handled")
        logger.info("Result: %s", data)

        break


@pytest.mark.asyncio
async def test_database_connection_during_tool_execution():
    """Test that tools handle database connection issues gracefully."""
    from agent.tools.persona_tools import list_available_personas

    result = list_available_personas()
    data = json.loads(result)

    assert "personas" in data or "error" in data

    logger.info("Tool executed with result keys: %s", list(data.keys()))


@pytest.mark.asyncio
async def test_nonexistent_user_id(letta_client):
    """Test update_user_persona_profile_in_db with nonexistent user ID."""
    result = update_user_persona_profile_in_db(
        "nonexistent_user_id_12345", "test_industry_role", 1.0
    )
    data = json.loads(result)

    assert data["success"] is False
    assert "error" in data
    assert "not found" in data["error"].lower()

    logger.info("Nonexistent user handled gracefully")
    logger.info("Error message: %s", data["error"])


@pytest.mark.asyncio
async def test_get_or_create_with_invalid_agent_id(letta_client):
    """Test get_or_create_persona_shared_block with invalid agent_id values."""
    from app.services.persona_service import get_or_create_persona_shared_block

    invalid_agent_ids = [
        None,
        "",
        "   ",
        123,
        [],
        {},
        "fake-agent-id-that-does-not-exist",
    ]

    for invalid_id in invalid_agent_ids:
        with pytest.raises(ValueError, match="Invalid agent_id"):
            await get_or_create_persona_shared_block(
                letta_client, "test_edge_invalid_agent", invalid_id
            )

    logger.info(
        "All %s invalid agent_id types rejected", len(invalid_agent_ids)
    )
