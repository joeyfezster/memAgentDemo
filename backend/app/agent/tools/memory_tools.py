from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.conversation_retrieval import search_messages_fulltext

# ============================================================================
# Tool Input Models (Pydantic for validation)
# ============================================================================


class SearchPastConversationsInput(BaseModel):
    keywords: list[str] = Field(
        ...,
        description="List of keywords to search for in past conversations. Use synonyms or related terms for better recall.",
        min_length=1,
    )
    limit: int = Field(
        5, description="Maximum number of conversations to return", ge=1, le=10
    )
    messages_before: int = Field(
        5,
        description="Number of messages to include before matched message",
        ge=0,
        le=5,
    )
    messages_after: int = Field(
        5, description="Number of messages to include after matched message", ge=0, le=5
    )
    max_days_ago: int | None = Field(
        182,
        description="Only search conversations from the last N days. Omit to search all history.",
        ge=1,
        le=365,
    )
    role_filter: str | None = Field(
        None,
        description="Filter matched messages by role: 'user' or 'assistant'. Omit to search all message types.",
    )
    case_sensitive: bool = Field(
        False,
        description="Whether keyword matching should be case-sensitive. Defaults to False (case-insensitive).",
    )


# ============================================================================
# Tool Implementations
# ============================================================================


class SearchPastConversationsTool:
    name = "search_past_conversations"
    description = """Search through past conversation history using keywords.

    Use when the user references previous discussions:
    - "before", "last time", "we discussed", "you mentioned"
    - "previous conversation about X"
    - "that analysis we did earlier"

    Returns full matched messages with surrounding context showing what was discussed.

    Query tips:
    - Extract 2-3 key terms, not full sentences
    - Use multiple keywords including synonyms and related terms
    - Example: User says "that cannibalization study from last week"
      → keywords: ["cannibalization", "overlap", "impact"]
    """

    def get_input_schema(self) -> dict:
        return SearchPastConversationsInput.model_json_schema()

    async def execute(self, **kwargs: Any) -> dict:
        session: AsyncSession | None = kwargs.get("session")
        user_id: str | None = kwargs.get("user_id")

        if not session or not user_id:
            return {
                "error": "Database session not available",
                "conversations": [],
                "total_found": 0,
            }

        try:
            input_data = SearchPastConversationsInput(**kwargs)
        except Exception as e:
            return {
                "error": f"Invalid input parameters: {str(e)}",
                "conversations": [],
                "total_found": 0,
            }

        try:
            matches = await search_messages_fulltext(
                session=session,
                user_id=user_id,
                keywords=input_data.keywords,
                limit=input_data.limit,
                context_before=input_data.messages_before,
                context_after=input_data.messages_after,
                max_days_ago=input_data.max_days_ago,
                role_filter=input_data.role_filter,
                case_sensitive=input_data.case_sensitive,
            )
        except Exception as e:
            return {
                "error": f"Search failed: {str(e)}",
                "conversations": [],
                "total_found": 0,
            }

        formatted_conversations = []
        for match in matches:
            snippet_parts = []

            for msg in match.messages_before:
                snippet_parts.append(f"[{msg.created_at}] {msg.role}: {msg.content}")

            snippet_parts.append(
                f"**[MATCH {match.matched_message.created_at}]**: {match.matched_message.role}: {match.matched_message.content}"
            )

            for msg in match.messages_after:
                snippet_parts.append(f"[{msg.created_at}] {msg.role}: {msg.content}")

            formatted_conversations.append(
                {
                    "conversation_id": match.conversation_id,
                    "title": match.conversation_title or "Untitled conversation",
                    "matched_snippet": "\n".join(snippet_parts),
                    "timestamp": match.conversation_created_at.isoformat(),
                    "message_count": match.total_messages,
                    "match_position": f"Message {match.match_index + 1} of {match.total_messages}",
                }
            )

        return {
            "conversations": formatted_conversations,
            "total_found": len(matches),
            "keywords_searched": input_data.keywords,
            "note": "Showing full matched messages with surrounding context. **[MATCH: ...]** indicates the message that matched your keywords.",
        }


MEMORY_TOOLS = [
    SearchPastConversationsTool(),
]
