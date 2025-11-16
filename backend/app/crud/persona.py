from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.persona import Persona, UserPersona
from app.models.user import User


async def get_persona_by_handle(session: AsyncSession, handle: str) -> Persona | None:
    result = await session.execute(select(Persona).where(Persona.handle == handle))
    return result.scalar_one_or_none()


async def get_personas_by_handles(
    session: AsyncSession, handles: list[str]
) -> list[Persona]:
    if not handles:
        return []
    result = await session.execute(select(Persona).where(Persona.handle.in_(handles)))
    return list(result.scalars().all())


async def assign_personas_by_handles(
    session: AsyncSession,
    user: User,
    handles: list[str],
    *,
    confidence_score: float = 1.0,
) -> list[Persona]:
    if not handles:
        return []
    personas = await get_personas_by_handles(session, handles)
    handle_map = {persona.handle: persona for persona in personas}
    missing = [handle for handle in handles if handle not in handle_map]
    if missing:
        raise ValueError(f"Unknown personas: {', '.join(missing)}")

    existing_links = await _get_user_persona_links(session, user.id)
    link_map = {(link.user_id, link.persona_id): link for link in existing_links}
    now = datetime.now(UTC)
    assigned: list[Persona] = []

    for handle in handles:
        persona = handle_map[handle]
        assigned.append(persona)
        key = (user.id, persona.id)
        if key in link_map:
            link = link_map[key]
            link.confidence_score = confidence_score
            link.last_confirmed = now
            continue
        session.add(
            UserPersona(
                user_id=user.id,
                persona_id=persona.id,
                confidence_score=confidence_score,
                discovered_at=now,
                last_confirmed=now,
            )
        )
    await session.commit()
    return assigned


async def list_user_personas(session: AsyncSession, user_id: str) -> list[UserPersona]:
    result = await session.execute(
        select(UserPersona)
        .options(selectinload(UserPersona.persona))
        .where(UserPersona.user_id == user_id)
        .order_by(UserPersona.last_confirmed.desc())
    )
    return list(result.scalars().all())


async def sync_user_personas(
    session: AsyncSession,
    user_id: str,
    persona_confidences: dict[str, float],
) -> None:
    personas = await get_personas_by_handles(session, list(persona_confidences.keys()))
    persona_map = {persona.handle: persona for persona in personas}
    now = datetime.now(UTC)

    existing_links = await _get_user_persona_links(session, user_id)
    existing_map = {link.persona_id: link for link in existing_links}
    desired_persona_ids: set[str] = set()

    for handle, score in persona_confidences.items():
        persona = persona_map.get(handle)
        if not persona:
            continue
        desired_persona_ids.add(persona.id)
        link = existing_map.get(persona.id)
        if link:
            link.confidence_score = score
            link.last_confirmed = now
            continue
        session.add(
            UserPersona(
                user_id=user_id,
                persona_id=persona.id,
                confidence_score=score,
                discovered_at=now,
                last_confirmed=now,
            )
        )

    for persona_id, link in existing_map.items():
        if persona_id not in desired_persona_ids:
            await session.delete(link)

    await session.commit()


async def _get_user_persona_links(
    session: AsyncSession, user_id: str
) -> list[UserPersona]:
    result = await session.execute(
        select(UserPersona).where(UserPersona.user_id == user_id)
    )
    return list(result.scalars().all())
