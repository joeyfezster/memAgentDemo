from __future__ import annotations

from fastapi import APIRouter, Depends

from app.agents import AgentRequestContext, get_agent_orchestrator
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.chat import ChatMessage, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/messages", response_model=ChatResponse)
async def create_message(
    payload: ChatMessage, current_user: User = Depends(get_current_user)
) -> ChatResponse:
    orchestrator = get_agent_orchestrator()
    context = AgentRequestContext(
        user_id=current_user.id,
        persona_handle=current_user.persona_handle,
        display_name=current_user.display_name,
    )
    reply = await orchestrator.route(context, payload.message)
    return ChatResponse(
        reply=reply.reply,
        agent_slug=reply.agent_slug,
        agent_name=reply.agent_name,
        reasoning=reply.reasoning,
    )
