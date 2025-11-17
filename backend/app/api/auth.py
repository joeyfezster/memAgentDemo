from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.letta_client import create_letta_client, create_pi_agent
from app.core.security import create_access_token, get_password_hash, verify_password
from app.crud.user import create_user, get_user_by_email
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])

logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, session: AsyncSession = Depends(get_session)
) -> TokenResponse:
    user = await get_user_by_email(session, payload.email)
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    payload: RegisterRequest, session: AsyncSession = Depends(get_session)
) -> TokenResponse:
    existing_user = await get_user_by_email(session, payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password = get_password_hash(payload.password)

    letta_agent_id = None
    letta_base_url = os.getenv("LETTA_BASE_URL", "http://localhost:8283")
    letta_token = os.getenv("LETTA_SERVER_PASSWORD")

    try:
        letta_client = create_letta_client(letta_base_url, letta_token)
        letta_agent_id = create_pi_agent(
            letta_client,
            user_display_name=payload.display_name,
            initial_user_persona_info="",
        )
    except Exception as e:
        logger.warning("Warning: Could not create Letta agent during registration: %s", e)

    user = await create_user(
        session,
        email=payload.email,
        display_name=payload.display_name,
        hashed_password=hashed_password,
        letta_agent_id=letta_agent_id,
    )

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.get("/me", response_model=UserPublic)
async def read_current_user(
    current_user: User = Depends(get_current_user),
) -> UserPublic:
    return UserPublic.model_validate(current_user)
