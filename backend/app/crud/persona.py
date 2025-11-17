from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.persona import Persona
from app.models.user_persona_bridge import UserPersonaBridge


async def get_persona_by_handle(session: AsyncSession, handle: str) -> Persona | None:
    result = await session.execute(
        select(Persona).where(Persona.persona_handle == handle)
    )
    return result.scalar_one_or_none()


async def get_persona_by_id(session: AsyncSession, persona_id: str) -> Persona | None:
    result = await session.execute(select(Persona).where(Persona.id == persona_id))
    return result.scalar_one_or_none()


async def list_all_personas(session: AsyncSession) -> list[Persona]:
    result = await session.execute(select(Persona))
    return list(result.scalars().all())


async def get_user_personas(
    session: AsyncSession, user_id: str
) -> list[UserPersonaBridge]:
    result = await session.execute(
        select(UserPersonaBridge)
        .where(UserPersonaBridge.user_id == user_id)
        .options(selectinload(UserPersonaBridge.persona))
    )
    return list(result.scalars().all())


async def assign_persona_to_user(
    session: AsyncSession,
    user_id: str,
    persona_id: str,
    confidence_score: float = 1.0,
) -> UserPersonaBridge:
    user_persona = UserPersonaBridge(
        user_id=user_id, persona_id=persona_id, confidence_score=confidence_score
    )
    session.add(user_persona)
    await session.commit()
    await session.refresh(user_persona)
    return user_persona


async def update_persona_confidence(
    session: AsyncSession, user_persona_id: str, confidence_score: float
) -> UserPersonaBridge | None:
    result = await session.execute(
        select(UserPersonaBridge).where(UserPersonaBridge.id == user_persona_id)
    )
    user_persona = result.scalar_one_or_none()
    if user_persona:
        user_persona.confidence_score = confidence_score
        await session.commit()
        await session.refresh(user_persona)
    return user_persona


async def remove_persona_from_user(
    session: AsyncSession, user_id: str, persona_id: str
) -> bool:
    result = await session.execute(
        select(UserPersonaBridge).where(
            UserPersonaBridge.user_id == user_id,
            UserPersonaBridge.persona_id == persona_id,
        )
    )
    user_persona = result.scalar_one_or_none()
    if user_persona:
        await session.delete(user_persona)
        await session.commit()
        return True
    return False
