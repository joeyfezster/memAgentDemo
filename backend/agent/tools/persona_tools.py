from __future__ import annotations

import asyncio
import json
import logging
import os

from letta_client import Letta

logger = logging.getLogger(__name__)


def _run_async(coro):
    """
    Run an async coroutine, handling both fresh and nested event loops.

    This allows tools to work both in Letta's synchronous context and
    in async test environments (pytest-asyncio).
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        import nest_asyncio

        nest_asyncio.apply(loop)
        return asyncio.run(coro)


def _get_db_session():
    """
    Get a database session for tool execution.

    Note: This is a simplified approach for tool database access.
    In production, consider using a connection pool or context manager.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import get_settings

    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    return async_session_maker()


def _get_letta_client() -> Letta:
    """Get Letta client for tool execution."""
    from app.core.letta_client import create_letta_client

    letta_base_url = os.getenv("LETTA_BASE_URL", "http://localhost:8283")
    letta_token = os.getenv("LETTA_SERVER_PASSWORD")
    return create_letta_client(letta_base_url, letta_token)


def list_available_personas() -> str:
    """
    List all available persona handles with their metadata.

    Use this tool to discover what personas exist in the system before
    attempting to associate a user with a persona.

    Personas follow the <industry>_<professional_role> naming convention.
    Examples: qsr_real_estate, tobacco_consumer_insights

    Returns:
        str: JSON string with personas array, taxonomy format, and examples
    """
    from app.crud.persona import list_all_personas

    async def _list():
        session = _get_db_session()
        try:
            personas = await list_all_personas(session)

            personas_data = [
                {
                    "persona_handle": p.persona_handle,
                    "industry": p.industry,
                    "professional_role": p.professional_role,
                    "description": p.description,
                    "typical_kpis": p.typical_kpis,
                    "typical_motivations": p.typical_motivations,
                }
                for p in personas
            ]

            return json.dumps(
                {
                    "personas": personas_data,
                    "taxonomy_format": "<industry>_<professional_role>",
                    "examples": ["qsr_real_estate", "tobacco_consumer_insights"],
                }
            )
        finally:
            await session.close()

    try:
        return _run_async(_list())
    except Exception as e:
        return json.dumps(
            {"personas": [], "error": f"Failed to list personas: {str(e)}"}
        )


def update_user_persona_profile_in_db(
    user_id: str, persona_handle: str, confidence_score: float = 1.0
) -> str:
    """
    Associate a user with a persona and attach shared memory blocks.

    This tool MUST be called before updating the user_persona_profile memory block.

    If the persona_handle doesn't exist but follows the <industry>_<professional_role> format:
    - Creates a new Persona record in the database
    - Triggers creation of shared memory block for the persona
    - Associates the user with the new persona

    If the persona exists:
    - Creates user-persona bridge record
    - Attaches shared persona memory block to the user's agent
    - Attaches block to all other agents serving users with this persona

    Args:
        user_id (str): The ID of the user to associate with the persona
        persona_handle (str): Persona handle following <industry>_<professional_role> format
            Examples: qsr_real_estate, tobacco_consumer_insights, retail_marketing_manager
        confidence_score (float): Confidence score for the persona match (0.0 to 1.0, default 1.0)

    Returns:
        str: JSON string with success status, persona details, and any errors
    """
    from app.crud.persona import get_persona_by_handle, assign_persona_to_user
    from app.crud.user import get_user_by_id
    from app.models.persona import Persona
    from app.services.persona_service import (
        attach_persona_blocks_to_agents_of_users_with_persona_handle,
    )

    async def _update():
        logger.debug(
            "DEBUG TOOL: Starting update for user_id=%s, persona_handle=%s",
            user_id,
            persona_handle,
        )
        session = _get_db_session()
        letta_client = _get_letta_client()

        try:
            user = await get_user_by_id(session, user_id)
            if not user:
                logger.debug("DEBUG TOOL: User not found: %s", user_id)
                return json.dumps({"success": False, "error": "User not found"})

            logger.debug(
                "DEBUG TOOL: Found user %s, agent_id=%s",
                user.id,
                user.letta_agent_id,
            )

            persona = await get_persona_by_handle(session, persona_handle)

            if not persona:
                if "_" not in persona_handle:
                    return json.dumps(
                        {
                            "success": False,
                            "error": f"Persona '{persona_handle}' not found and does not follow <industry>_<professional_role> format",
                        }
                    )

                parts = persona_handle.split("_")
                if len(parts) < 2:
                    return json.dumps(
                        {
                            "success": False,
                            "error": f"Persona handle must follow <industry>_<professional_role> format. Got: {persona_handle}",
                        }
                    )

                industry = parts[0].replace("_", " ").title()
                professional_role = " ".join(parts[1:]).replace("_", " ").title()

                persona = Persona(
                    persona_handle=persona_handle,
                    industry=industry,
                    professional_role=professional_role,
                    description=f"{professional_role} in the {industry} industry",
                    typical_kpis="To be determined through interactions",
                    typical_motivations="To be determined through interactions",
                    quintessential_queries="To be determined through interactions",
                )
                session.add(persona)
                await session.commit()
                await session.refresh(persona)

            await assign_persona_to_user(
                session,
                user_id=user_id,
                persona_id=persona.id,
                confidence_score=confidence_score,
            )

            logger.debug("DEBUG TOOL: Assigned persona to user, now attaching blocks")
            await attach_persona_blocks_to_agents_of_users_with_persona_handle(
                session, letta_client, persona_handle
            )
            logger.debug("DEBUG TOOL: Finished attaching blocks")

            return json.dumps(
                {
                    "success": True,
                    "persona_handle": persona.persona_handle,
                    "industry": persona.industry,
                    "professional_role": persona.professional_role,
                    "confidence_score": confidence_score,
                    "message": "User associated with persona and shared memory blocks attached",
                    "_debug_agent_id": user.letta_agent_id,
                }
            )

        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Failed to update persona profile: {str(e)}",
                }
            )
        finally:
            await session.close()

    try:
        return _run_async(_update())
    except Exception as e:
        return json.dumps(
            {"success": False, "error": f"Failed to execute update: {str(e)}"}
        )
