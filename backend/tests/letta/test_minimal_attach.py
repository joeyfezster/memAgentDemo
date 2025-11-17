"""Minimal test to debug block attachment."""

import pytest
from app.core.letta_client import create_pi_agent
from app.crud.persona import assign_persona_to_user
from app.crud.user import create_user
from app.db.session import get_session
from app.models.persona import Persona
from app.services.persona_service import (
    attach_persona_blocks_to_agents_of_users_with_persona_handle,
)


@pytest.mark.asyncio
async def test_minimal_block_attach(letta_client):
    """Minimal test - create persona, user, agent, assign, attach, check. This is largely a learning and debugging test"""
    async for session in get_session():
        persona = Persona(
            persona_handle="minimal_test_persona",
            industry="Test",
            professional_role="Tester",
            description="Test",
            typical_kpis="Test",
            typical_motivations="Test",
            quintessential_queries="Test",
        )
        session.add(persona)
        await session.commit()
        await session.refresh(persona)

        user = await create_user(
            session,
            email="minimal@test.com",
            display_name="Minimal User",
            hashed_password="pass",
        )
        agent_id = create_pi_agent(letta_client, user.display_name)
        user.letta_agent_id = agent_id
        await session.commit()

        await assign_persona_to_user(session, user.id, persona.id)

        await attach_persona_blocks_to_agents_of_users_with_persona_handle(
            session, letta_client, persona.persona_handle
        )

        blocks = letta_client.agents.blocks.list(agent_id=agent_id)
        persona_block = next(
            (b for b in blocks if "minimal_test_persona" in b.label), None
        )

        print(f"\nAgent ID: {agent_id}")
        print(f"All blocks on agent: {[b.label for b in blocks]}")
        print(f"Persona block: {persona_block}")

        assert (
            persona_block is not None
        ), f"Block not found. Agent has blocks: {[b.label for b in blocks]}"

        break
