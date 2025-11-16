from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message, MessageRole


async def create_message(
    session: AsyncSession, *, conversation_id: str, role: MessageRole, content: str
) -> Message:
    message = Message(conversation_id=conversation_id, role=role, content=content)
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message


async def get_conversation_messages(
    session: AsyncSession, conversation_id: str
) -> list[Message]:
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())


async def get_message_count(session: AsyncSession, conversation_id: str) -> int:
    result = await session.execute(
        select(Message).where(Message.conversation_id == conversation_id)
    )
    return len(list(result.scalars().all()))
