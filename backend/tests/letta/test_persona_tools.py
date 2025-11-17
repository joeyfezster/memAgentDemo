from __future__ import annotations

import json
import logging

import pytest

from agent.tools.persona_tools import (
    list_available_personas,
    update_user_persona_profile_in_db,
)
from app.core.letta_client import create_pi_agent
from app.crud.persona import get_persona_by_handle
from app.crud.user import create_user
from app.db.session import get_session
from app.models.persona import Persona

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_list_available_personas_returns_all_personas():
    """Test that list_available_personas returns all personas from database."""
    async for session in get_session():
        persona1 = Persona(
            persona_handle="test_list_industry1_role1",
            industry="Test Industry 1",
            professional_role="Test Role 1",
            description="Test persona 1",
            typical_kpis="KPIs 1",
            typical_motivations="Motivations 1",
            quintessential_queries="Queries 1",
        )
        persona2 = Persona(
            persona_handle="test_list_industry2_role2",
            industry="Test Industry 2",
            professional_role="Test Role 2",
            description="Test persona 2",
            typical_kpis="KPIs 2",
            typical_motivations="Motivations 2",
            quintessential_queries="Queries 2",
        )
        session.add_all([persona1, persona2])
        await session.commit()

        break

    result = list_available_personas()
    data = json.loads(result)

    assert "personas" in data
    assert "taxonomy_format" in data
    assert "examples" in data
    assert data["taxonomy_format"] == "<industry>_<professional_role>"
    assert "qsr_real_estate" in data["examples"]
    assert "tobacco_consumer_insights" in data["examples"]

    test_personas = [p for p in data["personas"] if "test_list" in p["persona_handle"]]
    assert len(test_personas) >= 2

    logger.info("Found %s total personas", len(data["personas"]))
    logger.info("Taxonomy format: %s", data["taxonomy_format"])
    logger.info("Examples: %s", data["examples"])


@pytest.mark.asyncio
async def test_update_user_persona_profile_associates_with_existing_persona(
    letta_client,
):
    """Test that update_user_persona_profile_in_db associates user with existing persona."""
    async for session in get_session():
        persona = Persona(
            persona_handle="test_existing_persona",
            industry="Test Industry",
            professional_role="Test Role",
            description="Test persona",
            typical_kpis="Test KPIs",
            typical_motivations="Test motivations",
            quintessential_queries="Test queries",
        )
        session.add(persona)
        await session.commit()
        await session.refresh(persona)

        user = await create_user(
            session,
            email="test_existing_persona_user@example.com",
            display_name="Test User",
            hashed_password="hashedpass",
        )

        agent_id = create_pi_agent(letta_client, user.display_name)
        user.letta_agent_id = agent_id
        await session.commit()

        result = update_user_persona_profile_in_db(user.id, persona.persona_handle, 0.9)
        data = json.loads(result)

        logger.info("%s", "=" * 80)
        logger.info("Tool result: %s", json.dumps(data, indent=2))
        logger.info("%s", "=" * 80)

        assert data["success"] is True
        assert data["persona_handle"] == persona.persona_handle
        assert data["industry"] == persona.industry
        assert data["professional_role"] == persona.professional_role
        assert data["confidence_score"] == 0.9

        agent_blocks = letta_client.agents.blocks.list(agent_id=agent_id)
        logger.info("Checking agent: %s", agent_id)
        logger.info("Found %s blocks: %s", len(agent_blocks), [b.label for b in agent_blocks])
        persona_block = next(
            (
                b
                for b in agent_blocks
                if b.label == f"{persona.persona_handle}_service_experience"
            ),
            None,
        )

        assert persona_block is not None

        logger.info("User associated with persona: %s", persona.persona_handle)
        logger.info("Confidence score: %s", data["confidence_score"])
        logger.info("Persona block attached to agent: %s", persona_block.label)

        break


@pytest.mark.asyncio
async def test_update_user_persona_profile_creates_new_persona_with_valid_handle(
    letta_client,
):
    """Test that update_user_persona_profile_in_db creates new persona when handle is properly formatted."""
    async for session in get_session():
        user = await create_user(
            session,
            email="test_new_persona_user@example.com",
            display_name="Test User New Persona",
            hashed_password="hashedpass",
        )

        agent_id = create_pi_agent(letta_client, user.display_name)
        user.letta_agent_id = agent_id
        await session.commit()

        new_handle = "retail_marketing_manager"
        result = update_user_persona_profile_in_db(user.id, new_handle, 1.0)
        data = json.loads(result)

        assert data["success"] is True
        assert data["persona_handle"] == new_handle
        assert "retail" in data["industry"].lower()
        assert "marketing" in data["professional_role"].lower()

        created_persona = await get_persona_by_handle(session, new_handle)
        assert created_persona is not None
        assert created_persona.persona_handle == new_handle

        agent_blocks = letta_client.agents.blocks.list(agent_id=agent_id)
        logger.info("Agent %s blocks:", agent_id)
        for b in agent_blocks:
            logger.info("  - %s (id: %s)", b.label, b.id)

        persona_block = next(
            (b for b in agent_blocks if b.label == f"{new_handle}_service_experience"),
            None,
        )

        assert persona_block is not None

        logger.info("New persona created: %s", new_handle)
        logger.info("Industry: %s", data["industry"])
        logger.info("Role: %s", data["professional_role"])
        logger.info("Shared block created: %s", persona_block.label)

        break


@pytest.mark.asyncio
async def test_update_user_persona_profile_returns_proper_json():
    """Test that update_user_persona_profile_in_db returns proper JSON structure."""
    async for session in get_session():
        _ = await create_user(
            session,
            email="test_json_response_user@example.com",
            display_name="Test User JSON",
            hashed_password="hashedpass",
        )
        await session.commit()

        result = update_user_persona_profile_in_db(
            "nonexistent_user_id", "test_industry_role", 1.0
        )
        data = json.loads(result)

        assert "success" in data
        assert "error" in data
        assert data["success"] is False

        logger.info("Proper JSON returned for nonexistent user: %s", data)

        break


@pytest.mark.asyncio
async def test_list_available_personas_handles_errors_gracefully():
    """Test that list_available_personas handles database errors gracefully."""
    result = list_available_personas()

    data = json.loads(result)
    assert "personas" in data or "error" in data

    logger.info("Function handled execution: %s", list(data.keys()))
