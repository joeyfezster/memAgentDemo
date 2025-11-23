from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import create_access_token, get_password_hash, verify_password
from app.crud import persona as persona_crud
from app.crud.user import create_user, get_user_by_email, update_letta_agent_id
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserPublic
from app.services.pi_agent import pi_agent_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, session: AsyncSession = Depends(get_session)
) -> TokenResponse:
    user = await get_user_by_email(session, payload.email)
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.get("/me", response_model=UserPublic)
async def read_current_user(current_user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic.model_validate(current_user)
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest, session: AsyncSession = Depends(get_session)
) -> TokenResponse:
    existing = await get_user_by_email(session, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )

    hashed_password = get_password_hash(payload.password)
    persona_handle = payload.persona_handle or payload.display_name.lower().replace(" ", "_")
    user = await create_user(
        session,
        email=payload.email,
        display_name=payload.display_name,
        persona_handle=persona_handle,
        role=payload.role,
        hashed_password=hashed_password,
    )

    assigned_personas: list = []
    if payload.persona_handle:
        try:
            assigned_personas = await persona_crud.assign_personas_by_handles(
                session, user, [payload.persona_handle]
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

    if pi_agent_service.is_configured():
        agent_id = await pi_agent_service.provision_user_agent(user, assigned_personas)
        user = await update_letta_agent_id(session, user, agent_id)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))
