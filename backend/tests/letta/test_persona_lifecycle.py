from __future__ import annotations

from asyncio import sleep
import os

import pytest

from app.core.letta_client import create_letta_client, create_pi_agent
from app.crud.persona import assign_persona_to_user
from app.crud.user import create_user
from app.db.session import get_session
from app.models.persona import Persona
from app.services.persona_service import get_or_create_persona_shared_block


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
async def test_after_insert_event_fires_and_creates_block(letta_client):
    """Test that after_insert event fires when UserPersonaBridge created and Letta block is auto-created and attached."""
    async for session in get_session():
        persona_handle = "test_lifecycle_industry_role"

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

        await sleep(2)  # Allow time for async event to process

        agent_blocks = letta_client.agents.blocks.list(agent_id=agent_id)
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

        print(f"\n✓ UserPersonaBridge created for {persona_handle}")
        print("✓ Lifecycle hook triggered")
        print(f"✓ Letta block auto-created and attached: {persona_block.label}")
        print(f"✓ Block value: {persona_block.value[:80]}...")

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

        print(f"\n✓ Block label correct: {block.label}")
        print(f"✓ Block value correct: {block.value[:60]}...")
        print("✓ Block description contains required warnings")
        print(f"✓ Block limit: {block.limit}")

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

            print("\n✓ UserPersonaBridge created for user without agent_id")
            print("✓ Transaction committed successfully despite hook warning")
            print(f"✓ User ID: {user_without_agent.id}")

        except Exception as e:
            pytest.fail(
                f"Transaction should not fail even if user has no agent_id: {e}"
            )

        break
