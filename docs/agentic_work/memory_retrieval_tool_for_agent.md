# Memory Retrieval Tool for Agent

## Plan:

This plan implements a memory retrieval tool enabling the agent to search through past conversations for relevant context. We'll start with full-text search (leveraging existing GIN indexes), create proper context injection, write comprehensive tests with artificial conversation seeding, and ensure the agent understands when to use this capability.

## Steps

### Implement context injection for tool execution in agent_service.py

> why? what does this achieve? why can't we use the existing \*\*kwargs approach?

Modify ToolRegistry.execute() to accept and pass session and user_id as dependency injection parameters
Update AgentService.generate_response_with_tools() to provide DB context when executing tools
Ensure backward compatibility with tools that don't need session/user context

### Implement SearchPastConversationsTool.execute() in backend/agent/tools/conversation_search.py

Wire up to search_conversations_fulltext() from conversation_retrieval.py
Format results for LLM consumption: conversation title, snippet (first user + assistant message), timestamp, message count
Limit response size to prevent context overflow (~200 tokens per conversation)
Return user-friendly error dicts on failures (never raise exceptions)

> I dont want to assume that conversation_retrieval.py just works and is correctly scoped/implemented
> do we have tests that validate the ~~embedding of the conversations/messages as they occur/are stored~~ keyword based search works as intended?
> ~~what is the current architecture for that? are we re-embedding the entire conversation on each message, or is each message embedded separately and then linked? [should be the latter, but i'm not sure]. This is probably the most important point to clarify before we move forward.~~
> I would expect the ~~semantic~~ keyword search to work a bit like grep -B xx -Axx where we get the matching message and some context before and after it, plus metadata about the conversation
> agree with the rest

### Enhance agent system prompt in agent_config.py

Add guidance on when to use search_past_conversations: when user refers to "before", "last time", "previous", or requests continuity
Specify search query construction: extract key topics/entities rather than full user message
Clarify that tool returns conversation metadata, not full message history (agent should reference findings)

> good idea. i want a test that shows what the tool actually returns - just for clarity and readability

### Create test seed data generator in backend/tests/fixtures/conversation_seeds.py

Build reusable function to create realistic multi-turn conversations with both user and assistant messages
Include diverse topics: site evaluation, cannibalization analysis, trade area demographics, campaign performance
Vary timestamps across conversations (7 days ago, 3 days ago, 1 day ago, recent)
Support parameterized seeding for different test scenarios

> note we allready have seed.py for general seeding - I want this seed to be specific to this past conversation retrieval use case
> make sure you look through the /docs/product docs so the topics are relevant to placer

### Write integration tests in backend/tests/test_memory_retrieval.py

Test tool returns relevant conversations for keyword search (e.g., "cannibalization" finds past cannibalization discussions)
Test user isolation (user A cannot see user B's conversations via tool)
Test result truncation and formatting (verify snippet structure, token limits)
Test edge cases: no matching conversations, empty query, limit parameter

> we have a conversation isolation test already - I wonder if this one belongs together with that one?

### Write agent behavior tests in backend/tests/test_agent_memory.py

Mark as @pytest.mark.expensive (makes real Claude API calls)
Seed 3-4 past conversations with distinct topics for test user
Test agent retrieves past context when user says "like we discussed before about cannibalization"
Test agent uses retrieved context in response (references specific past findings)
Test agent doesn't search when not needed (simple factual questions)
Verify tool_metadata.tool_interactions includes search_past_conversations calls

> yes

## Further Considerations

Embedding generation for hybrid search - Current implementation uses full-text only. Should we implement embedding generation pipeline for semantic search, or defer until we see real usage patterns showing full-text limitations? Option A: Implement basic embedding generation (OpenAI API + async task) now. Option B: Ship full-text first, add embeddings in next iteration based on user feedback.

> see my prev comments on this above - we need to validate the existing ~~embedding~~ keyword search architecture first, or work to fix it if its not designed as we expect

Result ranking improvements - Full-text search uses simple ILIKE matching without relevance scoring. Should we add BM25 or tf-idf scoring to rank results by relevance? This could help when many conversations match but quality varies significantly.

> I don't want to focus on a retrieval optimization until all the memory functionalities are working well. once we have that, we can look at optimizations
> just simple keyword search

Token budget management - Current plan limits to 5 conversations × ~200 tokens = ~1000 tokens max. Should we implement dynamic truncation based on actual context window utilization, or keep fixed limits for predictability?

> make sure it stays fixed

# Plan - V2

## Plan: Memory Retrieval Tool with Keyword Search

TL;DR: Implement message-level keyword search for memory retrieval using existing GIN indexes, returning matching messages with context (grep -B/-A style). Add context injection for DB access in tools, write comprehensive tests with realistic seed data, and integrate into agent workflow. No embeddings, no semantic search - fast and simple.

> realistic and relevant to placer, use /docs/product for inspiration as needed

## Steps

### Add context injection to ToolRegistry and AgentService in base.py and agent_service.py

Modify ToolRegistry.execute() signature: add optional session: AsyncSession | None = None, user_id: str | None = None parameters
Update AgentService.generate_response_with_tools() ReAct loop to pass session and user.id when calling tool_registry.execute(tool_name, session=session, user_id=user.id, **tool_input)
Tools receive these via **kwargs - tools needing DB access extract them, others ignore them
Why needed? Tools are stateless singletons registered at init - can't store request-specific context. Must inject session/user at execution time to query DB while maintaining tool isolation.

> i get the tools are stateless, but do we really need a construct for session and user_id? could we not just pass \*\*kwargs as is, and have the tools extract what they need?

### Create message-level keyword search in conversation_retrieval.py

New function: async def search_messages_fulltext(session, user_id, search_text, limit=10, context_before=2, context_after=2) -> list[dict]
Query: Use existing search_conversations_fulltext() to find conversations, then iterate through messages_document to find exact matching messages
For each match: extract context messages (N before, M after) from same conversation
Return: [[{conversation_id, conversation_title, matched_message: {id, role, content, created_at}, context_before: [...], context_after: [...], match_index, total_messages, conversation_created_at}]](http://vscodecontentref/12)
Enforce user isolation via conversation.user_id = user_id filter
Case-insensitive search using existing GIN trigram index

> all great ideas - just i want to make sure the keyword search is working as intended first, and the existing conversation_retrieval.py and it's tests validate that. if this is not the case - you need to raise this issue!

### Implement SearchPastConversationsTool.execute() in placer_tools.py

Replace placeholder implementation in existing SearchPastConversationsTool class
Extract session and user_id from kwargs - return error dict if missing
Call await search_messages_fulltext(session, user_id, input_data.query, limit=5, context_before=2, context_after=2)
Format for LLM: {conversations: [{id, title, matched_snippet, timestamp, message_count}], total_found, search_query}
Snippet structure: "...{context_before}... **[MATCH: {matched_message}]** ...{context_after}..." (max 150 tokens per conversation)
Fixed limit: 5 conversations max (~750 tokens total)
Return {"error": "Database session not available"} if session/user_id missing

> we need a memory_tools.py, not placer_tools.py
> move the existing SearchPastConversationsTool to memory_tools.py
> the tool should allow for more than one keyword to search for at a time - so the input should be a list of keywords, not a single string in case the agent wants to try synonyms or related terms

### Enhance agent system prompt in agent_config.py

Add section after tool usage guidance:
MEMORY RETRIEVAL:
Use the 'search_past_conversations' tool when the user references prior discussions.
Trigger phrases: "before", "last time", "we discussed", "you mentioned", "previous conversation about X"

Query construction: Extract 2-3 key terms, not full sentences.
Example: User says "like that cannibalization analysis we did last week"
→ Query: "cannibalization analysis"

The tool returns message snippets with surrounding context. Reference these naturally in your response.

### Create test seed utilities in new file backend/tests/fixtures/memory_seeds.py

Function: async def seed_past_conversations_for_sarah(session, user) -> list[Conversation]
Create 4 realistic Placer.ai conversations based on sarah_director_real_estate_qsr.md:
"Site evaluation - Westgate Shopping Center" (7 days ago, 6 messages: trade area comparison, demographics, visitor profiles)
"Cannibalization risk for Dallas infill" (3 days ago, 5 messages: overlap analysis, visit redistribution estimates)
"Portfolio health check - underperforming stores" (1 day ago, 4 messages: ranking stores by metrics, relocation candidates)
"Lease renewal decision - location 458" (2 hours ago, 3 messages: foot traffic trends, comparative performance)
Each conversation has realistic multi-turn exchanges with both user questions and assistant analysis
Vary timestamps: conversation.created_at = datetime.now(UTC) - timedelta(days=X)
Use await conversation_crud.add_message_to_conversation(session, conv.id, role=MessageRole.AGENT.value, content="...")

> the agent and tool messages in the conversation should be realistically generated.

### Write message search tests in test_conversation_retrieval.py (add to existing file)

Test: search_messages_fulltext() finds message containing keyword "cannibalization"
Test: Returns exactly 2 context messages before and 2 after matched message
Test: User isolation - user A cannot search user B's messages
Test: Limit parameter caps results to specified number
Test: Keyword matches in user messages, assistant messages, and system messages
Test: Case-insensitive matching ("Cannibalization" finds "cannibalization")
Test: Empty results when no matches found
Use memory_seeds.seed_past_conversations_for_sarah() for rich test data

> ok

### Write tool execution tests in new file backend/tests/test_memory_tool.py

Test: Tool with valid session/user_id returns formatted results (verify exact JSON structure with matched_snippet format)
Test: Tool without session returns {"error": "Database session not available"}
Test: Tool respects user isolation (user A cannot retrieve user B's conversations)
Test: Result truncation keeps total output under 1000 tokens (5 convs × 150 tokens + metadata)
Test: Empty query returns empty results gracefully
Test: Tool output clearly shows [MATCH: ...] marker in snippets
Purpose: Documentation via tests - shows developers exact tool return format

> yep

### Write agent behavior tests in new file backend/tests/test_agent_memory.py

Mark @pytest.mark.expensive (real Claude API calls)
Setup: Seed 4 conversations using memory_seeds.seed_past_conversations_for_sarah()
Test: User asks "What did we discuss about cannibalization last week?" → agent calls search_past_conversations with query "cannibalization" → response references specific past findings from seeded conversation
Test: User asks "What is cannibalization?" (no historical reference) → agent does NOT call search tool → provides direct definition
Test: User asks "Show me that Dallas analysis from before" → agent searches with "Dallas analysis" → retrieves correct conversation
Test: Verify tool_metadata.tool_interactions contains search_past_conversations with correct query parameter
Test: Agent's response accurately reflects content from retrieved conversation snippets

> yes

## Further Considerations

Search query quality - Should we add few-shot examples in system prompt to improve query extraction? Adding 2-3 examples like "User: 'that store we looked at in Austin' → Query: 'Austin store'" might boost accuracy. Cost: ~50 tokens in prompt. Recommendation: Start simple, add examples if agent struggles with query construction in testing.

> we'll be using a cheaper model, so adding a few examples is fine

Snippet formatting readability - Current plan uses **[MATCH: ...]** markdown bold. Alternatives: (A) Use all caps "MATCHED MESSAGE:", (B) Use ellipsis only "...", (C) Add line breaks for clarity. Recommendation: Test current format with Claude - models are good at parsing structured text, bold marker should work well.

> honestly, i have no idea what this is about. can you clarify?

Conversation ranking - When multiple conversations match, should we rank by: (A) Most recent first, (B) Most matches in conversation, (C) Match position (earlier matches ranked higher). Recommendation: Most recent first (use conversation.created_at DESC) - recency bias aligns with user expectations for "before" references.

> most recent first
