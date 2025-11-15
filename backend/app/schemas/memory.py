"""Memory schemas."""

from datetime import datetime
from pydantic import BaseModel, Field


class MemoryBase(BaseModel):
    """Base memory schema."""

    content: str = Field(..., description="Memory content")
    metadata: dict[str, str] | None = Field(default=None, description="Additional metadata")


class MemoryCreate(MemoryBase):
    """Schema for creating a memory."""

    pass


class MemoryResponse(MemoryBase):
    """Schema for memory response."""

    id: str = Field(..., description="Memory ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}
