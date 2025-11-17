from __future__ import annotations

import asyncio
import logging
from typing import Dict

from letta_client import Letta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user_persona_bridge import UserPersonaBridge

_persona_locks: Dict[str, asyncio.Lock] = {}

logger = logging.getLogger(__name__)


async def get_or_create_persona_shared_block(
    client: Letta, persona_handle: str, agent_id: str
):
    """
    Get or create Letta shared memory block for a persona.

    Block label format: {persona_handle}_service_experience
    If block exists, returns it without modification.
    If block doesn't exist, creates it and immediately attaches to agent_id.

    Uses per-persona locking to prevent race conditions when multiple agents
    try to create the same persona block simultaneously.

    Note: Due to Letta API limitations, blocks.list() only returns blocks attached to agents.
    To find existing unattached blocks, we search through all agents' blocks.

    Args:
        client: Letta client instance
        persona_handle: Persona handle (e.g., 'qsr_real_estate')
        agent_id: Agent ID to attach new block to (if created)

    Returns:
        Block object from Letta

    Raises:
        ValueError: If agent_id is None, empty, invalid, or agent doesn't exist
    """
    logger.debug(
        "=== get_or_create_persona_shared_block called: persona=%s, agent=%s",
        persona_handle,
        agent_id,
    )

    if not agent_id or not isinstance(agent_id, str) or not agent_id.strip():
        raise ValueError(f"Invalid agent_id: {agent_id}. Must be a non-empty string.")

    logger.debug("Validating agent...")

    try:
        agents = client.agents.list()
        if not any(agent.id == agent_id for agent in agents):
            raise ValueError(
                f"Invalid agent_id: {agent_id}. Agent does not exist in Letta."
            )
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(
            f"Invalid agent_id: {agent_id}. Unable to verify agent existence: {e}"
        )

    logger.debug("Agent validated, acquiring lock...")

    if persona_handle not in _persona_locks:
        _persona_locks[persona_handle] = asyncio.Lock()

    async with _persona_locks[persona_handle]:
        block_label = f"{persona_handle}_service_experience"

        logger.debug(
            "Lock acquired, searching for existing block with label: %s",
            block_label,
        )

        existing_block = None
        try:
            agents = client.agents.list()
            for agent in agents:
                try:
                    agent_blocks = client.agents.blocks.list(agent_id=agent.id)
                    for block in agent_blocks:
                        if block.label == block_label:
                            logger.debug(
                                "Found existing block: %s on agent %s",
                                block.id,
                                agent.id,
                            )
                            existing_block = block
                            break
                except Exception:
                    continue
                if existing_block:
                    break
        except Exception as e:
            logger.warning("Warning: Could not search for existing blocks: %s", e)

        if existing_block:
            # Check if this block is already attached to the target agent
            try:
                target_agent_blocks = client.agents.blocks.list(agent_id=agent_id)
                if existing_block.id in [b.id for b in target_agent_blocks]:
                    logger.debug(
                        "Block %s already attached to target agent %s",
                        existing_block.id,
                        agent_id,
                    )
                    return existing_block
                else:
                    # Attach the existing block to this agent
                    logger.debug(
                        "Attaching existing block %s to target agent %s",
                        existing_block.id,
                        agent_id,
                    )
                    client.agents.blocks.attach(
                        agent_id=agent_id, block_id=existing_block.id
                    )
                    logger.debug("Successfully attached existing block to target agent")
                    return existing_block
            except Exception as e:
                logger.error("Error attaching existing block to agent: %s", e)
                # If attach fails, continue to create a new block

        logger.debug("No existing block found (or failed to attach), creating new one...")

        initial_value = f"We have not yet gained any experience commensurate of the specific servicing of queries or analytical flows for {persona_handle} users"

        description = f"Gained experience and/or lessons learned from servicing or responding to queries typical or quintessential of users associated with the {persona_handle} persona. This memory block will be shared, and it is therefore VITAL that you not add any PII or sensitive or proprietary information about any specific user in here, e.g. POIs they're interested in, or particular and specific insights they found useful, but rather information that will help a future agent servicing a similar ask in a different instance for a different user"

        block = client.blocks.create(
            label=block_label, value=initial_value, description=description, limit=8000
        )

        logger.debug("Created block: %s", block.id)

        logger.debug("DEBUG: Created block %s with label %s", block.id, block_label)

        try:
            logger.debug("Attempting to attach block %s to agent %s...", block.id, agent_id)
            client.agents.blocks.attach(agent_id=agent_id, block_id=block.id)
            logger.debug(
                "Successfully attached block %s to agent %s", block.id, agent_id
            )

            verify_blocks = client.agents.blocks.list(agent_id=agent_id)
            logger.debug("Agent now has %s blocks:", len(verify_blocks))
            for vb in verify_blocks:
                logger.debug("  - %s (id: %s)", vb.label, vb.id)
        except Exception as e:
            logger.error("ERROR attaching block: %s", e)

        logger.debug("Returning newly created block: %s", block.id)

        return block


async def attach_persona_blocks_to_agents_of_users_with_persona_handle(
    session: AsyncSession, client: Letta, persona_handle: str
) -> None:
    """
    Attach persona shared block to all agents serving users with this persona.

    This function is idempotent - it safely handles cases where blocks are
    already attached.

    Args:
        session: Database session
        client: Letta client instance
        persona_handle: Persona handle to find users for
    """
    result = await session.execute(
        select(UserPersonaBridge)
        .where(UserPersonaBridge.persona.has(persona_handle=persona_handle))
        .options(selectinload(UserPersonaBridge.user))
    )
    user_persona_bridges = result.scalars().all()

    users_with_agents = [
        bridge.user for bridge in user_persona_bridges if bridge.user.letta_agent_id
    ]

    logger.debug(
        "DEBUG: Found %s users with agents for persona %s",
        len(users_with_agents),
        persona_handle,
    )

    if not users_with_agents:
        return

    first_agent_id = users_with_agents[0].letta_agent_id
    logger.debug(
        "DEBUG: Getting/creating block for persona %s with agent %s",
        persona_handle,
        first_agent_id,
    )
    block = await get_or_create_persona_shared_block(
        client, persona_handle, first_agent_id
    )
    logger.debug(
        "DEBUG: Got block %s for persona %s",
        block.id,
        persona_handle,
    )

    for user in users_with_agents:
        try:
            existing_blocks = client.agents.blocks.list(agent_id=user.letta_agent_id)
            block_ids = [b.id for b in existing_blocks]

            if block.id not in block_ids:
                logger.debug(
                    "DEBUG: Attaching block %s to agent %s",
                    block.id,
                    user.letta_agent_id,
                )
                client.agents.blocks.attach(
                    agent_id=user.letta_agent_id, block_id=block.id
                )
                logger.debug(
                    "DEBUG: Successfully attached block %s to agent %s",
                    block.id,
                    user.letta_agent_id,
                )
            else:
                logger.debug(
                    "DEBUG: Block %s already attached to agent %s",
                    block.id,
                    user.letta_agent_id,
                )
        except Exception as e:
            logger.warning(
                "Warning: Could not attach block to agent %s: %s",
                user.letta_agent_id,
                e,
            )
