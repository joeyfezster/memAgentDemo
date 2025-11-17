from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.letta_client import (
    create_letta_client,
    create_pi_agent,
    send_message_to_agent,
)
from app.core.security import get_password_hash
from app.crud.conversation import create_conversation
from app.crud import message as message_crud
from app.crud.user import get_user_by_email
from app.models.message import MessageRole
from app.models.user import User
from app.models.persona import Persona
from app.models.user_persona_bridge import UserPersonaBridge


@dataclass
class UserRecord:
    email: str
    display_name: str
    persona_handle: str


def _parse_persona_to_user_record(file_path: Path) -> UserRecord | None:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    display_name: str | None = None
    email: str | None = None
    persona_handle: str | None = None
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
            elif persona_handle is None:
                persona_handle = value

        if display_name and email and persona_handle:
            break

    if not (display_name and email and persona_handle):
        return None

    return UserRecord(
        email=email,
        display_name=display_name,
        persona_handle=persona_handle,
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
        print("No user records found to seed")
        return

    settings = get_settings()
    letta_base_url = os.getenv("LETTA_BASE_URL", "http://localhost:8283")
    letta_token = os.getenv("LETTA_SERVER_PASSWORD")
    skip_letta = os.getenv("SKIP_LETTA_USE", "").lower() == "true"

    print(f"Seed starting - SKIP_LETTA_USE: {skip_letta}")

    letta_client = None
    max_retries = 1 if skip_letta else 10
    retry_delay = 0.1 if skip_letta else 1.0

    if not skip_letta:
        for attempt in range(max_retries):
            try:
                letta_client = create_letta_client(letta_base_url, letta_token)
                print(f"Successfully connected to Letta on attempt {attempt + 1}")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(
                        f"Attempt {attempt + 1}/{max_retries}: Letta not ready yet, retrying in {retry_delay}s..."
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 1.5
                else:
                    print(
                        f"Warning: Could not create Letta client after {max_retries} attempts: {e}"
                    )
    else:
        print("TESTING mode: Skipping Letta client creation")

    created_users = {}

    for persona in user_records:
        user = await get_user_by_email(session, persona.email)
        hashed_password = get_password_hash(settings.persona_seed_password)

        persona_record = await session.execute(
            select(Persona).where(Persona.persona_handle == persona.persona_handle)
        )
        persona_obj = persona_record.scalar_one_or_none()

        if not persona_obj:
            persona_obj = Persona(
                persona_handle=persona.persona_handle,
                industry="Location Analytics",
                professional_role=persona.display_name,
                description=f"Demo persona for {persona.display_name}",
                typical_kpis="Demo KPIs",
                typical_motivations="Demo motivations",
                quintessential_queries="Demo queries",
            )
            session.add(persona_obj)
            await session.flush()

        if user:
            user.display_name = persona.display_name
            user.hashed_password = hashed_password

            existing_bridge = await session.execute(
                select(UserPersonaBridge).where(
                    UserPersonaBridge.user_id == user.id,
                    UserPersonaBridge.persona_id == persona_obj.id,
                )
            )
            if not existing_bridge.scalar_one_or_none():
                bridge = UserPersonaBridge(user_id=user.id, persona_id=persona_obj.id)
                session.add(bridge)

            if letta_client and not user.letta_agent_id:
                agent_max_retries = 1 if skip_letta else 5
                agent_retry_delay = 0.1 if skip_letta else 2.0
                for agent_attempt in range(agent_max_retries):
                    try:
                        agent_id = create_pi_agent(
                            letta_client,
                            user_display_name=user.display_name,
                            initial_user_persona_info="",
                        )
                        user.letta_agent_id = agent_id
                        break
                    except Exception as e:
                        if agent_attempt < agent_max_retries - 1:
                            print(
                                f"Attempt {agent_attempt + 1}/{agent_max_retries}: Could not create agent for {user.email}, retrying in {agent_retry_delay}s..."
                            )
                            await asyncio.sleep(agent_retry_delay)
                            agent_retry_delay *= 1.5
                        else:
                            print(
                                f"Warning: Could not create Letta agent for {user.email} after {agent_max_retries} attempts: {e}"
                            )
        else:
            new_user = User(
                email=persona.email,
                display_name=persona.display_name,
                hashed_password=hashed_password,
            )

            session.add(new_user)
            await session.flush()

            bridge = UserPersonaBridge(user_id=new_user.id, persona_id=persona_obj.id)
            session.add(bridge)

            if letta_client:
                agent_max_retries = 1 if skip_letta else 5
                agent_retry_delay = 0.1 if skip_letta else 2.0
                for agent_attempt in range(agent_max_retries):
                    try:
                        agent_id = create_pi_agent(
                            letta_client,
                            user_display_name=new_user.display_name,
                            initial_user_persona_info="",
                        )
                        new_user.letta_agent_id = agent_id
                        break
                    except Exception as e:
                        if agent_attempt < agent_max_retries - 1:
                            print(
                                f"Attempt {agent_attempt + 1}/{agent_max_retries}: Could not create agent for {new_user.email}, retrying in {agent_retry_delay}s..."
                            )
                            await asyncio.sleep(agent_retry_delay)
                            agent_retry_delay *= 1.5
                        else:
                            print(
                                f"Warning: Could not create Letta agent for {new_user.email} after {agent_max_retries} attempts: {e}"
                            )

            session.add(new_user)
            user = new_user

        created_users[persona.display_name.lower()] = user

    await session.commit()

    if (
        not skip_letta
        and letta_client
        and "sarah" in created_users
        and "daniel" in created_users
    ):
        try:
            sarah = created_users["sarah"]
            daniel = created_users["daniel"]

            await session.refresh(sarah)
            await session.refresh(daniel)

            if sarah.letta_agent_id and daniel.letta_agent_id:
                from app.crud.conversation import get_user_conversations

                sarah_existing_convs = await get_user_conversations(session, sarah.id)
                daniel_existing_convs = await get_user_conversations(session, daniel.id)

                sarah_has_messages = False
                for conv in sarah_existing_convs:
                    count = await message_crud.get_message_count(session, conv.id)
                    if count > 0:
                        sarah_has_messages = True
                        break

                daniel_has_messages = False
                for conv in daniel_existing_convs:
                    count = await message_crud.get_message_count(session, conv.id)
                    if count > 0:
                        daniel_has_messages = True
                        break

                sarah_intro = "Hi! I'm Sarah, Director of Real Estate for a fast-casual chain. I'm exploring how location analytics can help with site selection."
                daniel_intro = "Hey I'm Daniel, a director of consumer insights and activation at a tobacco company. I'm interested in how location data can enhance our marketing strategies."

                from app.crud.conversation import update_conversation_title
                from datetime import datetime

                timestamp = datetime.now().strftime("%d-%m:%H:%M")

                max_message_retries = 1 if skip_letta else 10
                message_retry_delay = 0.1 if skip_letta else 3.0

                if not sarah_has_messages:
                    sarah_conv = await create_conversation(session, user_id=sarah.id)
                    sarah_response = None

                    for attempt in range(max_message_retries):
                        try:
                            sarah_response = send_message_to_agent(
                                letta_client, sarah.letta_agent_id, sarah_intro
                            )
                            print(
                                f"Successfully sent message to Sarah's agent on attempt {attempt + 1}"
                            )
                            break
                        except Exception as msg_err:
                            if attempt < max_message_retries - 1:
                                print(
                                    f"Attempt {attempt + 1}/{max_message_retries}: Could not send message to Sarah's agent, retrying in {message_retry_delay}s..."
                                )
                                await asyncio.sleep(message_retry_delay)
                                message_retry_delay *= 1.2
                            else:
                                print(
                                    f"Warning: Could not create Sarah's initial conversation after {max_message_retries} attempts: {msg_err}"
                                )

                    if sarah_response:
                        await message_crud.create_message(
                            session,
                            conversation_id=sarah_conv.id,
                            role=MessageRole.USER,
                            content=sarah_intro,
                        )
                        await message_crud.create_message(
                            session,
                            conversation_id=sarah_conv.id,
                            role=MessageRole.AGENT,
                            content=sarah_response.message_content,
                        )
                        await update_conversation_title(
                            session, sarah_conv.id, f"Hi! I'm Sarah 17-{timestamp}"
                        )
                        await session.commit()
                        print("Created initial conversation for Sarah")
                else:
                    print("Sarah already has messages, skipping")

                message_retry_delay = 0.1 if skip_letta else 3.0
                if not daniel_has_messages:
                    daniel_conv = await create_conversation(session, user_id=daniel.id)
                    daniel_response = None

                    for attempt in range(max_message_retries):
                        try:
                            daniel_response = send_message_to_agent(
                                letta_client, daniel.letta_agent_id, daniel_intro
                            )
                            print(
                                f"Successfully sent message to Daniel's agent on attempt {attempt + 1}"
                            )
                            break
                        except Exception as msg_err:
                            if attempt < max_message_retries - 1:
                                print(
                                    f"Attempt {attempt + 1}/{max_message_retries}: Could not send message to Daniel's agent, retrying in {message_retry_delay}s..."
                                )
                                await asyncio.sleep(message_retry_delay)
                                message_retry_delay *= 1.2
                            else:
                                print(
                                    f"Warning: Could not create Daniel's initial conversation after {max_message_retries} attempts: {msg_err}"
                                )

                    if daniel_response:
                        await message_crud.create_message(
                            session,
                            conversation_id=daniel_conv.id,
                            role=MessageRole.USER,
                            content=daniel_intro,
                        )
                        await message_crud.create_message(
                            session,
                            conversation_id=daniel_conv.id,
                            role=MessageRole.AGENT,
                            content=daniel_response.message_content,
                        )
                        await update_conversation_title(
                            session, daniel_conv.id, f"Hey I'm Daniel 17-{timestamp}"
                        )
                        await session.commit()
                        print("Created initial conversation for Daniel")
                else:
                    print("Daniel already has messages, skipping")
        except Exception as e:
            print(
                f"Warning: Could not create initial conversation between personas: {e}"
            )
