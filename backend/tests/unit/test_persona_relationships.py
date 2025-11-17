from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.main import app
from app.db.session import get_session
from app.models.persona import Persona
from app.crud.persona import assign_persona_to_user, get_user_personas


@pytest.mark.asyncio
async def test_user_persona_bridge_relationships():
    """Test that User, Persona, and UserPersonaBridge relationships work correctly."""
    registration_payload = {
        "email": "test_persona_bridge@example.com",
        "password": "testpass123",
        "display_name": "Persona Bridge Test User",
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        register_response = await client.post(
            "/auth/register", json=registration_payload
        )
        assert (
            register_response.status_code == 201
        ), f"Registration failed: {register_response.text}"

        register_data = register_response.json()
        user_id = register_data["user"]["id"]

        async for session in get_session():
            from uuid import uuid4

            test_persona = Persona(
                id=str(uuid4()),
                persona_handle="test_real_estate_director",
                persona_character_name="Test Sarah",
                industry="QSR / Fast Casual",
                professional_role="Director of Real Estate",
                description="Test persona for relationship validation",
                typical_kpis="Test KPIs",
                typical_motivations="Test motivations",
                quintessential_queries="Test queries",
            )
            session.add(test_persona)
            await session.commit()
            await session.refresh(test_persona)

            persona_id = test_persona.id

            user_persona_bridge = await assign_persona_to_user(
                session, user_id=user_id, persona_id=persona_id, confidence_score=0.85
            )

            assert (
                user_persona_bridge is not None
            ), "UserPersonaBridge should be created"
            assert (
                user_persona_bridge.user_id == user_id
            ), "Bridge should link to correct user"
            assert (
                user_persona_bridge.persona_id == persona_id
            ), "Bridge should link to correct persona"
            assert (
                user_persona_bridge.confidence_score == 0.85
            ), "Confidence score should be set correctly"

            print(f"\nCreated UserPersonaBridge: {user_persona_bridge.id}")
            print(f"  User ID: {user_persona_bridge.user_id}")
            print(f"  Persona ID: {user_persona_bridge.persona_id}")
            print(f"  Confidence: {user_persona_bridge.confidence_score}")

            user_personas = await get_user_personas(session, user_id=user_id)

            assert (
                len(user_personas) == 1
            ), "User should have exactly one persona assigned"
            assert (
                user_personas[0].persona.persona_handle == "test_real_estate_director"
            ), "Retrieved persona should match assigned persona"
            assert (
                user_personas[0].persona.industry == "QSR / Fast Casual"
            ), "Persona relationship should load full persona details"

            print("\n✓ UserPersonaBridge relationship validated:")
            print(f"  - User has {len(user_personas)} persona(s)")
            print(f"  - Persona handle: {user_personas[0].persona.persona_handle}")
            print(f"  - Persona industry: {user_personas[0].persona.industry}")

            break
