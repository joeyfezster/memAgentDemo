from __future__ import annotations

import asyncio
import os

from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapper, Session

from app.models.user_persona_bridge import UserPersonaBridge


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
    import sys

    print("EVENT LISTENER FIRED!", file=sys.stderr, flush=True)

    from app.core.letta_client import create_letta_client
    from app.models.user import User
    from app.models.persona import Persona
    from app.services.persona_service import get_or_create_persona_shared_block

    session = Session(bind=connection)

    try:
        print(f"EVENT: Getting user {target.user_id}", file=sys.stderr, flush=True)
        user = session.get(User, target.user_id)

        if not user or not user.letta_agent_id:
            print(
                f"Warning: User has no agent_id, skipping block creation for persona association {target.id}"
            )
            return

        print(
            f"EVENT: Found user with agent_id={user.letta_agent_id}",
            file=sys.stderr,
            flush=True,
        )
        persona = session.get(Persona, target.persona_id)

        if not persona:
            print(f"Warning: Persona not found for persona association {target.id}")
            return

        print(
            f"EVENT: Found persona {persona.persona_handle}",
            file=sys.stderr,
            flush=True,
        )
        letta_base_url = os.getenv("LETTA_BASE_URL", "http://localhost:8283")
        letta_token = os.getenv("LETTA_SERVER_PASSWORD")

        letta_client = create_letta_client(letta_base_url, letta_token)

        print("EVENT: Created Letta client", file=sys.stderr, flush=True)

        try:
            import nest_asyncio

            nest_asyncio.apply()
        except Exception:
            pass

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        print(f"EVENT: Loop detected: {loop is not None}", file=sys.stderr, flush=True)

        if loop is not None:
            print("EVENT: Using ThreadPoolExecutor", file=sys.stderr, flush=True)
            import concurrent.futures

            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        get_or_create_persona_shared_block(
                            letta_client, persona.persona_handle, user.letta_agent_id
                        ),
                    )
                    print(
                        "EVENT: Waiting for future result", file=sys.stderr, flush=True
                    )
                    result = future.result(timeout=10)
                    print(f"EVENT: Got result {result.id}", file=sys.stderr, flush=True)
                    print(
                        "EVENT: About to print success message",
                        file=sys.stderr,
                        flush=True,
                    )
                    print(
                        f"Created/attached shared memory block for persona {persona.persona_handle} to agent {user.letta_agent_id}, block_id: {result.id}",
                        file=sys.stderr,
                        flush=True,
                    )
                    print("EVENT: Finished successfully", file=sys.stderr, flush=True)
            except Exception as thread_ex:
                print(
                    f"EVENT ERROR in ThreadPoolExecutor: {thread_ex}",
                    file=sys.stderr,
                    flush=True,
                )
                import traceback

                traceback.print_exc(file=sys.stderr)
                raise
        else:
            print("EVENT: Using asyncio.run directly", file=sys.stderr, flush=True)
            result = asyncio.run(
                get_or_create_persona_shared_block(
                    letta_client, persona.persona_handle, user.letta_agent_id
                )
            )
            print(
                f"Created/attached shared memory block for persona {persona.persona_handle} to agent {user.letta_agent_id}, block_id: {result.id}"
            )
    except Exception as e:
        print(
            f"Warning: Could not create/attach shared block for persona association {target.id}: {e}"
        )
