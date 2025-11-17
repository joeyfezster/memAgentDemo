from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AssignedUserSchema(BaseModel):
    id: str
    email: str
    display_name: str


class MemoryBlockSchema(BaseModel):
    id: str
    label: str | None = None
    description: str | None = None
    value: str | None = None
    limit: int | None = None
    read_only: bool | None = None
    block_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentOverviewSchema(BaseModel):
    id: str
    name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user: AssignedUserSchema | None = None
    memory_blocks: list[MemoryBlockSchema] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentsOverviewResponse(BaseModel):
    agents: list[AgentOverviewSchema]
    agent_count: int
    block_count: int
    generated_at: datetime


class ArchivalEntrySchema(BaseModel):
    id: str
    content: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentArchivalResponse(BaseModel):
    agent_id: str
    entries: list[ArchivalEntrySchema]
    requested_limit: int
    returned_count: int
