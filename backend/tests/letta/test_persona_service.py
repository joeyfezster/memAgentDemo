from __future__ import annotations

import os

import pytest

from app.core.letta_client import create_letta_client, create_pi_agent
from app.crud.persona import assign_persona_to_user
from app.crud.user import create_user
from app.db.session import get_session
from app.models.persona import Persona
from app.services.persona_service import (
    attach_persona_blocks_to_agents_of_users_with_persona_handle,
    get_or_create_persona_shared_block,
)


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
async def test_get_or_create_persona_shared_block_returns_existing_block(letta_client):
    """Test that get_or_create_persona_shared_block returns existing block without modification."""
    persona_handle = "test_industry_test_role_existing"
    agent_id = create_pi_agent(letta_client, "Test Agent for Block Reuse")

    block1 = await get_or_create_persona_shared_block(
        letta_client, persona_handle, agent_id
    )
    original_value = block1.value
    original_id = block1.id

    letta_client.blocks.modify(block_id=block1.id, value="Modified value for testing")

    block2 = await get_or_create_persona_shared_block(
        letta_client, persona_handle, agent_id
    )

    assert block2.id == original_id
    assert block2.value == "Modified value for testing"
    assert block2.value != original_value

    print(f"\n✓ Returned existing block with ID: {block2.id}")
    print(f"✓ Block value was not reset: {block2.value[:50]}...")


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

        print("\n✓ Both agents have persona block attached")
        print(f"✓ Shared block ID: {agent1_shared_block.id}")
        print(f"✓ Block label: {agent1_shared_block.label}")

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

        print(f"\n✓ Idempotence verified: block count unchanged ({block_count_before})")
        print(f"✓ Block IDs unchanged: {block_ids_before}")

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

        print("\n✓ User with agent got block attached")
        print("✓ User without agent was skipped (no error)")

        break
