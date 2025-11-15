"""Memory management endpoints."""

from fastapi import APIRouter, HTTPException, status
from app.schemas.memory import MemoryCreate, MemoryResponse

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_memory(memory: MemoryCreate) -> MemoryResponse:
    """Create a new memory entry."""
    # TODO: Implement memory creation logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Memory creation not yet implemented",
    )


@router.get("/{memory_id}")
async def get_memory(memory_id: str) -> MemoryResponse:
    """Retrieve a memory entry by ID."""
    # TODO: Implement memory retrieval logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Memory retrieval not yet implemented",
    )


@router.get("/")
async def list_memories(skip: int = 0, limit: int = 100) -> list[MemoryResponse]:
    """List memory entries."""
    # TODO: Implement memory listing logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Memory listing not yet implemented",
    )
