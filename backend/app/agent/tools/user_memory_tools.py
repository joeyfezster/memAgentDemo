from typing import Any, Literal

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user import (
    add_user_memory_fact,
    add_user_memory_poi,
    deactivate_user_memory_fact,
    get_user_memory,
)

# ==============================
# Tool Input Model
# ==============================


class ManageUserMemoryInput(BaseModel):
    operation: Literal["add_fact", "deactivate_fact", "add_poi", "get_memory"]
    content: str | None = Field(None, description="For add_fact: the fact to remember")
    fact_id: str | None = Field(
        None, description="For deactivate_fact: the UUID of fact to deactivate"
    )
    place_id: str | None = Field(
        None, description="For add_poi: unique identifier for place"
    )
    place_name: str | None = Field(None, description="For add_poi: human-readable name")
    notes: str | None = Field(None, description="For add_poi: additional context")


# ==============================
# Tool Implementation
# ==============================


class ManageUserMemoryTool:
    name = "manage_user_memory"
    description = """Store and retrieve persistent facts about the user that should be remembered across all conversations.

    WHEN TO USE:
    - User shares personal information (name, preferences, interests, location)
    - User shows special attention to places of interest (POIs) (e.g. specific retail stores, portfolio locations, etc)
    - User explicitly asks you to remember something
    - User corrects previous information (deactivate old fact, add new one)

    WHAT TO STORE:
    - Personal details: "User's name is Alex", "User prefers morning workouts"
    - Placer Intelligence: "User is interested in identifying the next rollout location for his retail stores, and uses foot traffic data to help make decisions."
    - Points of Interest (POIs): "place_sf_001: Starbucks Reserve Roastery"
    - Preferences: "User likes Italian food", "User is vegetarian"
    - Context: "User is a real estate developer for Starbucks"

    DO NOT STORE:
    - Sensitive data (passwords, SSN, financial info)
    - Temporary information (first-time analytical asks before user shows interest, today's weather, one-time events)
    - Information user hasn't shared or confirmed

    OPERATIONS:
    - add_fact: Store a new fact (requires: content)
    - deactivate_fact: Mark fact as outdated (requires: fact_id)
    - add_poi: Store a place of interest (requires: place_id, place_name) - given this is a demo, if you don't know the place_id, make one up
    - get_memory: Retrieve all stored memories
    """

    def get_input_schema(self) -> dict:
        return ManageUserMemoryInput.model_json_schema()

    async def execute(self, **kwargs: Any) -> dict:
        session: AsyncSession | None = kwargs.get("session")
        user_id: str | None = kwargs.get("user_id")
        conversation_id: str | None = kwargs.get("conversation_id")
        message_id: str | None = kwargs.get("message_id")

        if not session or not user_id:
            return {
                "error": "Database session or user_id not available",
                "success": False,
            }

        try:
            input_data = ManageUserMemoryInput(**kwargs)
        except Exception as e:
            return {"error": f"Invalid input parameters: {str(e)}", "success": False}

        try:
            if input_data.operation == "add_fact":
                if not input_data.content:
                    return {
                        "error": "content is required for add_fact",
                        "success": False,
                    }

                fact_id = await add_user_memory_fact(
                    session=session,
                    user_id=user_id,
                    content=input_data.content,
                    source_conversation_id=conversation_id,
                    source_message_id=message_id,
                )
                return {
                    "success": True,
                    "operation": "add_fact",
                    "fact_id": fact_id,
                    "message": f"Stored fact: {input_data.content}",
                }

            elif input_data.operation == "deactivate_fact":
                if not input_data.fact_id:
                    return {
                        "error": "fact_id is required for deactivate_fact",
                        "success": False,
                    }

                success = await deactivate_user_memory_fact(
                    session=session, user_id=user_id, fact_id=input_data.fact_id
                )
                if success:
                    return {
                        "success": True,
                        "operation": "deactivate_fact",
                        "message": f"Deactivated fact {input_data.fact_id}",
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Fact {input_data.fact_id} not found",
                    }

            elif input_data.operation == "add_poi":
                if not input_data.place_id or not input_data.place_name:
                    return {
                        "error": "place_id and place_name are required for add_poi",
                        "success": False,
                    }

                if not conversation_id or not message_id:
                    return {
                        "error": "conversation_id and message_id required for add_poi",
                        "success": False,
                    }

                poi_id = await add_user_memory_poi(
                    session=session,
                    user_id=user_id,
                    place_id=input_data.place_id,
                    place_name=input_data.place_name,
                    notes=input_data.notes,
                    conversation_id=conversation_id,
                    message_id=message_id,
                )
                return {
                    "success": True,
                    "operation": "add_poi",
                    "place_id": poi_id,
                    "message": f"Stored place: {input_data.place_name}",
                }

            elif input_data.operation == "get_memory":
                memory = await get_user_memory(session=session, user_id=user_id)
                active_facts = [f for f in memory.facts if f.is_active]
                return {
                    "success": True,
                    "operation": "get_memory",
                    "facts": [
                        {
                            "id": f.id,
                            "content": f.content,
                            "added_at": f.added_at,
                        }
                        for f in active_facts
                    ],
                    "places": [
                        {
                            "place_id": p.place_id,
                            "place_name": p.place_name,
                            "notes": p.notes,
                        }
                        for p in memory.placer_user_datapoints
                        if hasattr(p, "place_id")
                    ],
                    "metadata": {
                        "total_facts": memory.metadata.total_facts,
                        "total_active_facts": memory.metadata.total_active_facts,
                        "total_pois": memory.metadata.total_pois,
                        "token_count": memory.metadata.token_count,
                    },
                }

            else:
                return {
                    "error": f"Unknown operation: {input_data.operation}",
                    "success": False,
                }

        except Exception as e:
            return {"error": f"Operation failed: {str(e)}", "success": False}


USER_MEMORY_TOOLS = [
    ManageUserMemoryTool(),
]
