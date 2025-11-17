from __future__ import annotations

import asyncio
import logging
import os

from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapper, Session

from app.models.user_persona_bridge import UserPersonaBridge

logger = logging.getLogger(__name__)


@event.listens_for(UserPersonaBridge, "after_insert")
def create_persona_shared_block_on_user_association(
    mapper: Mapper, connection: Connection, target: UserPersonaBridge
) -> None:
    """
    Create and attach Letta shared memory block when a user is associated with a persona.

    This ensures every persona has a corresponding shared experience block,
    and it gets attached to the user's agent immediately upon association.

    The block is labeled {persona_handle}_service_experience.
    """
    logger.debug("EVENT LISTENER FIRED!")

    from app.core.letta_client import create_letta_client
    from app.models.user import User
    from app.models.persona import Persona
    from app.services.persona_service import get_or_create_persona_shared_block

    session = Session(bind=connection)

    try:
        logger.debug("EVENT: Getting user %s", target.user_id)
        user = session.get(User, target.user_id)

        if not user or not user.letta_agent_id:
            logger.warning(
                "Warning: User has no agent_id, skipping block creation for persona association %s",
                target.id,
            )
            return

        logger.debug("EVENT: Found user with agent_id=%s", user.letta_agent_id)
        persona = session.get(Persona, target.persona_id)

        if not persona:
            logger.warning(
                "Warning: Persona not found for persona association %s", target.id
            )
            return

        logger.debug("EVENT: Found persona %s", persona.persona_handle)
        letta_base_url = os.getenv("LETTA_BASE_URL", "http://localhost:8283")
        letta_token = os.getenv("LETTA_SERVER_PASSWORD")

        letta_client = create_letta_client(letta_base_url, letta_token)

        logger.debug("EVENT: Created Letta client")

        try:
            import nest_asyncio

            nest_asyncio.apply()
        except Exception:
            pass

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        logger.debug("EVENT: Loop detected: %s", loop is not None)

        if loop is not None:
            logger.debug("EVENT: Using ThreadPoolExecutor")
            import concurrent.futures

            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        get_or_create_persona_shared_block(
                            letta_client, persona.persona_handle, user.letta_agent_id
                        ),
                    )
                    logger.debug("EVENT: Waiting for future result")
                    result = future.result(timeout=10)
                    logger.debug("EVENT: Got result %s", result.id)
                    logger.debug("EVENT: About to log success message")
                    logger.info(
                        "Created/attached shared memory block for persona %s to agent %s, block_id: %s",
                        persona.persona_handle,
                        user.letta_agent_id,
                        result.id,
                    )
                    logger.debug("EVENT: Finished successfully")
            except Exception as thread_ex:
                logger.error("EVENT ERROR in ThreadPoolExecutor: %s", thread_ex)
                import traceback

                traceback.print_exc()
                raise
        else:
            logger.debug("EVENT: Using asyncio.run directly")
            result = asyncio.run(
                get_or_create_persona_shared_block(
                    letta_client, persona.persona_handle, user.letta_agent_id
                )
            )
            logger.info(
                "Created/attached shared memory block for persona %s to agent %s, block_id: %s",
                persona.persona_handle,
                user.letta_agent_id,
                result.id,
            )
    except Exception as e:
        logger.warning(
            "Warning: Could not create/attach shared block for persona association %s: %s",
            target.id,
            e,
        )
