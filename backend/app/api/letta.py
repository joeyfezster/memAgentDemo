from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.letta_client import create_letta_client
from app.crud import user as user_crud
from app.db.session import get_session
from app.models.user import User
from app.schemas.letta import (
    AgentArchivalResponse,
    AgentOverviewSchema,
    AgentsOverviewResponse,
    ArchivalEntrySchema,
    AssignedUserSchema,
    MemoryBlockSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/letta", tags=["letta"])


def _serialize_model(model: Any) -> dict[str, Any]:
    if model is None:
        return {}
    if hasattr(model, "model_dump"):
        return dict(model.model_dump())  # type: ignore[no-any-return]
    if hasattr(model, "dict"):
        return dict(model.dict())  # type: ignore[no-any-return]
    if isinstance(model, dict):
        return dict(model)
    if hasattr(model, "__dict__"):
        return {
            key: value
            for key, value in vars(model).items()
            if not key.startswith("_")
        }
    return {"value": model}


def _extract_metadata(data: dict[str, Any], reserved_keys: set[str]) -> dict[str, Any]:
    return {
        key: value
        for key, value in data.items()
        if key not in reserved_keys and value is not None
    }


def _infer_agent_name(agent_data: dict[str, Any]) -> str | None:
    for key in ("name", "display_name", "agent_name", "handle", "alias"):
        value = agent_data.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _create_client():
    letta_base_url = os.getenv("LETTA_BASE_URL", "http://localhost:8283")
    letta_token = os.getenv("LETTA_SERVER_PASSWORD")
    try:
        return create_letta_client(letta_base_url, letta_token)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to create Letta client")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to connect to Letta server",
        ) from exc


@router.get("/agents/overview", response_model=AgentsOverviewResponse)
async def get_agents_overview(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AgentsOverviewResponse:
    del current_user  # The endpoint is currently admin-only

    letta_client = _create_client()

    try:
        agent_states = list(letta_client.agents.list())
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unable to list agents from Letta")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to list Letta agents",
        ) from exc

    users = await user_crud.list_users(session)
    agent_to_user = {
        user.letta_agent_id: user for user in users if user.letta_agent_id
    }

    serialized_agents: list[AgentOverviewSchema] = []
    total_blocks = 0

    for agent_state in agent_states:
        agent_data = _serialize_model(agent_state)
        agent_id = str(agent_data.get("id") or getattr(agent_state, "id", ""))

        blocks: list[MemoryBlockSchema] = []
        try:
            block_states = letta_client.agents.blocks.list(agent_id=agent_id)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "Unable to list memory blocks for agent %s: %s", agent_id, exc
            )
            block_states = []

        for block_state in block_states:
            block_data = _serialize_model(block_state)
            block_id = str(block_data.get("id") or getattr(block_state, "id", ""))
            block = MemoryBlockSchema(
                id=block_id,
                label=block_data.get("label"),
                description=block_data.get("description"),
                value=block_data.get("value"),
                limit=block_data.get("limit"),
                read_only=block_data.get("read_only"),
                block_type=block_data.get("block_type"),
                metadata=_extract_metadata(
                    block_data,
                    {
                        "id",
                        "label",
                        "description",
                        "value",
                        "limit",
                        "read_only",
                        "block_type",
                    },
                ),
            )
            blocks.append(block)

        total_blocks += len(blocks)

        assigned_user = agent_to_user.get(agent_id)
        serialized_agents.append(
            AgentOverviewSchema(
                id=agent_id,
                name=_infer_agent_name(agent_data),
                created_at=agent_data.get("created_at"),
                updated_at=agent_data.get("updated_at"),
                user=(
                    AssignedUserSchema(
                        id=assigned_user.id,
                        email=assigned_user.email,
                        display_name=assigned_user.display_name,
                    )
                    if assigned_user
                    else None
                ),
                memory_blocks=blocks,
                metadata=_extract_metadata(
                    agent_data, {"id", "created_at", "updated_at"}
                ),
            )
        )

    return AgentsOverviewResponse(
        agents=serialized_agents,
        agent_count=len(serialized_agents),
        block_count=total_blocks,
        generated_at=datetime.now(UTC),
    )


@router.get(
    "/agents/{agent_id}/archival", response_model=AgentArchivalResponse
)
async def get_agent_archival_entries(
    agent_id: str,
    limit: int = 7,
    current_user: User = Depends(get_current_user),
) -> AgentArchivalResponse:
    del current_user  # Authorization handled by dependency

    safe_limit = max(1, min(limit, 200))
    letta_client = _create_client()

    try:
        passages = letta_client.agents.passages.list(
            agent_id=agent_id,
            limit=safe_limit,
            ascending=False,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unable to list archival entries for %s", agent_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to read archival memory entries",
        ) from exc

    entries: list[ArchivalEntrySchema] = []
    for passage in passages:
        passage_data = _serialize_model(passage)
        entry_id = str(passage_data.get("id") or getattr(passage, "id", ""))
        raw_tags = passage_data.get("tags") or []
        entry = ArchivalEntrySchema(
            id=entry_id,
            content=str(passage_data.get("content") or ""),
            tags=[str(tag) for tag in raw_tags],
            created_at=passage_data.get("created_at"),
            updated_at=passage_data.get("updated_at"),
            metadata=_extract_metadata(
                passage_data,
                {"id", "content", "tags", "created_at", "updated_at"},
            ),
        )
        entries.append(entry)

    return AgentArchivalResponse(
        agent_id=agent_id,
        entries=entries,
        requested_limit=safe_limit,
        returned_count=len(entries),
    )
