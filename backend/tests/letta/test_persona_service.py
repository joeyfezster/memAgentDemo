from __future__ import annotations

import logging

import pytest

from app.core.letta_client import create_pi_agent
from app.crud.persona import assign_persona_to_user
from app.crud.user import create_user
from app.db.session import get_session
from app.models.persona import Persona
from app.services.persona_service import (
    attach_persona_blocks_to_agents_of_users_with_persona_handle,
)

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_attach_persona_blocks_attaches_to_all_agents(letta_client):
    """Test that attach_persona_blocks_to_agents_of_users_with_persona_handle attaches blocks to all users' agents."""
    async for session in get_session():
        persona = Persona(
            persona_handle="test_multi_user_persona",
            industry="Test Industry",
            professional_role="Test Role",
            description="Test persona for multi-user attachment",
            typical_kpis="Test KPIs",
            typical_motivations="Test motivations",
            quintessential_queries="Test queries",
        )
        session.add(persona)
        await session.commit()
        await session.refresh(persona)

        user1 = await create_user(
            session,
            email="persona_test_user1@example.com",
            display_name="Persona Test User 1",
            hashed_password="hashedpass",
        )

        user2 = await create_user(
            session,
            email="persona_test_user2@example.com",
            display_name="Persona Test User 2",
            hashed_password="hashedpass",
        )

        agent1_id = create_pi_agent(letta_client, user1.display_name)
        agent2_id = create_pi_agent(letta_client, user2.display_name)

        user1.letta_agent_id = agent1_id
        user2.letta_agent_id = agent2_id
        await session.commit()

        await assign_persona_to_user(session, user1.id, persona.id)
        await assign_persona_to_user(session, user2.id, persona.id)

        await attach_persona_blocks_to_agents_of_users_with_persona_handle(
            session, letta_client, persona.persona_handle
        )

        agent1_blocks = letta_client.agents.blocks.list(agent_id=agent1_id)
        agent2_blocks = letta_client.agents.blocks.list(agent_id=agent2_id)

        agent1_shared_block = next(
            (
                b
                for b in agent1_blocks
                if b.label == f"{persona.persona_handle}_service_experience"
            ),
            None,
        )
        agent2_shared_block = next(
            (
                b
                for b in agent2_blocks
                if b.label == f"{persona.persona_handle}_service_experience"
            ),
            None,
        )

        assert agent1_shared_block is not None
        assert agent2_shared_block is not None
        assert agent1_shared_block.id == agent2_shared_block.id

        logger.info("Both agents have persona block attached")
        logger.info("Shared block ID: %s", agent1_shared_block.id)
        logger.info("Block label: %s", agent1_shared_block.label)

        break


@pytest.mark.asyncio
async def test_attach_persona_blocks_is_idempotent(letta_client):
    """Test that calling attach_persona_blocks multiple times doesn't cause errors or change state."""
    async for session in get_session():
        persona = Persona(
            persona_handle="test_idempotent_persona",
            industry="Test Industry",
            professional_role="Test Role",
            description="Test persona for idempotence",
            typical_kpis="Test KPIs",
            typical_motivations="Test motivations",
            quintessential_queries="Test queries",
        )
        session.add(persona)
        await session.commit()
        await session.refresh(persona)

        user = await create_user(
            session,
            email="idempotent_test_user@example.com",
            display_name="Idempotent Test User",
            hashed_password="hashedpass",
        )

        agent_id = create_pi_agent(letta_client, user.display_name)
        user.letta_agent_id = agent_id
        await session.commit()

        await assign_persona_to_user(session, user.id, persona.id)

        await attach_persona_blocks_to_agents_of_users_with_persona_handle(
            session, letta_client, persona.persona_handle
        )

        blocks_before = letta_client.agents.blocks.list(agent_id=agent_id)
        block_ids_before = {b.id for b in blocks_before}
        block_count_before = len(blocks_before)

        await attach_persona_blocks_to_agents_of_users_with_persona_handle(
            session, letta_client, persona.persona_handle
        )

        blocks_after = letta_client.agents.blocks.list(agent_id=agent_id)
        block_ids_after = {b.id for b in blocks_after}
        block_count_after = len(blocks_after)

        assert block_count_before == block_count_after
        assert block_ids_before == block_ids_after

        logger.info(
            "Idempotence verified: block count unchanged (%s)", block_count_before
        )
        logger.info("Block IDs unchanged: %s", block_ids_before)

        break


@pytest.mark.asyncio
async def test_attach_persona_blocks_skips_users_without_agent_id(letta_client):
    """Test that attach_persona_blocks skips users without letta_agent_id."""
    async for session in get_session():
        persona = Persona(
            persona_handle="test_no_agent_persona",
            industry="Test Industry",
            professional_role="Test Role",
            description="Test persona for users without agents",
            typical_kpis="Test KPIs",
            typical_motivations="Test motivations",
            quintessential_queries="Test queries",
        )
        session.add(persona)
        await session.commit()
        await session.refresh(persona)

        user_with_agent = await create_user(
            session,
            email="user_with_agent@example.com",
            display_name="User With Agent",
            hashed_password="hashedpass",
        )

        user_without_agent = await create_user(
            session,
            email="user_without_agent@example.com",
            display_name="User Without Agent",
            hashed_password="hashedpass",
        )

        agent_id = create_pi_agent(letta_client, user_with_agent.display_name)
        user_with_agent.letta_agent_id = agent_id
        await session.commit()

        await assign_persona_to_user(session, user_with_agent.id, persona.id)
        await assign_persona_to_user(session, user_without_agent.id, persona.id)

        await attach_persona_blocks_to_agents_of_users_with_persona_handle(
            session, letta_client, persona.persona_handle
        )

        agent_blocks = letta_client.agents.blocks.list(agent_id=agent_id)
        agent_shared_block = next(
            (
                b
                for b in agent_blocks
                if b.label == f"{persona.persona_handle}_service_experience"
            ),
            None,
        )

        assert agent_shared_block is not None

        logger.info("User with agent got block attached")
        logger.info("User without agent was skipped (no error)")

        break
