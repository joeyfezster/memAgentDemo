from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    display_name: str
    persona_handle: str
    role: str | None = None
    letta_agent_id: str | None = None
    created_at: datetime
    updated_at: datetime


class UserPublic(UserBase):
    pass
