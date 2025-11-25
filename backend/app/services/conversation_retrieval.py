from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, Text, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.types import ConversationSection


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
            func.cast(Conversation.messages_document, Text).ilike(f"%{search_text}%"),
        )
        .limit(limit)
    )
    return list(result.scalars().all())


async def search_messages_fulltext(
    session: AsyncSession,
    user_id: str,
    keywords: list[str],
    limit: int = 10,
    context_before: int = 2,
    context_after: int = 2,
    max_days_ago: int | None = None,
    role_filter: str | None = None,
    case_sensitive: bool = False,
) -> list[ConversationSection]:
    """Search for specific messages matching keywords with surrounding context.

    Performs message-level keyword search across user's conversations, returning
    matched messages wrapped in ConversationSection objects with configurable context.
    Supports multiple keywords (OR logic), date filtering, and role-based filtering.

    Args:
        session: Async database session
        user_id: User whose conversations to search
        keywords: List of keywords (any match counts)
        limit: Maximum conversation sections to return
        context_before: Number of messages before match to include
        context_after: Number of messages after match to include
        max_days_ago: Only search conversations from last N days (None = all history)
        role_filter: Filter matched messages by role ('user', 'assistant', None = all)
        case_sensitive: Whether keyword matching is case-sensitive (default False)

    Returns:
        List of ConversationSection objects, one per matched conversation,
        ordered by conversation recency (most recent first)
    """
    search_query = select(Conversation).where(Conversation.user_id == user_id)

    if max_days_ago is not None:
        cutoff_date = datetime.now(UTC) - timedelta(days=max_days_ago)
        search_query = search_query.where(Conversation.created_at >= cutoff_date)

    keyword_conditions = [
        func.cast(Conversation.messages_document, Text).ilike(f"%{keyword}%")
        for keyword in keywords
    ]

    if keyword_conditions:
        search_query = search_query.where(or_(*keyword_conditions))

    search_query = search_query.order_by(Conversation.created_at.desc())

    result = await session.execute(search_query)
    conversations = list(result.scalars().all())

    matches = []
    for conv in conversations:
        messages = conv.get_messages()

        for idx, msg in enumerate(messages):
            if role_filter and msg.role != role_filter:
                continue

            content = msg.content if case_sensitive else msg.content.lower()
            keywords_normalized = (
                keywords if case_sensitive else [k.lower() for k in keywords]
            )
            if any(keyword in content for keyword in keywords_normalized):
                start_idx = max(0, idx - context_before)
                end_idx = min(len(messages), idx + context_after + 1)

                context_before_msgs = messages[start_idx:idx]
                context_after_msgs = messages[idx + 1 : end_idx]

                matches.append(
                    ConversationSection(
                        conversation_id=conv.id,
                        conversation_title=conv.title,
                        conversation_created_at=conv.created_at,
                        matched_message=msg,
                        messages_before=context_before_msgs,
                        messages_after=context_after_msgs,
                        match_index=idx,
                        total_messages=len(messages),
                    )
                )

                break

        if len(matches) >= limit:
            break

    return matches[:limit]


async def search_conversations_vector(
    session: AsyncSession,
    user_id: str,
    query_embedding: list[float],
    limit: int = 10,
) -> list[Conversation]:
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
