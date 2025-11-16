from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.chat import ChatMessage, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/messages", response_model=ChatResponse)
async def create_message(
    payload: ChatMessage, current_user: User = Depends(get_current_user)
) -> ChatResponse:
    reply_text = f"hi {current_user.display_name}"
    return ChatResponse(reply=reply_text)
