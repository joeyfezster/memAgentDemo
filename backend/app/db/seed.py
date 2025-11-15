from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.crud.user import get_user_by_email
from app.models.user import User


@dataclass
class PersonaRecord:
    email: str
    display_name: str
    persona_handle: str
    role: str | None


def _parse_persona(file_path: Path) -> PersonaRecord | None:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    display_name: str | None = None
    role: str | None = None
    email: str | None = None
    persona_handle: str | None = None
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
            elif persona_handle is None:
                persona_handle = value

        if display_name and email and persona_handle:
            break

    if not (display_name and email and persona_handle):
        return None

    return PersonaRecord(
        email=email,
        display_name=display_name,
        persona_handle=persona_handle,
        role=role,
    )


def load_personas() -> list[PersonaRecord]:
    repo_root = Path(__file__).resolve().parents[3]
    personas_dir = repo_root / "docs" / "product" / "personas"
    if not personas_dir.exists():
        return []

    records: list[PersonaRecord] = []
    for file_path in personas_dir.glob("*.md"):
        record = _parse_persona(file_path)
        if record:
            records.append(record)
    return records


async def seed_personas(session: AsyncSession) -> None:
    personas = load_personas()
    if not personas:
        return

    settings = get_settings()
    for persona in personas:
        user = await get_user_by_email(session, persona.email)
        hashed_password = get_password_hash(settings.persona_seed_password)
        if user:
            user.display_name = persona.display_name
            user.persona_handle = persona.persona_handle
            user.role = persona.role
            user.hashed_password = hashed_password
        else:
            session.add(
                User(
                    email=persona.email,
                    display_name=persona.display_name,
                    persona_handle=persona.persona_handle,
                    role=persona.role,
                    hashed_password=hashed_password,
                )
            )
    await session.commit()
