from __future__ import annotations

import os

import pytest

from app.core.letta_client import create_letta_client
from app.crud.persona import get_user_personas
from app.crud.user import get_user_by_email
from app.db.session import get_session


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
async def test_sarah_associated_with_qsr_real_estate(letta_client):
    """Test that Sarah is associated with qsr_real_estate persona after seeding."""
    async for session in get_session():
        sarah = await get_user_by_email(session, "sarah.director@fastfoodchain.com")

        if sarah is None:
            pytest.skip("Sarah not found - seed data not loaded")

        user_personas = await get_user_personas(session, sarah.id)

        persona_handles = [up.persona.persona_handle for up in user_personas]

        assert "qsr_real_estate" in persona_handles

        print(f"\n✓ Sarah found: {sarah.display_name}")
        print(f"✓ Sarah's personas: {persona_handles}")
        print("✓ qsr_real_estate persona assigned")

        break


@pytest.mark.asyncio
async def test_daniel_associated_with_tobacco_consumer_insights(letta_client):
    """Test that Daniel is associated with tobacco_consumer_insights persona after seeding."""
    async for session in get_session():
        daniel = await get_user_by_email(session, "daniel.insights@goldtobacco.com")

        if daniel is None:
            pytest.skip("Daniel not found - seed data not loaded")

        user_personas = await get_user_personas(session, daniel.id)

        persona_handles = [up.persona.persona_handle for up in user_personas]

        assert "tobacco_consumer_insights" in persona_handles

        print(f"\n✓ Daniel found: {daniel.display_name}")
        print(f"✓ Daniel's personas: {persona_handles}")
        print("✓ tobacco_consumer_insights persona assigned")

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

        print(f"\n✓ Sarah's agent ID: {sarah.letta_agent_id}")
        print(f"✓ Persona block found: {qsr_block.label}")
        print(f"✓ Block value: {qsr_block.value[:80]}...")

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

        print(f"\n✓ Daniel's agent ID: {daniel.letta_agent_id}")
        print(f"✓ Persona block found: {tobacco_block.label}")
        print(f"✓ Block value: {tobacco_block.value[:80]}...")

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

        print(f"\n✓ Sarah's persona blocks: {[b.label for b in sarah_persona_blocks]}")
        print(f"✓ Daniel's persona blocks: {[b.label for b in daniel_persona_blocks]}")
        print("✓ No shared persona blocks between different personas")

        break
