from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.crud import conversation as conversation_crud
from app.crud import message as message_crud
from app.db.session import get_session
from app.models.message import MessageRole
from app.models.user import User
from app.schemas.chat import (
    ChatMessage,
    ChatResponse,
    ConversationListResponse,
    ConversationSchema,
    CreateConversationResponse,
    MessageListResponse,
    MessageSchema,
    SendMessageRequest,
    SendMessageResponse,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/messages", response_model=ChatResponse)
async def create_message(
    payload: ChatMessage, current_user: User = Depends(get_current_user)
) -> ChatResponse:
    reply_text = f"hi {current_user.display_name}"
    return ChatResponse(reply=reply_text)


@router.post("/conversations", response_model=CreateConversationResponse)
async def create_conversation(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CreateConversationResponse:
    conversation = await conversation_crud.create_conversation(
        session, user_id=current_user.id
    )
    return CreateConversationResponse(
        id=conversation.id, created_at=conversation.created_at
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ConversationListResponse:
    conversations = await conversation_crud.get_user_conversations(
        session, current_user.id
    )
    return ConversationListResponse(
        conversations=[
            ConversationSchema.model_validate(conv) for conv in conversations
        ]
    )


@router.get(
    "/conversations/{conversation_id}/messages", response_model=MessageListResponse
)
async def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MessageListResponse:
    conversation = await conversation_crud.get_conversation_by_id(
        session, conversation_id, current_user.id
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )

    messages = await message_crud.get_conversation_messages(session, conversation_id)
    return MessageListResponse(
        messages=[MessageSchema.model_validate(msg) for msg in messages]
    )


@router.post(
    "/conversations/{conversation_id}/messages", response_model=SendMessageResponse
)
async def send_message_to_conversation(
    conversation_id: str,
    payload: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SendMessageResponse:
    conversation = await conversation_crud.get_conversation_by_id(
        session, conversation_id, current_user.id
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )

    user_message = await message_crud.create_message(
        session,
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=payload.content,
    )

    assistant_reply = f"hi {current_user.display_name}"
    assistant_message = await message_crud.create_message(
        session,
        conversation_id=conversation_id,
        role=MessageRole.AGENT,
        content=assistant_reply,
    )

    message_count = await message_crud.get_message_count(session, conversation_id)
    if message_count == 2 and not conversation.title:
        words = payload.content.split()[:4]
        title_prefix = " ".join(words)
        timestamp = datetime.now().strftime("%d-%m:%H:%M")
        title = f"{title_prefix} {timestamp}"
        await conversation_crud.update_conversation_title(
            session, conversation_id, title
        )

    return SendMessageResponse(
        user_message=MessageSchema.model_validate(user_message),
        assistant_message=MessageSchema.model_validate(assistant_message),
    )
