from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.letta_client import (
    create_letta_client,
    create_pi_agent,
    send_message_to_agent,
)
from app.core.security import get_password_hash
from app.crud.conversation import create_conversation
from app.crud.message import create_message
from app.crud.user import get_user_by_email
from app.models.message import MessageRole
from app.models.user import User


@dataclass
class UserRecord:
    email: str
    display_name: str


def _parse_persona_to_user_record(file_path: Path) -> UserRecord | None:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    display_name: str | None = None
    email: str | None = None
    in_handles = False

    for raw_line in lines:
        line = raw_line.strip()
        if line.startswith("# Persona:"):
            content = line.split(":", 1)[1].strip()
            if "–" in content:
                name_part, _ = content.split("–", 1)
                display_name = name_part.strip()
            else:
                display_name = content
        elif line.startswith("## "):
            in_handles = line.lower() == "## demo handle"
        elif in_handles and line.startswith("- "):
            value = line[2:].strip()
            if email is None:
                email = value

        if display_name and email:
            break

    if not (display_name and email):
        return None

    return UserRecord(
        email=email,
        display_name=display_name,
    )


def load_user_records() -> list[UserRecord]:
    repo_root = Path(__file__).resolve().parents[3]
    personas_dir = repo_root / "docs" / "product" / "personas"
    if not personas_dir.exists():
        return []

    records: list[UserRecord] = []
    for file_path in personas_dir.glob("*.md"):
        record = _parse_persona_to_user_record(file_path)
        if record:
            records.append(record)
    return records


async def seed_personas(session: AsyncSession) -> None:
    user_records = load_user_records()
    if not user_records:
        return

    from sqlalchemy import select

    skip_letta = os.getenv("SKIP_LETTA_USE") == "1"
    if skip_letta:
        print("Skipping Letta integration (SKIP_LETTA_USE=1)")

    settings = get_settings()
    letta_base_url = os.getenv("LETTA_BASE_URL", "http://localhost:8283")
    letta_token = os.getenv("LETTA_SERVER_PASSWORD")

    letta_client = None
    if not skip_letta:
        try:
            letta_client = create_letta_client(letta_base_url, letta_token)

            if letta_client:
                result = await session.execute(select(User.letta_agent_id))
                user_agent_ids = {row[0] for row in result if row[0]}

                if user_agent_ids:
                    all_agents = letta_client.list_agents()
                    orphaned_count = 0
                    for agent in all_agents:
                        if agent.id not in user_agent_ids:
                            try:
                                letta_client.delete_agent(agent.id)
                                orphaned_count += 1
                            except Exception as e:
                                print(
                                    f"Warning: Could not delete orphaned agent {agent.id}: {e}"
                                )

                    if orphaned_count > 0:
                        print(
                            f"Cleaned up {orphaned_count} orphaned Letta agents during seed"
                        )
        except Exception as e:
            print(f"Warning: Could not create Letta client: {e}")

    created_users = {}

    for persona in user_records:
        user = await get_user_by_email(session, persona.email)
        hashed_password = get_password_hash(settings.persona_seed_password)

        if user:
            user.display_name = persona.display_name
            user.hashed_password = hashed_password

            if letta_client and not user.letta_agent_id:
                try:
                    agent_id = create_pi_agent(
                        letta_client,
                        user_display_name=user.display_name,
                        initial_user_persona_info="",
                    )
                    user.letta_agent_id = agent_id
                except Exception as e:
                    print(
                        f"Warning: Could not create Letta agent for {user.email}: {e}"
                    )
        else:
            new_user = User(
                email=persona.email,
                display_name=persona.display_name,
                hashed_password=hashed_password,
            )

            if letta_client:
                try:
                    agent_id = create_pi_agent(
                        letta_client,
                        user_display_name=new_user.display_name,
                        initial_user_persona_info="",
                    )
                    new_user.letta_agent_id = agent_id
                except Exception as e:
                    print(
                        f"Warning: Could not create Letta agent for {new_user.email}: {e}"
                    )

            session.add(new_user)
            user = new_user

        created_users[persona.display_name.lower()] = user

    await session.commit()

    if letta_client:
        try:
            sarah = created_users.get("sarah")
            daniel = created_users.get("daniel")
            emma = created_users.get("emma")

            if sarah:
                await session.refresh(sarah)
            if daniel:
                await session.refresh(daniel)
            if emma:
                await session.refresh(emma)

            from app.crud.conversation import get_user_conversations
            from app.crud.message import get_conversation_messages

            if sarah and sarah.letta_agent_id:
                sarah_convs = await get_user_conversations(session, sarah.id)
                sarah_has_messages = False

                if sarah_convs:
                    for conv in sarah_convs:
                        messages = await get_conversation_messages(session, conv.id)
                        if messages:
                            sarah_has_messages = True
                            break

                if not sarah_has_messages:
                    sarah_conv = await create_conversation(session, user_id=sarah.id)

                    sarah_queries = [
                        "Hi! I'm Sarah, Director of Real Estate for a fast-casual chain. I'm exploring how location analytics can help with site selection.",
                        "I need to evaluate a candidate site in Atlanta. Can you help me search for fast-casual restaurants in the Atlanta metro area? I'm particularly interested in QSR locations with strong foot traffic.",
                        "Now I'd like to compare the performance of our top existing locations in Atlanta. Can you analyze visit trends and visitor demographics for the locations you found? I need to see which ones would be good comps for a new site.",
                        "Great! For the top 3 performing locations, can you show me their trade areas? I need to understand the geographic reach and identify any potential cannibalization risks if we open nearby.",
                        "This is helpful. What about the visitor profiles - can you break down the demographics and income levels of visitors to these top locations? I want to make sure our new site will attract the right customer base.",
                    ]

                    for query in sarah_queries:
                        try:
                            response = send_message_to_agent(
                                letta_client, sarah.letta_agent_id, query
                            )

                            await create_message(
                                session,
                                conversation_id=sarah_conv.id,
                                role=MessageRole.USER,
                                content=query,
                            )
                            await create_message(
                                session,
                                conversation_id=sarah_conv.id,
                                role=MessageRole.AGENT,
                                content=response.message_content,
                            )
                            await session.commit()
                        except Exception as e:
                            print(f"Warning: Failed to process query for Sarah: {e}")
                            break

                    print("Created comprehensive interaction sequence for Sarah")
                else:
                    print("Sarah already has messages, skipping")

            if daniel and daniel.letta_agent_id:
                daniel_convs = await get_user_conversations(session, daniel.id)
                daniel_has_messages = False

                if daniel_convs:
                    for conv in daniel_convs:
                        messages = await get_conversation_messages(session, conv.id)
                        if messages:
                            daniel_has_messages = True
                            break

                if not daniel_has_messages:
                    daniel_conv = await create_conversation(session, user_id=daniel.id)

                    daniel_intro = "Hey I'm Daniel, a director of consumer insights and activation at a tobacco company. I'm interested in how location data can enhance our marketing strategies."

                    daniel_response = send_message_to_agent(
                        letta_client, daniel.letta_agent_id, daniel_intro
                    )

                    await create_message(
                        session,
                        conversation_id=daniel_conv.id,
                        role=MessageRole.USER,
                        content=daniel_intro,
                    )
                    await create_message(
                        session,
                        conversation_id=daniel_conv.id,
                        role=MessageRole.AGENT,
                        content=daniel_response.message_content,
                    )

                    await session.commit()
                    print("Created initial conversation for Daniel")
                else:
                    print("Daniel already has messages, skipping")

            if emma and emma.letta_agent_id:
                emma_convs = await get_user_conversations(session, emma.id)
                emma_has_messages = False

                if emma_convs:
                    for conv in emma_convs:
                        messages = await get_conversation_messages(session, conv.id)
                        if messages:
                            emma_has_messages = True
                            break

                if not emma_has_messages:
                    emma_conv = await create_conversation(session, user_id=emma.id)

                    emma_queries = [
                        "Hello! I'm Emma, Director of Real Estate for a regional pizza chain. We're looking to expand into new markets and I could use help with site selection.",
                        "We're considering expansion in the Dallas area. Can you help me find shopping centers and restaurant locations that would be good for a pizza restaurant? I want to understand the competitive landscape.",
                        "Perfect! Now can you show me which of these locations have the strongest visitor patterns? I need to benchmark performance metrics like visit frequency and understand trade area overlap.",
                    ]

                    for query in emma_queries:
                        try:
                            response = send_message_to_agent(
                                letta_client, emma.letta_agent_id, query
                            )

                            await create_message(
                                session,
                                conversation_id=emma_conv.id,
                                role=MessageRole.USER,
                                content=query,
                            )
                            await create_message(
                                session,
                                conversation_id=emma_conv.id,
                                role=MessageRole.AGENT,
                                content=response.message_content,
                            )
                            await session.commit()
                        except Exception as e:
                            print(f"Warning: Failed to process query for Emma: {e}")
                            break

                    print("Created interaction sequence for Emma")
                else:
                    print("Emma already has messages, skipping")

        except Exception as e:
            print(f"Warning: Could not create initial conversations for personas: {e}")
