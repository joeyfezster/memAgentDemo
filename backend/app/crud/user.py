from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.types import MemoryDocument
from app.models.user import User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: str) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def list_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User))
    return list(result.scalars().all())


async def create_user(
    session: AsyncSession,
    *,
    email: str,
    display_name: str,
    role: str | None,
    hashed_password: str,
) -> User:
    user = User(
        email=email,
        display_name=display_name,
        role=role,
        hashed_password=hashed_password,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def add_user_memory_fact(
    session: AsyncSession,
    user_id: str,
    content: str,
    source_conversation_id: str | None,
    source_message_id: str | None,
) -> str:
    user = await get_user_by_id(session, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    fact_id = user.add_fact(content, source_conversation_id, source_message_id)
    await session.commit()
    await session.refresh(user)
    return fact_id


async def deactivate_user_memory_fact(
    session: AsyncSession, user_id: str, fact_id: str
) -> bool:
    user = await get_user_by_id(session, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    success = user.deactivate_fact(fact_id)
    if success:
        await session.commit()
        await session.refresh(user)
    return success


async def add_user_memory_poi(
    session: AsyncSession,
    user_id: str,
    place_id: str,
    place_name: str,
    notes: str | None,
    conversation_id: str,
    message_id: str,
) -> str:
    user = await get_user_by_id(session, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    poi_id = user.add_poi(place_id, place_name, notes, conversation_id, message_id)
    await session.commit()
    await session.refresh(user)
    return poi_id


async def get_user_memory(session: AsyncSession, user_id: str) -> MemoryDocument:
    user = await get_user_by_id(session, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    return user.get_memory()
