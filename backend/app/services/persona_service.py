from __future__ import annotations

import asyncio
from typing import Dict

from letta_client import Letta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user_persona_bridge import UserPersonaBridge

_persona_locks: Dict[str, asyncio.Lock] = {}


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
    print(
        f"=== get_or_create_persona_shared_block called: persona={persona_handle}, agent={agent_id}\n"
    )

    if not agent_id or not isinstance(agent_id, str) or not agent_id.strip():
        raise ValueError(f"Invalid agent_id: {agent_id}. Must be a non-empty string.")

    print("Validating agent...\n")

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

    print("Agent validated, acquiring lock...\n")

    if persona_handle not in _persona_locks:
        _persona_locks[persona_handle] = asyncio.Lock()

    async with _persona_locks[persona_handle]:
        block_label = f"{persona_handle}_service_experience"

        print(
            f"Lock acquired, searching for existing block with label: {block_label}\n"
        )

        existing_block = None
        try:
            agents = client.agents.list()
            for agent in agents:
                try:
                    agent_blocks = client.agents.blocks.list(agent_id=agent.id)
                    for block in agent_blocks:
                        if block.label == block_label:
                            print(
                                f"Found existing block: {block.id} on agent {agent.id}\n"
                            )
                            existing_block = block
                            break
                except Exception:
                    continue
                if existing_block:
                    break
        except Exception as e:
            print(f"Warning: Could not search for existing blocks: {e}")

        if existing_block:
            # Check if this block is already attached to the target agent
            try:
                target_agent_blocks = client.agents.blocks.list(agent_id=agent_id)
                if existing_block.id in [b.id for b in target_agent_blocks]:
                    print(
                        f"Block {existing_block.id} already attached to target agent {agent_id}\n"
                    )
                    return existing_block
                else:
                    # Attach the existing block to this agent
                    print(
                        f"Attaching existing block {existing_block.id} to target agent {agent_id}\n"
                    )
                    client.agents.blocks.attach(
                        agent_id=agent_id, block_id=existing_block.id
                    )
                    print("Successfully attached existing block to target agent\n")
                    return existing_block
            except Exception as e:
                print(f"Error attaching existing block to agent: {e}\n")
                # If attach fails, continue to create a new block

        print("No existing block found (or failed to attach), creating new one...\n")

        initial_value = f"We have not yet gained any experience commensurate of the specific servicing of queries or analytical flows for {persona_handle} users"

        description = f"Gained experience and/or lessons learned from servicing or responding to queries typical or quintessential of users associated with the {persona_handle} persona. This memory block will be shared, and it is therefore VITAL that you not add any PII or sensitive or proprietary information about any specific user in here, e.g. POIs they're interested in, or particular and specific insights they found useful, but rather information that will help a future agent servicing a similar ask in a different instance for a different user"

        block = client.blocks.create(
            label=block_label, value=initial_value, description=description, limit=8000
        )

        print(f"Created block: {block.id}\n")

        import sys

        print(
            f"DEBUG: Created block {block.id} with label {block_label}",
            file=sys.stderr,
            flush=True,
        )

        try:
            print(f"Attempting to attach block {block.id} to agent {agent_id}...\n")
            client.agents.blocks.attach(agent_id=agent_id, block_id=block.id)
            print(f"Successfully attached block {block.id} to agent {agent_id}\n")

            verify_blocks = client.agents.blocks.list(agent_id=agent_id)
            print(f"Agent now has {len(verify_blocks)} blocks:\n")
            for vb in verify_blocks:
                print(f"  - {vb.label} (id: {vb.id})")
        except Exception as e:
            print(f"ERROR attaching block: {e}\n")

        print(f"Returning newly created block: {block.id}\n")

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

    import sys

    print(
        f"DEBUG: Found {len(users_with_agents)} users with agents for persona {persona_handle}",
        file=sys.stderr,
        flush=True,
    )

    if not users_with_agents:
        return

    first_agent_id = users_with_agents[0].letta_agent_id
    print(
        f"DEBUG: Getting/creating block for persona {persona_handle} with agent {first_agent_id}",
        file=sys.stderr,
        flush=True,
    )
    block = await get_or_create_persona_shared_block(
        client, persona_handle, first_agent_id
    )
    print(
        f"DEBUG: Got block {block.id} for persona {persona_handle}",
        file=sys.stderr,
        flush=True,
    )

    for user in users_with_agents:
        try:
            existing_blocks = client.agents.blocks.list(agent_id=user.letta_agent_id)
            block_ids = [b.id for b in existing_blocks]

            if block.id not in block_ids:
                print(
                    f"DEBUG: Attaching block {block.id} to agent {user.letta_agent_id}",
                    file=sys.stderr,
                    flush=True,
                )
                client.agents.blocks.attach(
                    agent_id=user.letta_agent_id, block_id=block.id
                )
                print(
                    f"DEBUG: Successfully attached block {block.id} to agent {user.letta_agent_id}",
                    file=sys.stderr,
                    flush=True,
                )
            else:
                print(
                    f"DEBUG: Block {block.id} already attached to agent {user.letta_agent_id}",
                    file=sys.stderr,
                    flush=True,
                )
        except Exception as e:
            print(
                f"Warning: Could not attach block to agent {user.letta_agent_id}: {e}"
            )
