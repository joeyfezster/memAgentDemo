# Agent-Managed User Memory JSONB Document - FINALIZED PLAN

## Overview

Adding a `memory_document` JSONB field to the User table will enable persistent, cross-conversation memory for user preferences, personal information, and agent-learned facts. This builds on the existing JSONB document pattern used for `messages_document` in Conversations.

**Key Clarification**: Like Conversation.messages_document, the memory_document uses an immutable update pattern (`self.memory_document = {**self.memory_document, ...}`) which creates a new dict/list to trigger SQLAlchemy change detection. The entire JSONB document is replaced in the database on each update - there's only ONE memory_document per user row.

## Implementation Steps

### Step 1: Token Counting Infrastructure

**Action**: Add `tiktoken` to `requirements.txt` and create token counting utility.

**Details**:

- Add `tiktoken==0.5.2` to `backend/requirements.txt`
- Create `count_tokens(text: str, model: str = "cl100k_base") -> int` in `backend/app/core/utils.py`
- Use Anthropic's recommended encoding for Claude models

### Step 2: Pydantic Type Definitions

**Action**: Create comprehensive type definitions for memory document structure.

**Location**: `backend/app/models/types.py` (add to existing file)

**Types to Create**:

```python
POIMention = tuple[str, str]  # (message_id, timestamp_iso8601)
POIMentions = dict[str, list[POIMention]]  # conversation_id -> mentions

class PlacerUserDatapoint(BaseModel):
    pass

class PlacerPOI(PlacerUserDatapoint):
    place_id: str
    place_name: str
    notes: str | None = None
    mentioned_in: POIMentions = Field(default_factory=dict)
    added_at: str

class MemoryFact(BaseModel):
    id: str
    content: str = Field(min_length=1, max_length=500)
    added_at: str
    source_conversation_id: str | None = None
    source_message_id: str | None = None
    is_active: bool = True

class MemoryMetadata(BaseModel):
    last_updated: str
    total_facts: int
    total_active_facts: int
    total_pois: int
    token_count: int
    schema_version: str = "1.0"

class MemoryDocument(BaseModel):
    facts: list[MemoryFact] = Field(default_factory=list)
    placer_user_datapoints: list[PlacerUserDatapoint] = Field(default_factory=list)
    metadata: MemoryMetadata
```

### Step 3: Database Migration

**Action**: Create `backend/alembic/versions/m004_add_user_memory_document.py`

**Details**:

- Add JSONB column `memory_document` to `user` table
- Set `server_default='{}'`
- Create GIN index: `CREATE INDEX ix_user_memory_document ON user USING gin (memory_document)`
- Follow pattern from `m003_conversation_document_model.py`

### Step 4: User Model Enhancement

**Action**: Update `backend/app/models/user.py` with memory_document field and helper methods.

**Field Definition**:

```python
memory_document: Mapped[dict] = mapped_column(
    JSON().with_variant(JSONB, "postgresql"),
    nullable=False,
    server_default=text("'{}'")
)
```

**Helper Methods** (all use immutable update pattern):

1. `add_fact(content: str, source_conversation_id: str | None, source_message_id: str | None) -> str`

   - Creates new MemoryFact with UUID
   - Appends to facts list using `[*self.get_memory().facts, new_fact]`
   - Updates metadata (token_count, totals, last_updated)
   - Returns fact_id

2. `deactivate_fact(fact_id: str) -> bool`

   - Finds fact by id, sets `is_active=False`
   - Rebuilds facts list immutably
   - Updates metadata
   - Returns True if found, False otherwise

3. `add_poi(place_id: str, place_name: str, notes: str | None, conversation_id: str, message_id: str) -> str`

   - Creates new PlacerPOI with initial mention
   - Appends to placer_user_datapoints list
   - Updates metadata
   - Returns place_id

4. `add_poi_mention(place_id: str, conversation_id: str, message_id: str) -> bool`

   - Finds POI by place_id
   - Adds mention to mentioned_in dict
   - Rebuilds POI list immutably
   - Returns True if found

5. `get_memory() -> MemoryDocument`

   - Parses memory_document dict into MemoryDocument Pydantic model
   - Returns empty/initialized MemoryDocument if empty dict

6. `get_active_facts() -> list[MemoryFact]`

   - Filters facts where `is_active=True`

7. `_update_metadata() -> MemoryMetadata`

   - Recalculates token_count using `count_tokens(self.memory_document_json())`
   - Updates totals (total_facts, total_active_facts, total_pois)
   - Sets last_updated to current UTC ISO8601
   - Returns new metadata

8. `_enforce_token_limit(max_tokens: int = 10000) -> int` (STRETCH GOAL)
   - If token_count > max_tokens:
     - Sort facts: inactive first, then by oldest added_at
     - Remove facts one-by-one until under limit
     - Update metadata
   - Returns number of facts evicted

### Step 5: CRUD Operations

**Action**: Add memory management functions to `backend/app/crud/user.py`

**Functions**:

1. `async add_user_memory_fact(session: AsyncSession, user_id: str, content: str, source_conversation_id: str | None, source_message_id: str | None) -> str`

   - Get user with user_id check
   - Call `user.add_fact(...)`
   - Commit transaction
   - Return fact_id

2. `async deactivate_user_memory_fact(session: AsyncSession, user_id: str, fact_id: str) -> bool`

   - Get user with user_id check
   - Call `user.deactivate_fact(fact_id)`
   - Commit if found
   - Return success boolean

3. `async add_user_memory_poi(session: AsyncSession, user_id: str, place_id: str, place_name: str, notes: str | None, conversation_id: str, message_id: str) -> str`

   - Get user with user_id check
   - Call `user.add_poi(...)`
   - Commit transaction
   - Return place_id

4. `async get_user_memory(session: AsyncSession, user_id: str) -> MemoryDocument`
   - Get user with user_id check
   - Return `user.get_memory()`

### Step 6: Agent Tool Implementation

**Action**: Create `ManageUserMemoryTool` in `backend/app/agent/tools/`

**Tool Design**:

- **Name**: `manage_user_memory`
- **Single tool with operation parameter** to minimize context window usage
- **Operations**: `add_fact`, `deactivate_fact`, `add_poi`, `get_memory`

**Tool Description** (guides agent when to use):

```
Use this tool to store and retrieve persistent facts about the user that should be remembered across all conversations.

WHEN TO USE:
- User shares personal information (name, preferences, interests, location)
- User mentions places they care about (home, work, favorite spots)
- User explicitly asks you to remember something
- User corrects previous information (deactivate old fact, add new one)

WHAT TO STORE:
- Personal details: "User's name is Alex", "User prefers morning workouts"
- Preferences: "User likes Italian food", "User is vegetarian"
- Context: "User lives in Seattle", "User works in tech industry"
- Places: User's home address, workplace, frequently mentioned locations

DO NOT STORE:
- Sensitive data (passwords, SSN, financial info)
- Temporary information (today's weather, one-time events)
- Information user hasn't shared or confirmed
```

**Input Schema** (Pydantic model):

```python
class ManageUserMemoryInput(BaseModel):
    operation: Literal["add_fact", "deactivate_fact", "add_poi", "get_memory"]
    content: str | None = Field(None, description="For add_fact: the fact to remember")
    fact_id: str | None = Field(None, description="For deactivate_fact: the UUID of fact to deactivate")
    place_id: str | None = Field(None, description="For add_poi: unique identifier for place")
    place_name: str | None = Field(None, description="For add_poi: human-readable name")
    notes: str | None = Field(None, description="For add_poi: additional context")
```

**Execute Method**:

- Call appropriate CRUD function based on operation
- Include current conversation_id and message_id from context
- Return formatted result dict

**Registration**:

- Register in `ToolRegistry`
- Add to agent_service.py tool initialization

### Step 7: System Prompt Integration

**Action**: Update `backend/app/services/agent_service.py` to load memory into system prompt

**Details**:

1. Add current datetime to system prompt:

   ```python
   f"Current datetime: {datetime.now(timezone.utc).isoformat()}"
   ```

2. Load user memory on FIRST message only:

   - Check `conversation.get_message_count() == 0`
   - If true, fetch user memory via `get_user_memory(session, user_id)`
   - Format active facts with timestamps:

     ```
     USER'S STORED MEMORIES:
     - [2024-11-20] User's name is Alex
     - [2024-11-22] User prefers morning workouts
     - [2024-11-23] User lives in Seattle

     PLACES OF INTEREST:
     - Home: 123 Main St, Seattle (mentioned in 3 conversations)
     ```

   - Inject into system prompt BEFORE conversation history

3. On subsequent messages in same conversation, skip memory loading (already in context)

### Step 8: Comprehensive Testing

**Action**: Write tests following project patterns

**Test Files**:

1. `backend/tests/unit/test_user_memory_model.py` (non-expensive)

   - Test all User model helper methods
   - Test immutable update pattern
   - Test metadata calculation
   - Test token limit enforcement (stretch goal)

2. `backend/tests/unit/test_user_memory_crud.py` (non-expensive)

   - Test all CRUD operations
   - Test user isolation
   - Test transaction rollback on error

3. `backend/tests/test_user_memory_tool.py` (non-expensive)

   - Test ManageUserMemoryTool execution
   - Test input validation
   - Test all operations

4. `backend/tests/test_agent_user_memory.py` (expensive - mark with `@pytest.mark.expensive`)
   - Test agent stores facts when user shares information
   - Test agent retrieves and references stored memories
   - Test agent deactivates outdated facts
   - Test cross-conversation memory persistence
   - **Use model: `claude-sonnet-4-20250514`** (matching other expensive tests)

**Test Patterns**:

- Use `test_cases = [(input, expected), ...]` with for loops
- No mocking unless absolutely necessary
- Functional tests with real database

### Step 9: LRU Eviction Strategy (STRETCH GOAL)

**Action**: Implement automatic pruning when memory exceeds 10K tokens

**Algorithm**:

1. After each add operation, call `_enforce_token_limit(10000)`
2. If over limit:
   - Sort facts: `is_active=False` first, then by oldest `added_at` timestamp
   - Remove facts one by one until `token_count <= 10000`
   - Update metadata with new counts
3. Log evictions for future analysis (use existing logger)
4. Return count of evicted facts

**Logging**:

- Log at WARNING level: `f"Evicted {count} facts for user {user_id} due to token limit"`
- Include list of evicted fact IDs for debugging

## Design Decisions

### Last-Write-Wins for Concurrent Updates

- Multiple simultaneous conversations can update memory
- No optimistic locking - last update wins
- Log all memory updates with user_id, conversation_id, timestamp for future conflict analysis

### No Eviction Notification to Agent

- Agent is NOT informed when facts are evicted (avoid confusion)
- Stretch goal: Could add eviction log to tool response in future

### Type Clarity for POI Mentions

- Create explicit types: `POIMention = tuple[str, str]` and `POIMentions = dict[str, list[POIMention]]`
- Makes structure clear and enables type checking

### Memory Loading Strategy

- Load full memory on first message (max 10K tokens is manageable)
- Simpler than selective retrieval tool
- Agent has complete context for better responses

## Success Criteria

1. ✅ User model has memory_document JSONB field with helper methods
2. ✅ Agent can store facts when user shares information
3. ✅ Agent can retrieve and reference stored memories
4. ✅ Memories persist across conversations
5. ✅ Token limit enforcement prevents memory growth beyond 10K tokens (stretch)
6. ✅ Comprehensive test coverage (unit + integration + agent tests)
7. ✅ Current datetime in system prompt enables temporal reasoning
