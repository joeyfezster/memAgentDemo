from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserPublic


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1)
    password: str = Field(min_length=8)
    persona_handle: str | None = None
    role: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
