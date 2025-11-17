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
    from app.models.persona import Persona
    from app.crud.persona import get_persona_by_handle

    qsr_persona = await get_persona_by_handle(session, "qsr_real_estate")
    if not qsr_persona:
        qsr_persona = Persona(
            persona_handle="qsr_real_estate",
            industry="QSR",
            professional_role="Real Estate",
            description="Quick Service Restaurant professionals focused on site selection and real estate strategy",
            typical_kpis="Traffic patterns, demographic alignment, competitive density, sales projections per location",
            typical_motivations="Maximize ROI on new locations, minimize cannibalization, optimize market coverage",
            quintessential_queries="Best locations for new stores, trade area analysis, competitor proximity analysis",
        )
        session.add(qsr_persona)

    tobacco_persona = await get_persona_by_handle(session, "tobacco_consumer_insights")
    if not tobacco_persona:
        tobacco_persona = Persona(
            persona_handle="tobacco_consumer_insights",
            industry="Tobacco",
            professional_role="Consumer Insights",
            description="Consumer insights professionals in tobacco industry focusing on market analysis and consumer behavior",
            typical_kpis="Market share by region, consumer demographics, purchase patterns, brand penetration",
            typical_motivations="Understand consumer behavior, optimize marketing spend, identify growth opportunities",
            quintessential_queries="Consumer demographic analysis, competitive market analysis, retail distribution patterns",
        )
        session.add(tobacco_persona)

    await session.commit()
    await session.refresh(qsr_persona)
    await session.refresh(tobacco_persona)

    user_records = load_user_records()
    if not user_records:
        return

    settings = get_settings()
    letta_base_url = os.getenv("LETTA_BASE_URL", "http://localhost:8283")
    letta_token = os.getenv("LETTA_SERVER_PASSWORD")

    letta_client = None
    try:
        letta_client = create_letta_client(letta_base_url, letta_token)
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

    if letta_client and "sarah" in created_users and "daniel" in created_users:
        try:
            from app.crud.persona import get_persona_by_handle, assign_persona_to_user
            from app.services.persona_service import (
                attach_persona_blocks_to_agents_of_users_with_persona_handle,
            )

            sarah = created_users["sarah"]
            daniel = created_users["daniel"]

            await session.refresh(sarah)
            await session.refresh(daniel)

            qsr_persona = await get_persona_by_handle(session, "qsr_real_estate")
            tobacco_persona = await get_persona_by_handle(
                session, "tobacco_consumer_insights"
            )

            if qsr_persona and sarah.letta_agent_id:
                await assign_persona_to_user(session, sarah.id, qsr_persona.id)
                await attach_persona_blocks_to_agents_of_users_with_persona_handle(
                    session, letta_client, "qsr_real_estate"
                )

            if tobacco_persona and daniel.letta_agent_id:
                await assign_persona_to_user(session, daniel.id, tobacco_persona.id)
                await attach_persona_blocks_to_agents_of_users_with_persona_handle(
                    session, letta_client, "tobacco_consumer_insights"
                )

            if sarah.letta_agent_id and daniel.letta_agent_id:
                sarah_conv = await create_conversation(session, user_id=sarah.id)
                daniel_conv = await create_conversation(session, user_id=daniel.id)

                sarah_intro = "Hi! I'm Sarah, Director of Real Estate for a fast-casual chain. I'm exploring how location analytics can help with site selection."
                daniel_intro = "Hey I'm Daniel, a director of consumer insights and activation at a tobacco company. I'm interested in how location data can enhance our marketing strategies."

                sarah_response = send_message_to_agent(
                    letta_client, sarah.letta_agent_id, daniel_intro
                )
                daniel_response = send_message_to_agent(
                    letta_client, daniel.letta_agent_id, sarah_intro
                )

                await create_message(
                    session,
                    conversation_id=sarah_conv.id,
                    role=MessageRole.USER,
                    content=daniel_intro,
                )
                await create_message(
                    session,
                    conversation_id=sarah_conv.id,
                    role=MessageRole.AGENT,
                    content=sarah_response.message_content,
                )

                await create_message(
                    session,
                    conversation_id=daniel_conv.id,
                    role=MessageRole.USER,
                    content=sarah_intro,
                )
                await create_message(
                    session,
                    conversation_id=daniel_conv.id,
                    role=MessageRole.AGENT,
                    content=daniel_response.message_content,
                )

                await session.commit()
                print("Created initial conversation between Sarah and Daniel")
        except Exception as e:
            print(
                f"Warning: Could not create initial conversation between personas: {e}"
            )
