from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


class PersonaInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    persona_handle: str


class UserPersonaInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    persona: PersonaInfo


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    display_name: str
    user_personas: list[UserPersonaInfo] = []
    letta_agent_id: str | None = None
    created_at: datetime
    updated_at: datetime


class UserPublic(UserBase):
    pass
