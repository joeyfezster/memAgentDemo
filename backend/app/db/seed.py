from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.crud.user import get_user_by_email
from app.db.persona_loader import load_persona_definitions
from app.models.persona import Persona, UserPersona
from app.models.user import User


async def seed_personas(session: AsyncSession) -> None:
    definitions = load_persona_definitions()
    if not definitions:
        return

    settings = get_settings()
    hashed_password = get_password_hash(settings.persona_seed_password)

    for definition in definitions:
        persona = await _upsert_persona(session, definition)
        user = await _upsert_persona_user(session, definition, hashed_password)
        await _ensure_user_persona_link(session, user.id, persona.id)

    await session.commit()


async def _upsert_persona(session: AsyncSession, definition) -> Persona:
    result = await session.execute(
        select(Persona).where(Persona.handle == definition.persona_handle)
    )
    persona = result.scalar_one_or_none()
    if persona:
        persona.name = definition.display_name
        persona.industry = definition.industry
        persona.professional_role = definition.professional_role
        persona.description = definition.description
        persona.typical_kpis = definition.typical_kpis
        persona.typical_motivations = definition.typical_motivations
        persona.quintessential_queries = definition.quintessential_queries
        return persona

    persona = Persona(
        handle=definition.persona_handle,
        name=definition.display_name,
        industry=definition.industry,
        professional_role=definition.professional_role,
        description=definition.description,
        typical_kpis=definition.typical_kpis,
        typical_motivations=definition.typical_motivations,
        quintessential_queries=definition.quintessential_queries,
    )
    session.add(persona)
    await session.flush()
    return persona


async def _upsert_persona_user(
    session: AsyncSession, definition, hashed_password: str
) -> User:
    user = await get_user_by_email(session, definition.email)
    if user:
        user.display_name = definition.display_name
        user.persona_handle = definition.persona_handle
        user.role = definition.professional_role or user.role
        user.hashed_password = hashed_password
        return user

    user = User(
        email=definition.email,
        display_name=definition.display_name,
        persona_handle=definition.persona_handle,
        role=definition.professional_role,
        hashed_password=hashed_password,
    )
    session.add(user)
    await session.flush()
    return user


async def _ensure_user_persona_link(
    session: AsyncSession, user_id: str, persona_id: str
) -> None:
    result = await session.execute(
        select(UserPersona)
        .where(UserPersona.user_id == user_id)
        .where(UserPersona.persona_id == persona_id)
    )
    link = result.scalar_one_or_none()
    now = datetime.now(UTC)
    if link:
        link.confidence_score = 1.0
        link.last_confirmed = now
        return

    session.add(
        UserPersona(
            user_id=user_id,
            persona_id=persona_id,
            confidence_score=1.0,
            discovered_at=now,
            last_confirmed=now,
        )
    )
