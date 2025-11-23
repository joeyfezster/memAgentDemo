from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.crud.user import get_user_by_email
from app.models.user import User
from app.models.conversation import Conversation


@dataclass
class UserRecord:
    email: str
    display_name: str
    role: str | None


def _parse_persona(file_path: Path) -> UserRecord | None:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    display_name: str | None = None
    role: str | None = None
    email: str | None = None
    in_handles = False

    for raw_line in lines:
        line = raw_line.strip()
        if line.startswith("# Persona:"):
            content = line.split(":", 1)[1].strip()
            if "–" in content:
                name_part, role_part = content.split("–", 1)
                display_name = name_part.strip()
                role = role_part.strip()
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
        role=role,
    )


def load_profiles() -> list[UserRecord]:
    repo_root = Path(__file__).resolve().parents[3]
    personas_dir = repo_root / "docs" / "product" / "personas"
    if not personas_dir.exists():
        return []

    records: list[UserRecord] = []
    for file_path in personas_dir.glob("*.md"):
        record = _parse_persona(file_path)
        if record:
            records.append(record)
    return records


async def seed_conversations_for_user(
    session: AsyncSession, user_id: str, user_email: str
) -> None:
    now = datetime.now(UTC)

    if "sarah" in user_email.lower():
        conversation_1 = Conversation(
            user_id=user_id,
            title="Site evaluation vs top comps",
            messages_document=[
                {
                    "id": "seed-msg-1-1",
                    "role": "user",
                    "content": "I'm evaluating a site at the Westgate Shopping Center in Phoenix. Can you compare it to our top performing locations?",
                    "created_at": (now - timedelta(days=7)).isoformat(),
                },
                {
                    "id": "seed-msg-1-2",
                    "role": "_agent",
                    "content": "I'll compare traffic volume, trade area demographics, and visit patterns for the Westgate site against your top 10 stores in Phoenix and similar suburban shopping centers. What metrics are most critical for your decision?",
                    "created_at": (now - timedelta(days=7, seconds=-30)).isoformat(),
                },
                {
                    "id": "seed-msg-1-3",
                    "role": "user",
                    "content": "Focus on weekly visit trends, income bands, and draw radius. I need to present this to Finance next week.",
                    "created_at": (now - timedelta(days=7, seconds=-120)).isoformat(),
                },
            ],
            created_at=now - timedelta(days=7),
            updated_at=now - timedelta(days=7, seconds=-120),
        )

        conversation_2 = Conversation(
            user_id=user_id,
            title="Cannibalization analysis for infill",
            messages_document=[
                {
                    "id": "seed-msg-2-1",
                    "role": "user",
                    "content": "We're considering an infill location between our Scottsdale and Tempe stores. Will this cannibalize existing traffic?",
                    "created_at": (now - timedelta(days=3)).isoformat(),
                },
                {
                    "id": "seed-msg-2-2",
                    "role": "_agent",
                    "content": "I'll analyze trade area overlap and estimate visit redistribution. Do you have the specific address for the candidate site?",
                    "created_at": (now - timedelta(days=3, seconds=-20)).isoformat(),
                },
                {
                    "id": "seed-msg-2-3",
                    "role": "user",
                    "content": "Yes, it's at Mesa Riverview. I'm concerned about pulling too much from our Tempe location which is already a top performer.",
                    "created_at": (now - timedelta(days=3, seconds=-90)).isoformat(),
                },
            ],
            created_at=now - timedelta(days=3),
            updated_at=now - timedelta(days=3, seconds=-90),
        )

        conversation_3 = Conversation(
            user_id=user_id,
            title="Portfolio health check - Dallas market",
            messages_document=[
                {
                    "id": "seed-msg-3-1",
                    "role": "user",
                    "content": "Can you rank all our Dallas locations by visit trends? I think a few stores might be underperforming.",
                    "created_at": now.isoformat(),
                },
                {
                    "id": "seed-msg-3-2",
                    "role": "_agent",
                    "content": "I'll rank your Dallas stores by 12-month visit trends, frequency, and dwell time versus market benchmarks. I'll flag any sustained negative trends. How many stores do you have in the Dallas metro?",
                    "created_at": (now + timedelta(seconds=25)).isoformat(),
                },
            ],
            created_at=now,
            updated_at=now + timedelta(seconds=25),
        )

        session.add(conversation_1)
        session.add(conversation_2)
        session.add(conversation_3)
    await session.commit()


async def seed_user_profiles(session: AsyncSession) -> None:
    profiles = load_profiles()
    if not profiles:
        return

    settings = get_settings()
    first_user_id = None
    first_user_email = None

    for idx, profile in enumerate(profiles):
        user = await get_user_by_email(session, profile.email)
        hashed_password = get_password_hash(settings.persona_seed_password)
        if user:
            user.display_name = profile.display_name
            user.role = profile.role
            user.hashed_password = hashed_password
            if idx == 0:
                first_user_id = user.id
                first_user_email = user.email
        else:
            new_user = User(
                email=profile.email,
                display_name=profile.display_name,
                role=profile.role,
                hashed_password=hashed_password,
            )
            session.add(new_user)
            await session.flush()
            if idx == 0:
                first_user_id = new_user.id
                first_user_email = new_user.email

    await session.commit()

    if first_user_id and first_user_email:
        await seed_conversations_for_user(session, first_user_id, first_user_email)
