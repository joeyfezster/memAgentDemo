from __future__ import annotations

import json
import logging

import pytest

from agent.tools.persona_tools import update_user_persona_profile_in_db
from app.core.letta_client import create_pi_agent
from app.crud.persona import get_persona_by_handle
from app.crud.user import create_user
from app.db.session import get_session
from app.models.persona import Persona
from app.services.persona_service import get_or_create_persona_shared_block

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_two_users_with_same_persona_share_same_block_id(letta_client):
    """Test end-to-end flow: two users associated with same persona share identical block ID."""
    async for session in get_session():
        persona = Persona(
            persona_handle="test_integration_shared_persona",
            industry="Test Industry",
            professional_role="Test Role",
            description="Test persona for integration",
            typical_kpis="Test KPIs",
            typical_motivations="Test motivations",
            quintessential_queries="Test queries",
        )
        session.add(persona)
        await session.commit()
        await session.refresh(persona)

        user1 = await create_user(
            session,
            email="integration_user1@example.com",
            display_name="Integration User 1",
            hashed_password="hashedpass",
        )

        user2 = await create_user(
            session,
            email="integration_user2@example.com",
            display_name="Integration User 2",
            hashed_password="hashedpass",
        )

        agent1_id = create_pi_agent(letta_client, user1.display_name)
        agent2_id = create_pi_agent(letta_client, user2.display_name)

        user1.letta_agent_id = agent1_id
        user2.letta_agent_id = agent2_id
        await session.commit()

        result1 = update_user_persona_profile_in_db(
            user1.id, persona.persona_handle, 1.0
        )
        data1 = json.loads(result1)
        assert data1["success"] is True

        result2 = update_user_persona_profile_in_db(
            user2.id, persona.persona_handle, 1.0
        )
        data2 = json.loads(result2)
        assert data2["success"] is True

        agent1_blocks = letta_client.agents.blocks.list(agent_id=agent1_id)
        agent2_blocks = letta_client.agents.blocks.list(agent_id=agent2_id)

        agent1_persona_block = next(
            (
                b
                for b in agent1_blocks
                if b.label == f"{persona.persona_handle}_service_experience"
            ),
            None,
        )
        agent2_persona_block = next(
            (
                b
                for b in agent2_blocks
                if b.label == f"{persona.persona_handle}_service_experience"
            ),
            None,
        )

        assert agent1_persona_block is not None
        assert agent2_persona_block is not None
        assert agent1_persona_block.id == agent2_persona_block.id

        logger.info("Both users associated with persona: %s", persona.persona_handle)
        logger.info("Agent 1 block ID: %s", agent1_persona_block.id)
        logger.info("Agent 2 block ID: %s", agent2_persona_block.id)
        logger.info(
            "Block IDs match: %s",
            agent1_persona_block.id == agent2_persona_block.id,
        )

        break


@pytest.mark.asyncio
async def test_agent_creates_new_persona_dynamically(letta_client):
    """Test end-to-end flow: agent creates new persona with properly formatted handle."""
    async for session in get_session():
        user = await create_user(
            session,
            email="dynamic_persona_user@example.com",
            display_name="Dynamic Persona User",
            hashed_password="hashedpass",
        )

        agent_id = create_pi_agent(letta_client, user.display_name)
        user.letta_agent_id = agent_id
        await session.commit()

        new_handle = "healthcare_data_analyst"

        existing_persona = await get_persona_by_handle(session, new_handle)
        assert existing_persona is None

        result = update_user_persona_profile_in_db(user.id, new_handle, 1.0)
        data = json.loads(result)

        assert data["success"] is True
        assert data["persona_handle"] == new_handle

        created_persona = await get_persona_by_handle(session, new_handle)
        assert created_persona is not None
        assert created_persona.persona_handle == new_handle
        assert created_persona.industry == "Healthcare"
        assert "Data Analyst" in created_persona.professional_role

        agent_blocks = letta_client.agents.blocks.list(agent_id=agent_id)
        persona_block = next(
            (b for b in agent_blocks if b.label == f"{new_handle}_service_experience"),
            None,
        )

        assert persona_block is not None
        assert new_handle in persona_block.value

        logger.info("New persona created dynamically: %s", new_handle)
        logger.info(
            "Persona record in database: %s", created_persona.persona_handle
        )
        logger.info("Shared block created: %s", persona_block.label)
        logger.info("Block attached to agent: %s", agent_id)

        break


@pytest.mark.asyncio
async def test_three_users_same_persona_all_see_shared_updates(letta_client):
    """Test that updates to shared block propagate to all agents with same persona."""
    async for session in get_session():
        persona = Persona(
            persona_handle="test_three_users_persona",
            industry="Test Industry",
            professional_role="Test Role",
            description="Test persona for three users",
            typical_kpis="Test KPIs",
            typical_motivations="Test motivations",
            quintessential_queries="Test queries",
        )
        session.add(persona)
        await session.commit()
        await session.refresh(persona)

        users = []
        agent_ids = []

        for i in range(3):
            user = await create_user(
                session,
                email=f"three_users_test_{i}@example.com",
                display_name=f"Three Users Test {i}",
                hashed_password="hashedpass",
            )
            agent_id = create_pi_agent(letta_client, user.display_name)
            user.letta_agent_id = agent_id
            users.append(user)
            agent_ids.append(agent_id)

        await session.commit()

        for user in users:
            result = update_user_persona_profile_in_db(
                user.id, persona.persona_handle, 1.0
            )
            data = json.loads(result)
            assert data["success"] is True

        shared_block = await get_or_create_persona_shared_block(
            letta_client, persona.persona_handle, agent_ids[0]
        )

        initial_block_ids = []
        for agent_id in agent_ids:
            agent_blocks = letta_client.agents.blocks.list(agent_id=agent_id)
            persona_block = next(
                (
                    b
                    for b in agent_blocks
                    if b.label == f"{persona.persona_handle}_service_experience"
                ),
                None,
            )
            assert persona_block is not None
            initial_block_ids.append(persona_block.id)

        assert len(set(initial_block_ids)) == 1

        updated_value = (
            "Updated experience: All three users should see this shared knowledge."
        )
        letta_client.blocks.modify(block_id=shared_block.id, value=updated_value)

        for agent_id in agent_ids:
            updated_block = letta_client.agents.blocks.retrieve(
                agent_id=agent_id,
                block_label=f"{persona.persona_handle}_service_experience",
            )
            assert updated_block.value == updated_value

        logger.info(
            "All 3 users associated with persona: %s", persona.persona_handle
        )
        logger.info("All agents share same block ID: %s", initial_block_ids[0])
        logger.info("Block updated with new value")
        logger.info("All 3 agents see updated value: %s...", updated_value[:50])

        break


@pytest.mark.asyncio
async def test_update_propagation_across_all_agents(letta_client):
    """Test that block content updates are immediately visible to all agents."""
    async for session in get_session():
        persona = Persona(
            persona_handle="test_propagation_persona",
            industry="Test Industry",
            professional_role="Test Role",
            description="Test persona for propagation",
            typical_kpis="Test KPIs",
            typical_motivations="Test motivations",
            quintessential_queries="Test queries",
        )
        session.add(persona)
        await session.commit()
        await session.refresh(persona)

        user1 = await create_user(
            session,
            email="propagation_user1@example.com",
            display_name="Propagation User 1",
            hashed_password="hashedpass",
        )

        user2 = await create_user(
            session,
            email="propagation_user2@example.com",
            display_name="Propagation User 2",
            hashed_password="hashedpass",
        )

        agent1_id = create_pi_agent(letta_client, user1.display_name)
        agent2_id = create_pi_agent(letta_client, user2.display_name)

        user1.letta_agent_id = agent1_id
        user2.letta_agent_id = agent2_id
        await session.commit()

        update_user_persona_profile_in_db(user1.id, persona.persona_handle, 1.0)
        update_user_persona_profile_in_db(user2.id, persona.persona_handle, 1.0)

        shared_block = await get_or_create_persona_shared_block(
            letta_client, persona.persona_handle, agent1_id
        )

        original_value = shared_block.value

        agent1_block_before = letta_client.agents.blocks.retrieve(
            agent_id=agent1_id,
            block_label=f"{persona.persona_handle}_service_experience",
        )
        agent2_block_before = letta_client.agents.blocks.retrieve(
            agent_id=agent2_id,
            block_label=f"{persona.persona_handle}_service_experience",
        )

        assert agent1_block_before.value == original_value
        assert agent2_block_before.value == original_value

        new_value = "Learned pattern: Site selection benefits from 3-mile trade area analysis for QSR."
        letta_client.blocks.modify(block_id=shared_block.id, value=new_value)

        agent1_block_after = letta_client.agents.blocks.retrieve(
            agent_id=agent1_id,
            block_label=f"{persona.persona_handle}_service_experience",
        )
        agent2_block_after = letta_client.agents.blocks.retrieve(
            agent_id=agent2_id,
            block_label=f"{persona.persona_handle}_service_experience",
        )

        assert agent1_block_after.value == new_value
        assert agent2_block_after.value == new_value
        assert agent1_block_after.value == agent2_block_after.value

        logger.info("Original value: %s...", original_value[:50])
        logger.info("Updated value: %s", new_value)
        logger.info("Agent 1 sees update: %s", agent1_block_after.value == new_value)
        logger.info("Agent 2 sees update: %s", agent2_block_after.value == new_value)
        logger.info(
            "Values match: %s",
            agent1_block_after.value == agent2_block_after.value,
        )

        break
