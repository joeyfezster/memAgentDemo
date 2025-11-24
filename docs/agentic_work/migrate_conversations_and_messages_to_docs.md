# Plan: Migrate Conversations to Document Model with Retrieval Support

## Objective

Migrate the 3NF conversation/message structure to a document-based model where conversations store embedded message arrays, enabling efficient retrieval for agent context while maintaining UI compatibility. Use PostgreSQL JSONB columns to store message documents natively with pgvector extension for hybrid search capabilities.

## Key Design Decisions

- **Complete migration**: Drop `messages` table entirely, no backward compatibility needed (demo context)
- **Document storage**: Store messages as JSONB array in `conversations.messages_document`
- **Vector search**: Enable pgvector extension for semantic similarity search on conversation content
- **Hybrid search**: Combine full-text search (GIN indexes) with vector similarity search
- **API compatibility**: Maintain existing API response structure so UI requires no changes
- **Search indexes**: GIN indexes on JSONB for full-text + pgvector indexes for semantic search

## Implementation Steps

### 1. Infrastructure Updates

- Add pgvector Python client library to `backend/requirements.txt`
- Update `infra/docker-compose.yml` to use PostgreSQL image with pgvector support
- Update `infra/init-db.sql` to enable pgvector extension on database creation

### 2. Database Migration (v004)

**File**: `backend/alembic/versions/v004_conversation_document_model.py`

**Actions**:

- Drop `messages` table entirely
- Add `messages_document` JSONB column to `conversations` table (default: `[]`)
- Add `embedding` vector column to `conversations` table for semantic search
- Create GIN index on `messages_document` for full-text search: `CREATE INDEX idx_messages_document_gin ON conversations USING gin (messages_document jsonb_path_ops);`
- Create GIN index for content search: `CREATE INDEX idx_messages_content_gin ON conversations USING gin ((messages_document::text) gin_trgm_ops);`
- Enable pgvector extension: `CREATE EXTENSION IF NOT EXISTS vector;`
- Create vector index on `embedding` column for similarity search

**JSONB Document Structure**:

```json
[
  {
    "id": "uuid",
    "role": "user|_agent",
    "content": "message text",
    "created_at": "ISO 8601 timestamp"
  }
]
```

### 3. Backend Model Updates

**Remove**:

- `backend/app/models/message.py` (entire file)
- `backend/app/crud/message.py` (entire file)

**Update**: `backend/app/models/conversation.py`

- Remove `messages` relationship to Message model
- Add `messages_document` Column(JSONB, nullable=False, default=[])
- Add `embedding` Column(Vector(1536)) for OpenAI embeddings
- Add helper method `add_message(role, content) -> dict` to append to JSONB array
- Add helper method `get_messages() -> list[dict]` to retrieve message array
- Add helper method `get_message_count() -> int`

**Update**: `backend/app/crud/conversation.py`

- Remove dependency on message CRUD
- Update `create_conversation` to initialize empty `messages_document` array
- Add `add_message_to_conversation(conversation_id, role, content)` to append message to JSONB
- Add `get_conversation_messages(conversation_id)` to extract messages from JSONB
- Update `list_conversations` to optionally include message count from JSONB array length

### 4. API Layer Updates

**Update**: `backend/app/schemas/chat.py`

- Keep `MessageResponse` schema unchanged (id, conversation_id, role, content, created_at)
- Keep `ConversationResponse` schema unchanged
- Internal conversion between JSONB document format and API response format

**Update**: `backend/app/api/chat.py`

- **GET `/conversations/{conversation_id}/messages`**: Extract messages from `messages_document` JSONB, convert to `MessageResponse` list
- **POST `/conversations/{conversation_id}/messages`**: Append user message and agent reply to `messages_document` JSONB array
- **POST `/conversations`**: Create conversation with empty `messages_document: []`
- Maintain auto-title generation logic after 2 messages

### 5. Retrieval Service (New)

**File**: `backend/app/services/conversation_retrieval.py`

**Functions**:

- `search_conversations_fulltext(user_id: str, query: str, limit: int) -> list[Conversation]`

  - Use PostgreSQL full-text search on JSONB content via GIN index
  - Filter by user_id for isolation

- `search_conversations_vector(user_id: str, query_embedding: list[float], limit: int) -> list[Conversation]`

  - Use pgvector cosine similarity search on embedding column
  - Return conversations ranked by semantic similarity

- `search_conversations_hybrid(user_id: str, query: str, query_embedding: list[float], limit: int, alpha: float = 0.5) -> list[Conversation]`

  - Combine full-text and vector search results with weighted scoring
  - Alpha parameter balances between lexical (1.0) and semantic (0.0) search

- `filter_messages_by_role(conversation: Conversation, role: str) -> list[dict]`

  - Extract messages from JSONB where role matches

- `filter_messages_by_date_range(conversation: Conversation, start: datetime, end: datetime) -> list[dict]`
  - Extract messages from JSONB within timestamp range

### 6. Seed Data Updates

**Update**: `backend/app/db/seed.py`

**Add conversation seeding**:

- Create 2-3 conversations for first seeded user
- Each conversation has 3-5 messages with realistic content
- Mix of "user" and "\_agent" roles
- Staggered timestamps (e.g., 1 week ago, 3 days ago, today)
- Varied content for testing retrieval:
  - Conversation 1: Technical discussion about Python features
  - Conversation 2: Project planning conversation
  - Conversation 3: Debugging help conversation
- Generate embeddings for each conversation using OpenAI API (or mock vectors for testing)

### 7. Testing

**Backend Functional Tests**: `backend/tests/test_conversation_document.py`

- Test conversation creation initializes empty messages_document
- Test adding messages appends to JSONB array correctly
- Test message ordering preserved (by created_at)
- Test GET /conversations/:id/messages returns messages in correct format
- Test POST /conversations/:id/messages creates both user and agent messages
- Test seed data creates conversations with messages
- Test auto-title generation still works
- Test user isolation (can't access other user's conversations)
- Edge cases: empty conversations, large message arrays, special characters in content

**Retrieval Tests**: `backend/tests/test_conversation_retrieval.py`

- Test full-text search finds conversations by content
- Test vector search ranks by semantic similarity
- Test hybrid search combines both methods
- Test role filtering extracts correct messages
- Test date range filtering
- Test user_id isolation in searches
- Test search performance with multiple conversations

**E2E Tests**: `e2e/tests/conversation-history.spec.ts`

- Test seeded conversation appears in sidebar with correct title
- Test clicking conversation loads all messages in chronological order
- Test new message appends to conversation and appears in UI
- Test conversation list updates with new message timestamp
- Test switching between conversations maintains message state
- Test empty conversation shows empty state correctly
- Compatible with other agent's work (check for conflicts, coordinate on shared selectors)

### 8. Validation Checklist

**Schema validation**:

- [ ] `messages` table dropped
- [ ] `conversations.messages_document` exists with JSONB type
- [ ] `conversations.embedding` exists with vector type
- [ ] GIN indexes created on messages_document
- [ ] pgvector extension enabled
- [ ] Vector index created on embedding column

**API compatibility**:

- [ ] GET /conversations returns same response structure
- [ ] GET /conversations/:id/messages returns MessageResponse array
- [ ] POST /conversations/:id/messages accepts same request format
- [ ] Frontend requires no changes

**Test coverage**:

- [ ] All backend functional tests pass
- [ ] All retrieval service tests pass
- [ ] All E2E tests pass
- [ ] Seed data creates conversations successfully

**Performance**:

- [ ] Message retrieval is fast (< 100ms for 100 messages)
- [ ] Full-text search uses GIN index (verify with EXPLAIN ANALYZE)
- [ ] Vector search uses vector index (verify with EXPLAIN ANALYZE)

## Migration Strategy

**Execution order**:

1. Update infrastructure (docker-compose, requirements.txt)
2. Create and run migration v004
3. Update models, remove message.py
4. Update CRUD operations
5. Update API endpoints
6. Create retrieval service
7. Update seed data
8. Run tests and validate

**Rollback plan**: Since this is a demo and we're dropping tables entirely, rollback would require reverting to previous migration (v003) and re-seeding database.
