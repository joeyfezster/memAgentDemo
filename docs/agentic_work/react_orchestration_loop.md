# ReAct Orchestration Loop Implementation Plan

**Branch:** `react_agent_framework`
**Date:** 2025-11-23

## Overview

Implement server-side ReAct (Reasoning-Action-Observation) orchestration loop where our backend controls tool execution. The agent service makes iterative calls to Anthropic's API, but WE execute tools server-side and feed results back—not Anthropic.

## Key Clarifications

### Tool Execution Model: Server-Side Control

**NOT doing:** Anthropic API executes tools for us (function calling where they run the code)
**DOING:** Our backend orchestrates the loop:

1. Call Anthropic API with tool definitions
2. Anthropic responds with `tool_use` blocks (requests to call tools)
3. **WE execute the tools** in our Python backend
4. WE feed tool results back to Anthropic
5. Repeat until Anthropic returns final text response

This demonstrates full control over the agentic loop, which is the point of this demo.

### Why `to_anthropic_schema()`?

We need to convert our Tool definitions (Python Protocol/Pydantic) into Anthropic's expected JSON schema format for the `tools` parameter in their API. This tells Anthropic what tools are AVAILABLE, but we still execute them server-side.

**Anthropic API expects:**

```json
{
  "name": "search_places",
  "description": "Find POIs by geography...",
  "input_schema": {
    "type": "object",
    "properties": {...},
    "required": [...]
  }
}
```

### Frontend Tool Visibility

Currently, frontend just displays `message.content` as plain text. We need to enhance the UI to show:

- Tool calls (what tool was invoked, with what arguments)
- Tool results (what the tool returned)
- Thinking/reasoning steps (optional, nice-to-have)

This requires:

1. Backend to return structured metadata alongside content
2. Frontend to parse and render tool interactions
3. E2E tests validating the UI displays tool usage correctly

## Implementation Steps

### Step 1: Database Schema Extension

**File:** `backend/alembic/versions/v003_add_message_metadata.py`

**Migration:** Add `metadata` JSONB column to `message` table

**Rationale:**

- Keep `content` as human-readable text summary
- Store structured tool interactions in `metadata`
- Backward compatible (existing messages have NULL metadata)
- Queryable for analytics/debugging

**Schema:**

```python
# message.metadata structure
{
  "tool_interactions": [
    {
      "type": "tool_use",
      "id": "toolu_abc123",
      "name": "search_places",
      "input": {"geo_filter": {...}, "limit": 10}
    },
    {
      "type": "tool_result",
      "tool_use_id": "toolu_abc123",
      "content": {"places": [...]},
      "is_error": false
    }
  ],
  "iteration_count": 2,
  "stop_reason": "end_turn"
}
```

**Update Message model:**

```python
# backend/app/models/message.py
from sqlalchemy.dialects.postgresql import JSONB

class Message(Base):
    # ... existing fields ...
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
```

---

### Step 2: Tool Framework Foundation

**File:** `backend/app/agent/tools/base.py`

**Purpose:** Type-safe tool protocol matching LangChain patterns but minimal

**Components:**

1. **Tool Protocol:**

```python
from typing import Protocol, Any
from pydantic import BaseModel

class Tool(Protocol):
    name: str
    description: str

    def get_input_schema(self) -> dict:
        """Return JSON schema for tool inputs"""
        ...

    async def execute(self, **kwargs: Any) -> dict:
        """Execute tool and return results"""
        ...

def to_anthropic_schema(tool: Tool) -> dict:
    """Convert Tool to Anthropic's tool definition format"""
    return {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.get_input_schema()
    }
```

2. **ToolRegistry:**

```python
class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def get_anthropic_schemas(self) -> list[dict]:
        return [to_anthropic_schema(t) for t in self._tools.values()]

    async def execute(self, name: str, **kwargs: Any) -> dict:
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool {name} not found")
        return await tool.execute(**kwargs)
```

---

### Step 3: Placer Stub Tools Implementation

**File:** `backend/app/agent/tools/placer_tools.py`

**Implement 6+1 tools:**

1. `search_places` - POI discovery (foundational)
2. `get_place_summary` - Health metrics for places
3. `compare_locations` - Time-series comparison
4. `get_trade_area_profile` - Visitor origin geography
5. `get_profile_and_overlap` - Demographics/audience
6. `get_visit_flows` - Journey analysis
7. **`search_past_conversations` - Placeholder for vector store recall** ✨

**Pattern for each tool:**

```python
from pydantic import BaseModel, Field

class SearchPlacesInput(BaseModel):
    geo_filter: dict = Field(..., description="Geography filter config")
    category_ids: list[str] | None = Field(None, description="NAICS categories")
    limit: int = Field(10, description="Max results")

class SearchPlacesTool:
    name = "search_places"
    description = """Discover POIs/properties by geography and filters.
    Use this for finding candidate sites, comps, portfolio enumeration."""

    def get_input_schema(self) -> dict:
        return SearchPlacesInput.model_json_schema()

    async def execute(self, **kwargs) -> dict:
        # Validate input
        input_data = SearchPlacesInput(**kwargs)

        # Return mock data based on tool_mockups spec
        return {
            "places": [
                {
                    "id": "place_001",
                    "name": "Starbucks Reserve Roastery",
                    "address": "199 Fremont St, San Francisco, CA",
                    "lat": 37.7897,
                    "lon": -122.3972,
                    "category_id": "coffee_shop",
                    "chain_id": "starbucks",
                    "tags": ["premium", "high_traffic"]
                },
                # ... more mock places
            ],
            "total": 15,
            "query_metadata": {
                "geo_type": input_data.geo_filter.get("type"),
                "filters_applied": ["category", "geo"]
            }
        }

# Register all tools
PLACER_TOOLS = [
    SearchPlacesTool(),
    GetPlaceSummaryTool(),
    CompareLocationsTool(),
    GetTradeAreaProfileTool(),
    GetProfileAndOverlapTool(),
    GetVisitFlowsTool(),
    SearchPastConversationsTool(),  # Placeholder
]
```

**SearchPastConversationsTool placeholder:**

```python
class SearchPastConversationsTool:
    name = "search_past_conversations"
    description = """Search through previous conversations for relevant context.
    Use when user references past discussions or you need historical context."""

    def get_input_schema(self) -> dict:
        return SearchPastConversationsInput.model_json_schema()

    async def execute(self, **kwargs) -> dict:
        # TODO: Wire up to vector store after PR merges
        return {
            "conversations": [],
            "note": "Vector store integration pending"
        }
```

---

### Step 4: AgentService ReAct Loop Refactor

**File:** `backend/app/services/agent_service.py`

**Replace single-shot LLM call with iterative loop:**

```python
from app.agent.tools.base import ToolRegistry
from app.agent.tools.placer_tools import PLACER_TOOLS

class AgentService:
    def __init__(self, settings: Settings):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = agent_config.MODEL_NAME
        self.max_iterations = 10

        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        for tool in PLACER_TOOLS:
            self.tool_registry.register(tool)

    async def generate_response_with_tools(
        self,
        conversation_id: str,
        user_message_content: str,
        user: User,
        session: AsyncSession,
    ) -> tuple[str, dict]:
        """
        Generate response using ReAct loop with tool calling.

        Returns:
            tuple: (final_text_response, metadata_dict)
        """
        # Load conversation history
        messages = await message_crud.get_conversation_messages(session, conversation_id)
        anthropic_messages = self._convert_to_anthropic_format(messages)
        anthropic_messages.append({"role": "user", "content": user_message_content})

        system_prompt = agent_config.build_system_prompt(user.display_name)
        tool_schemas = self.tool_registry.get_anthropic_schemas()

        # Metadata tracking
        tool_interactions = []
        iteration_count = 0

        # ReAct loop
        while iteration_count < self.max_iterations:
            iteration_count += 1

            # 1. Call Anthropic with current message history
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=anthropic_messages,
                tools=tool_schemas,
            )

            # 2. Check stop reason
            if response.stop_reason == "end_turn":
                # Extract final text response
                final_text = self._extract_text_content(response.content)

                return final_text, {
                    "tool_interactions": tool_interactions,
                    "iteration_count": iteration_count,
                    "stop_reason": "end_turn"
                }

            elif response.stop_reason == "tool_use":
                # 3. Extract tool calls from response
                tool_use_blocks = [
                    block for block in response.content
                    if block.type == "tool_use"
                ]

                # Add assistant message with tool requests to history
                anthropic_messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # 4. Execute tools SERVER-SIDE (sequential for MVP)
                tool_results = []
                for tool_use in tool_use_blocks:
                    # Track tool call
                    tool_interactions.append({
                        "type": "tool_use",
                        "id": tool_use.id,
                        "name": tool_use.name,
                        "input": tool_use.input
                    })

                    try:
                        # WE execute the tool
                        result = await self.tool_registry.execute(
                            tool_use.name,
                            **tool_use.input
                        )

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": result
                        })

                        # Track result
                        tool_interactions.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": result,
                            "is_error": False
                        })

                    except Exception as e:
                        # Graceful error handling - let LLM see the error
                        error_msg = f"Error executing {tool_use.name}: {str(e)}"
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": error_msg,
                            "is_error": True
                        })

                        tool_interactions.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": error_msg,
                            "is_error": True
                        })

                # 5. Add tool results to conversation history
                anthropic_messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # 6. Continue loop - next iteration will call Anthropic again
                continue

            else:
                # Unexpected stop reason
                raise ValueError(f"Unexpected stop reason: {response.stop_reason}")

        # Max iterations reached
        return "I apologize, but I've reached my processing limit. Please try rephrasing your question.", {
            "tool_interactions": tool_interactions,
            "iteration_count": iteration_count,
            "stop_reason": "max_iterations"
        }

    def _extract_text_content(self, content_blocks: list) -> str:
        """Extract text from content blocks, ignoring tool_use blocks"""
        text_parts = []
        for block in content_blocks:
            if hasattr(block, 'text'):
                text_parts.append(block.text)
        return "\n".join(text_parts)
```

---

### Step 5: Update Chat API Endpoint

**File:** `backend/app/api/chat.py`

**Minimal changes - maintain API contract:**

```python
@router.post("/conversations/{conversation_id}/messages")
async def send_message_to_conversation(
    conversation_id: str,
    message: SendMessageRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> SendMessageResponse:
    # Validate conversation ownership (existing logic)
    conv = await conversation_crud.get_conversation(session, conversation_id)
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Create user message
    user_message = await message_crud.create_message(
        session,
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=message.content,
        metadata=None,  # User messages don't have tool metadata
    )

    # Generate response WITH TOOLS
    agent_service = AgentService(settings)
    assistant_text, assistant_metadata = await agent_service.generate_response_with_tools(
        conversation_id=conversation_id,
        user_message_content=message.content,
        user=current_user,
        session=session,
    )

    # Create assistant message with metadata
    assistant_message = await message_crud.create_message(
        session,
        conversation_id=conversation_id,
        role=MessageRole.AGENT,
        content=assistant_text,
        metadata=assistant_metadata,  # Store tool interactions
    )

    # Auto-generate title (existing logic)
    message_count = await message_crud.count_conversation_messages(session, conversation_id)
    if message_count == 2 and not conv.title:
        # ... existing title generation logic ...

    await session.commit()
    await session.refresh(user_message)
    await session.refresh(assistant_message)

    return SendMessageResponse(
        user_message=user_message,
        assistant_message=assistant_message,
    )
```

**Update message CRUD:**

```python
# backend/app/crud/message.py

async def create_message(
    session: AsyncSession,
    conversation_id: str,
    role: MessageRole,
    content: str,
    metadata: dict | None = None,  # NEW parameter
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        metadata=metadata,  # Store structured tool data
    )
    session.add(message)
    await session.flush()
    return message
```

---

### Step 6: Backend Integration Tests

**File:** `backend/tests/test_agent_tools.py`

**No mocking policy - test with real Anthropic API:**

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import conversation as conversation_crud
from app.crud import message as message_crud
from app.models.user import User
from app.services.agent_service import AgentService
from app.core.config import get_settings

pytestmark = pytest.mark.asyncio

@pytest.fixture
def settings():
    return get_settings()

class TestAgentToolCalling:
    """Test ReAct loop with tool execution"""

    async def test_single_tool_call_search_places(
        self,
        session: AsyncSession,
        test_user: User,
        settings,
    ):
        """User asks to find places, agent calls search_places once"""
        # Create conversation
        conv = await conversation_crud.create_conversation(session, test_user.id)
        await session.commit()

        # User query requiring tool use
        user_query = "Find the top 5 Starbucks locations in San Francisco"

        # Agent service
        agent_service = AgentService(settings)
        response_text, metadata = await agent_service.generate_response_with_tools(
            conversation_id=conv.id,
            user_message_content=user_query,
            user=test_user,
            session=session,
        )

        # Assertions
        assert response_text  # Got a response
        assert metadata["stop_reason"] == "end_turn"
        assert metadata["iteration_count"] >= 1

        # Check tool was called
        tool_interactions = metadata["tool_interactions"]
        assert len(tool_interactions) > 0

        # Find search_places call
        tool_uses = [t for t in tool_interactions if t["type"] == "tool_use"]
        assert any(t["name"] == "search_places" for t in tool_uses)

        # Check we got results back
        tool_results = [t for t in tool_interactions if t["type"] == "tool_result"]
        assert len(tool_results) > 0
        assert not any(t.get("is_error") for t in tool_results)

        # Response should mention results
        assert "starbucks" in response_text.lower() or "coffee" in response_text.lower()

    async def test_multi_tool_sequence(
        self,
        session: AsyncSession,
        test_user: User,
        settings,
    ):
        """Agent makes multiple tool calls in sequence"""
        conv = await conversation_crud.create_conversation(session, test_user.id)
        await session.commit()

        # Query requiring search + summary
        user_query = "Find Chick-fil-A locations in Atlanta and tell me how they're performing"

        agent_service = AgentService(settings)
        response_text, metadata = await agent_service.generate_response_with_tools(
            conversation_id=conv.id,
            user_message_content=user_query,
            user=test_user,
            session=session,
        )

        # Should have called multiple tools
        tool_uses = [
            t for t in metadata["tool_interactions"]
            if t["type"] == "tool_use"
        ]
        assert len(tool_uses) >= 2  # At minimum: search + summary

        # Check expected tools were called
        tool_names = {t["name"] for t in tool_uses}
        assert "search_places" in tool_names
        assert "get_place_summary" in tool_names or "compare_locations" in tool_names

    async def test_tool_error_handling(
        self,
        session: AsyncSession,
        test_user: User,
        settings,
    ):
        """Agent handles tool execution errors gracefully"""
        # This would require injecting a failing tool or bad input
        # For MVP, verify structure supports error tracking
        conv = await conversation_crud.create_conversation(session, test_user.id)
        await session.commit()

        # Query that might trigger edge case (depends on tool implementation)
        user_query = "Find places with invalid parameters"

        agent_service = AgentService(settings)
        response_text, metadata = await agent_service.generate_response_with_tools(
            conversation_id=conv.id,
            user_message_content=user_query,
            user=test_user,
            session=session,
        )

        # Agent should still produce a response
        assert response_text
        assert metadata["stop_reason"] in ["end_turn", "max_iterations"]

    async def test_max_iterations_safety(
        self,
        session: AsyncSession,
        test_user: User,
        settings,
    ):
        """Agent stops after max iterations"""
        conv = await conversation_crud.create_conversation(session, test_user.id)
        await session.commit()

        # Complex query that might cause loops
        user_query = "Analyze every coffee shop in the United States"

        agent_service = AgentService(settings)
        agent_service.max_iterations = 3  # Lower for testing

        response_text, metadata = await agent_service.generate_response_with_tools(
            conversation_id=conv.id,
            user_message_content=user_query,
            user=test_user,
            session=session,
        )

        # Should hit limit
        assert metadata["iteration_count"] <= 3
        if metadata["stop_reason"] == "max_iterations":
            assert "limit" in response_text.lower() or "apologize" in response_text.lower()

    async def test_conversation_persistence_with_tools(
        self,
        session: AsyncSession,
        test_user: User,
        settings,
    ):
        """Tool interactions are properly stored in message.metadata"""
        conv = await conversation_crud.create_conversation(session, test_user.id)
        await session.commit()

        user_query = "Find shopping malls in Los Angeles"

        # Create messages via endpoint flow
        user_msg = await message_crud.create_message(
            session,
            conversation_id=conv.id,
            role=MessageRole.USER,
            content=user_query,
            metadata=None,
        )

        agent_service = AgentService(settings)
        response_text, metadata = await agent_service.generate_response_with_tools(
            conversation_id=conv.id,
            user_message_content=user_query,
            user=test_user,
            session=session,
        )

        assistant_msg = await message_crud.create_message(
            session,
            conversation_id=conv.id,
            role=MessageRole.AGENT,
            content=response_text,
            metadata=metadata,
        )
        await session.commit()

        # Reload from DB
        await session.refresh(assistant_msg)

        # Verify metadata stored correctly
        assert assistant_msg.metadata is not None
        assert "tool_interactions" in assistant_msg.metadata
        assert "iteration_count" in assistant_msg.metadata
        assert isinstance(assistant_msg.metadata["tool_interactions"], list)
```

---

### Step 7: Frontend Tool Visibility Enhancement

**Files:**

- `frontend/src/components/ChatWindow.tsx`
- `frontend/src/components/ToolInteraction.tsx` (new)
- `frontend/src/api/client.ts`

**API Response already includes metadata (from Message model serialization)**

**Update API client types:**

```typescript
// frontend/src/api/client.ts

export type ToolInteraction = {
  type: "tool_use" | "tool_result";
  id?: string;
  tool_use_id?: string;
  name?: string;
  input?: Record<string, any>;
  content?: any;
  is_error?: boolean;
};

export type MessageMetadata = {
  tool_interactions?: ToolInteraction[];
  iteration_count?: number;
  stop_reason?: string;
};

export type Message = {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  metadata?: MessageMetadata | null;
};
```

**Create ToolInteraction component:**

```tsx
// frontend/src/components/ToolInteraction.tsx

import type { ToolInteraction as ToolInteractionType } from "../api/client";

type ToolInteractionProps = {
  interaction: ToolInteractionType;
};

export function ToolInteraction({ interaction }: ToolInteractionProps) {
  if (interaction.type === "tool_use") {
    return (
      <div className="tool-interaction tool-interaction--use">
        <div className="tool-interaction__header">
          <span className="tool-interaction__icon">🔧</span>
          <span className="tool-interaction__name">
            Calling: {interaction.name}
          </span>
        </div>
        {interaction.input && (
          <details className="tool-interaction__details">
            <summary>View parameters</summary>
            <pre className="tool-interaction__json">
              {JSON.stringify(interaction.input, null, 2)}
            </pre>
          </details>
        )}
      </div>
    );
  }

  if (interaction.type === "tool_result") {
    return (
      <div
        className={`tool-interaction tool-interaction--result ${
          interaction.is_error ? "tool-interaction--error" : ""
        }`}
      >
        <div className="tool-interaction__header">
          <span className="tool-interaction__icon">
            {interaction.is_error ? "❌" : "✅"}
          </span>
          <span className="tool-interaction__name">
            {interaction.is_error ? "Error" : "Result received"}
          </span>
        </div>
        {interaction.content && (
          <details className="tool-interaction__details">
            <summary>View response</summary>
            <pre className="tool-interaction__json">
              {typeof interaction.content === "string"
                ? interaction.content
                : JSON.stringify(interaction.content, null, 2)}
            </pre>
          </details>
        )}
      </div>
    );
  }

  return null;
}
```

**Update ChatWindow to render tool interactions:**

```tsx
// frontend/src/components/ChatWindow.tsx

import { ToolInteraction } from "./ToolInteraction";

// In message rendering:
{
  !isLoading &&
    messages.map((message) => (
      <div
        key={message.id}
        className={`chat__message chat__message--${message.sender}`}
      >
        <span className="chat__message-label">
          {message.sender === "user" ? user.display_name : "Assistant"}
        </span>

        {/* Render tool interactions if present */}
        {message.metadata?.tool_interactions && (
          <div className="chat__tool-interactions">
            {message.metadata.tool_interactions.map((interaction, idx) => (
              <ToolInteraction key={idx} interaction={interaction} />
            ))}
          </div>
        )}

        {/* Final text response */}
        <p className="chat__message-text">{message.text}</p>
      </div>
    ));
}
```

**Add CSS styling:**

```css
/* Add to existing styles */
.chat__tool-interactions {
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.tool-interaction {
  background: #f8f9fa;
  border-left: 3px solid #007bff;
  padding: 0.75rem;
  border-radius: 4px;
  font-size: 0.875rem;
}

.tool-interaction--error {
  border-left-color: #dc3545;
  background: #fff5f5;
}

.tool-interaction__header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}

.tool-interaction__icon {
  font-size: 1rem;
}

.tool-interaction__details {
  margin-top: 0.5rem;
}

.tool-interaction__json {
  background: #fff;
  padding: 0.5rem;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 0.75rem;
  max-height: 200px;
  overflow-y: auto;
}
```

---

### Step 8: E2E Playwright Tests for Tool Visibility

**File:** `e2e/tests/chat.spec.ts`

**Add tests validating UI displays tool usage:**

```typescript
test("should display tool interactions when agent uses tools", async ({
  page,
}) => {
  await test.step("Create new conversation", async () => {
    await page.locator(".new-chat-button").click();
    await page.waitForTimeout(500);
  });

  await test.step("Send message requiring tool use", async () => {
    const messageInput = page.getByPlaceholder(/type.*message/i);
    await expect(messageInput).toBeEditable({ timeout: 10000 });

    // Query that should trigger search_places tool
    await messageInput.fill("Find Starbucks locations in San Francisco");

    const sendButton = page.getByRole("button", { name: /send/i });
    await sendButton.click();
  });

  await test.step("Verify tool interaction UI elements appear", async () => {
    // Wait for assistant response
    const assistantMessage = page.locator(".chat__message--assistant").first();
    await expect(assistantMessage).toBeVisible({ timeout: 20000 });

    // Check for tool interactions container
    const toolInteractions = page.locator(".chat__tool-interactions");
    await expect(toolInteractions).toBeVisible();

    // Check for tool use indicator
    const toolUse = page.locator(".tool-interaction--use");
    await expect(toolUse).toBeVisible();

    // Should show tool name
    await expect(toolUse).toContainText("search_places");

    // Check for tool result
    const toolResult = page.locator(".tool-interaction--result");
    await expect(toolResult).toBeVisible();
    await expect(toolResult).toContainText(/result received/i);
  });

  await test.step("Verify tool details are expandable", async () => {
    // Click to expand parameters
    const paramDetails = page.locator(".tool-interaction--use details");
    await paramDetails.click();

    // Should show JSON parameters
    const jsonContent = page.locator(".tool-interaction__json");
    await expect(jsonContent).toBeVisible();

    // Should contain expected parameter structure
    const jsonText = await jsonContent.textContent();
    expect(jsonText).toContain("geo_filter");
  });

  await test.step("Verify final text response is displayed", async () => {
    const messageText = page.locator(".chat__message-text").last();
    await expect(messageText).toBeVisible();

    const text = await messageText.textContent();
    expect(text).toBeTruthy();
    expect(text!.length).toBeGreaterThan(0);
  });
});

test("should handle multiple tool calls in sequence", async ({ page }) => {
  await test.step("Create new conversation", async () => {
    await page.locator(".new-chat-button").click();
    await page.waitForTimeout(500);
  });

  await test.step("Send complex query requiring multiple tools", async () => {
    const messageInput = page.getByPlaceholder(/type.*message/i);
    await messageInput.fill(
      "Find Chick-fil-A restaurants in Atlanta and tell me how they're performing",
    );
    await page.getByRole("button", { name: /send/i }).click();
  });

  await test.step("Verify multiple tool interactions displayed", async () => {
    const assistantMessage = page.locator(".chat__message--assistant").first();
    await expect(assistantMessage).toBeVisible({ timeout: 30000 });

    // Should show multiple tool uses
    const toolUses = page.locator(".tool-interaction--use");
    const toolUseCount = await toolUses.count();
    expect(toolUseCount).toBeGreaterThanOrEqual(2);

    // Should show corresponding results
    const toolResults = page.locator(".tool-interaction--result");
    const resultCount = await toolResults.count();
    expect(resultCount).toBeGreaterThanOrEqual(2);
  });
});

test("should display error when tool execution fails", async ({ page }) => {
  await test.step("Create new conversation", async () => {
    await page.locator(".new-chat-button").click();
    await page.waitForTimeout(500);
  });

  await test.step("Send query that might cause tool error", async () => {
    const messageInput = page.getByPlaceholder(/type.*message/i);
    // This depends on tool implementation - may need to adjust
    await messageInput.fill("Find places with completely invalid nonsense");
    await page.getByRole("button", { name: /send/i }).click();
  });

  await test.step("Verify error handling in UI", async () => {
    const assistantMessage = page.locator(".chat__message--assistant").first();
    await expect(assistantMessage).toBeVisible({ timeout: 20000 });

    // Check if error state is shown (if error occurred)
    const errorResult = page.locator(".tool-interaction--error");
    if (await errorResult.isVisible()) {
      await expect(errorResult).toContainText(/error/i);
    }

    // Agent should still provide a text response
    const messageText = page.locator(".chat__message-text").last();
    await expect(messageText).toBeVisible();
  });
});
```

---

## Implementation Checklist

- [ ] Step 1: Create migration `v003_add_message_metadata.py`
- [ ] Step 1: Update Message model with metadata field
- [ ] Step 1: Run migration: `make db-migrate`
- [ ] Step 2: Create `backend/app/agent/tools/base.py`
- [ ] Step 3: Create `backend/app/agent/tools/placer_tools.py` with all 7 tools
- [ ] Step 4: Refactor `backend/app/services/agent_service.py` with ReAct loop
- [ ] Step 5: Update `backend/app/api/chat.py` endpoint
- [ ] Step 5: Update `backend/app/crud/message.py` for metadata
- [ ] Step 6: Create `backend/tests/test_agent_tools.py`
- [ ] Step 6: Run backend tests: `pytest backend/tests/test_agent_tools.py`
- [ ] Step 7: Update `frontend/src/api/client.ts` types
- [ ] Step 7: Create `frontend/src/components/ToolInteraction.tsx`
- [ ] Step 7: Update `frontend/src/components/ChatWindow.tsx`
- [ ] Step 7: Add CSS styles for tool interactions
- [ ] Step 8: Add E2E tests to `e2e/tests/chat.spec.ts`
- [ ] Step 8: Run E2E tests: `cd e2e && pnpm test`
- [ ] Final: Manual testing with various tool-requiring queries
- [ ] Final: Code review and PR submission

## Success Criteria

✅ Agent can call tools iteratively in a ReAct loop
✅ All tool execution happens server-side (we control it)
✅ Tool interactions stored in message.metadata
✅ Frontend displays tool calls and results visually
✅ E2E tests validate tool UI rendering
✅ Placeholder for conversation recall tool exists
✅ No mocking in tests - real Anthropic API integration
✅ Max iteration safety prevents infinite loops
✅ Error handling provides graceful degradation

## Next Phase Considerations

- Streaming support (WebSocket endpoint)
- Parallel tool execution (asyncio.gather)
- Tool result summarization for large outputs
- Wire up `search_past_conversations` to vector store
- Advanced planning (todo list integration)
- Tool usage analytics and monitoring
