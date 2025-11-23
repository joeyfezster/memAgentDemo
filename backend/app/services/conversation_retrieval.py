from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation


async def search_conversations_fulltext(
    session: AsyncSession, user_id: str, search_text: str, limit: int = 10
) -> list[Conversation]:
    """Search conversations using full-text search on message content.

    Searches through all messages in conversations for the given user,
    looking for the search text in message content, roles, and metadata.
    Uses PostgreSQL GIN indexes for efficient full-text search.

    Args:
        session: The async database session.
        user_id: The ID of the user whose conversations to search.
        search_text: The text to search for (case-insensitive substring match).
        limit: Maximum number of conversations to return. Defaults to 10.

    Returns:
        A list of Conversation objects matching the search criteria,
        ordered by relevance.

    Example:
        >>> # Search for conversations about store cannibalization analysis
        >>> conversations = await search_conversations_fulltext(
        ...     session, user_id="123", search_text="cannibalization", limit=5
        ... )
        >>> # Search for retail media campaign discussions
        >>> conversations = await search_conversations_fulltext(
        ...     session, user_id="456", search_text="retail media lift", limit=10
        ... )
    """
    result = await session.execute(
        select(Conversation)
        .where(
            Conversation.user_id == user_id,
            func.cast(Conversation.messages_document, type_=text("text")).ilike(
                f"%{search_text}%"
            ),
        )
        .limit(limit)
    )
    return list(result.scalars().all())


async def search_conversations_vector(
    session: AsyncSession,
    user_id: str,
    query_embedding: list[float],
    limit: int = 10,
) -> list[Conversation]:
    """Search conversations using semantic vector similarity.

    Finds conversations semantically similar to the query using pgvector
    cosine distance. Requires conversations to have embeddings generated.

    Args:
        session: The async database session.
        user_id: The ID of the user whose conversations to search.
        query_embedding: Vector embedding of the search query (e.g., from OpenAI
            text-embedding-3-small). Must match the dimension configured in
            settings.embedding_dimension (default 1536).
        limit: Maximum number of conversations to return. Defaults to 10.

    Returns:
        A list of Conversation objects ordered by semantic similarity
        (closest first), excluding conversations without embeddings.

    Example:
        >>> # Find conversations about site selection semantically similar to query
        >>> query_emb = await get_embedding(
        ...     "Which locations should I consider for new store openings?"
        ... )
        >>> conversations = await search_conversations_vector(
        ...     session, user_id="123", query_embedding=query_emb, limit=5
        ... )
    """
    result = await session.execute(
        select(Conversation)
        .where(
            Conversation.user_id == user_id,
            Conversation.embedding.isnot(None),
        )
        .order_by(Conversation.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    return list(result.scalars().all())


async def search_conversations_hybrid(
    session: AsyncSession,
    user_id: str,
    search_text: str,
    query_embedding: list[float],
    limit: int = 10,
    alpha: float = 0.5,
) -> list[Conversation]:
    """Search conversations using hybrid full-text and vector similarity.

    Combines full-text search and semantic vector search with weighted scoring
    to find the most relevant conversations. Uses reciprocal rank fusion (RRF)
    to merge results from both search methods.

    Args:
        session: The async database session.
        user_id: The ID of the user whose conversations to search.
        search_text: The text to search for (case-insensitive substring match).
        query_embedding: Vector embedding of the search query. Must match the
            dimension configured in settings.embedding_dimension (default 1536).
        limit: Maximum number of conversations to return. Defaults to 10.
        alpha: Weight balance between full-text (alpha) and vector (1-alpha)
            search. Range [0.0, 1.0]. Default 0.5 gives equal weight.

    Returns:
        A list of Conversation objects ordered by hybrid relevance score
        (highest first), combining both lexical and semantic matches.

    Example:
        >>> # Search for trade area analysis using both keywords and semantics
        >>> query_emb = await get_embedding(
        ...     "Show me trade area demographics and visitor profiles"
        ... )
        >>> conversations = await search_conversations_hybrid(
        ...     session, user_id="123", search_text="trade area demographics",
        ...     query_embedding=query_emb, limit=5, alpha=0.6
        ... )
    """
    fulltext_results = await search_conversations_fulltext(
        session, user_id, search_text, limit=limit * 2
    )
    vector_results = await search_conversations_vector(
        session, user_id, query_embedding, limit=limit * 2
    )

    scored_conversations: dict[str, tuple[Conversation, float]] = {}

    for conv in fulltext_results:
        rank = fulltext_results.index(conv)
        score = alpha * (1.0 / (rank + 1))
        scored_conversations[conv.id] = (conv, score)

    for conv in vector_results:
        rank = vector_results.index(conv)
        vector_score = (1.0 - alpha) * (1.0 / (rank + 1))
        if conv.id in scored_conversations:
            existing_conv, existing_score = scored_conversations[conv.id]
            scored_conversations[conv.id] = (
                existing_conv,
                existing_score + vector_score,
            )
        else:
            scored_conversations[conv.id] = (conv, vector_score)

    sorted_conversations = sorted(
        scored_conversations.values(), key=lambda x: x[1], reverse=True
    )

    return [conv for conv, score in sorted_conversations[:limit]]


def filter_messages_by_role(
    conversation: Conversation, message_role: str
) -> list[dict]:
    """Filter messages in a conversation by role.

    Extracts only messages with a specific role from a conversation.
    Useful for analyzing user questions, agent responses, or system messages.

    Args:
        conversation: The Conversation object to filter.
        message_role: The role to filter by. Valid values: "user", "_agent", "system".

    Returns:
        A list of message dictionaries with the specified role, preserving
        original order.

    Example:
        >>> # Extract all user questions about store performance
        >>> user_msgs = filter_messages_by_role(conversation, "user")
        >>> # Get all agent recommendations for site selection
        >>> agent_msgs = filter_messages_by_role(conversation, "_agent")
    """
    messages = conversation.get_messages()
    return [msg for msg in messages if msg.get("role") == message_role]


def filter_messages_by_date_range(
    conversation: Conversation, start: datetime, end: datetime
) -> list[dict]:
    """Filter messages in a conversation by date range.

    Extracts messages created within a specific time window. Useful for
    analyzing conversation history over specific periods or finding recent
    interactions.

    Args:
        conversation: The Conversation object to filter.
        start: The start of the date range (inclusive).
        end: The end of the date range (inclusive).

    Returns:
        A list of message dictionaries created between start and end dates,
        preserving original order. Messages with invalid timestamps are excluded.

    Example:
        >>> # Get campaign performance discussions from last quarter
        >>> from datetime import datetime, timedelta
        >>> end = datetime.now(UTC)
        >>> start = end - timedelta(days=90)
        >>> recent_msgs = filter_messages_by_date_range(conversation, start, end)
    """
    messages = conversation.get_messages()
    filtered = []
    for msg in messages:
        created_at_str = msg.get("created_at")
        if created_at_str:
            try:
                if isinstance(created_at_str, str):
                    msg_date = datetime.fromisoformat(
                        created_at_str.replace("Z", "+00:00")
                    )
                else:
                    msg_date = created_at_str
                if start <= msg_date <= end:
                    filtered.append(msg)
            except (ValueError, AttributeError):
                continue
    return filtered
