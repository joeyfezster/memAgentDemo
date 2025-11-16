from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    persona_handle: str,
    role: str | None,
    hashed_password: str,
    letta_agent_id: str | None = None,
) -> User:
    user = User(
        email=email,
        display_name=display_name,
        persona_handle=persona_handle,
        role=role,
        hashed_password=hashed_password,
        letta_agent_id=letta_agent_id,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_letta_agent_id(
    session: AsyncSession, user: User, agent_id: str | None
) -> User:
    user.letta_agent_id = agent_id
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
