# Work Plan: Persona Taxonomy & Shared Memory Implementation

## Overview

Implement persona-based shared memory blocks that enable Pi agents to accumulate and share collective knowledge across users with the same professional role and industry context. When agents update their `user_persona_profile` memory block, the system creates database associations and attaches shared persona experience blocks to all agents serving users of that persona.

## Objectives

1. Establish `<industry>_<professional_role>` persona taxonomy convention
2. Create Letta shared memory blocks for each persona
3. Enable agents to discover available personas and associate users dynamically
4. Allow agents to expand taxonomy by creating new personas when properly formatted
5. Ensure shared blocks propagate to all agents serving users with same persona

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Layer                           │
│  User 1 (Sarah)        User 2 (Similar)     User 3 (Daniel) │
│  persona: qsr_real_estate  persona: qsr_real_estate  persona: tobacco_consumer_insights│
└───────────┬──────────────────┬──────────────────┬───────────┘
            │                  │                  │
            v                  v                  v
┌───────────────────────┐ ┌──────────────┐ ┌──────────────────┐
│   Agent 1             │ │  Agent 2     │ │    Agent 3       │
│ ┌───────────────────┐ │ │┌────────────┐│ │┌────────────────┐│
│ │ agent_persona (ro)│ │ ││agent_persona││ ││agent_persona  ││
│ │ human (private)   │ │ ││human       ││ ││human           ││
│ │ user_persona_prof │ │ ││user_persona││ ││user_persona    ││
│ └───────────────────┘ │ │└────────────┘│ │└────────────────┘│
│                       │ │              │ │                  │
│ ┌──────────────────┐  │ │┌────────────┐│ │┌────────────────┐│
│ │ SHARED:          │◄─┼─┼┤ SHARED:    ││ │ SHARED:         ││
│ │ qsr_real_estate_ │  │ ││ qsr_real_  ││ │ tobacco_consumer││
│ │ service_exp      │  │ ││ estate_... ││ │ _insights_...   ││
│ └──────────────────┘  │ │└────────────┘│ │└────────────────┘│
└───────────────────────┘ └──────────────┘ └──────────────────┘
```

## Key Decisions

### Taxonomy Convention

- **Format**: `<industry>_<professional_role>`
- **Examples**: `qsr_real_estate`, `tobacco_consumer_insights`
- **Documentation**: In migration comments and tool docstrings
- **Validation**: None (convention only, not enforced)

### Shared Memory Block Specification

**Label Format**: `{persona_handle}_service_experience`

**Initial Value**:

```
We have not yet gained any experience commensurate of the specific servicing of queries or analytical flows for {persona_handle} users
```

**Description**:

```
Gained experience and/or lessons learned from servicing or responding to queries typical or quintessential of users associated with the {persona_handle} persona. This memory block will be shared, and it is therefore VITAL that you not add any PII or sensitive or proprietary information about any specific user in here, e.g. POIs they're interested in, or particular and specific insights they found useful, but rather information that will help a future agent servicing a similar ask in a different instance for a different user
```

**Size Limit**: 8000 characters

### Agent Memory Update Flow

1. Agent interacts with user and identifies professional role/industry
2. Agent calls `list_available_personas()` to see taxonomy options
3. Agent calls `update_user_persona_profile_in_db(user_id, persona_handle, confidence_score)`
   - If persona exists: creates user-persona bridge, attaches shared block to agent
   - If persona doesn't exist but properly formatted: creates new Persona record (triggers lifecycle hook to create shared block), creates bridge, attaches block
4. Agent updates its local `user_persona_profile` memory block with classification details
5. Shared `{handle}_service_experience` block is now available to agent and all other agents serving users with same persona

### Database Session Injection for Tools

Tools will use the same dependency injection pattern as API routes:

- Import `get_session` from `app.db.session`
- Tools receive `AsyncSession` parameter
- Letta client must support passing context/dependencies to tools

## Implementation Steps

### 1. Create Work Plan (CURRENT)

**Status**: In Progress
**File**: `work_plan_persona_shared_memory.md`
**Description**: Document complete implementation plan with specifications

### 2. Rename v006 to v008_seed_demo_users

**Status**: Not Started
**File**: `backend/alembic/versions/v006_seed_personas.py` → `v008_seed_demo_users.py`
**Changes**:

- Rename file
- Update `revision = "seed_demo_users"`
- Update `down_revision = "drop_role_and_persona_handle"` (v007)
- Update docstring to clarify it seeds demo users, not personas

### 3. Create v006_seed_personas Migration

**Status**: Not Started
**File**: `backend/alembic/versions/v006_seed_personas.py`
**Changes**:

- Create new migration file
- `revision = "seed_personas"`
- `down_revision = "create_personas"` (v004)
- Insert two Persona records:
  1. `qsr_real_estate`: QSR/Fast Casual + Director of Real Estate
  2. `tobacco_consumer_insights`: Tobacco/CPG + Director of Consumer Insights & Activation
- Document `<industry>_<professional_role>` convention in comments
- Note: v007 will need `depends_on = ["seed_personas"]` to ensure personas exist

### 4. Create Persona Service Layer

**Status**: Not Started
**File**: `backend/app/services/persona_service.py`
**Functions**:

```python
async def get_or_create_persona_shared_block(
    client: Letta,
    persona_handle: str
) -> Block:
    """
    Get or create Letta shared memory block for persona.

    Block label: {persona_handle}_service_experience
    If exists, return without modification.
    If not exists, create with initial value and description per spec.
    """

async def attach_persona_blocks_to_agents_of_users_with_persona_handle(
    session: AsyncSession,
    client: Letta,
    persona_handle: str
) -> None:
    """
    Attach persona shared block to all agents serving users with this persona.

    - Query all users associated with persona via user_persona_bridge
    - For each user with letta_agent_id, attach block idempotently
    - Skip users without agent IDs
    """
```

### 5. Create Persona Tools

**Status**: Not Started
**File**: `backend/agent/tools/persona_tools.py`
**Functions**:

```python
def list_available_personas() -> str:
    """
    List all available persona handles with metadata.

    Returns JSON: {
      "personas": [
        {
          "persona_handle": "qsr_real_estate",
          "industry": "QSR / Fast Casual",
          "professional_role": "Director of Real Estate",
          "description": "..."
        },
        ...
      ],
      "taxonomy_format": "<industry>_<professional_role>",
      "examples": ["qsr_real_estate", "tobacco_consumer_insights"]
    }
    """

def update_user_persona_profile_in_db(
    user_id: str,
    persona_handle: str,
    confidence_score: float = 1.0
) -> str:
    """
    Associate user with persona and attach shared memory blocks.

    If persona_handle doesn't exist but follows <industry>_<professional_role>:
    - Create new Persona record (triggers lifecycle hook)
    - Parse industry and professional_role from handle
    - Set description to basic template

    If persona exists or newly created:
    - Create user_persona_bridge record
    - Attach shared block to user's agent
    - Attach shared block to all other agents of users with same persona

    Returns JSON with success/error status.
    """
```

**Note**: Tools need database session - investigate Letta tool execution context

### 6. Update pi_agent_base.af Memory Block Description

**Status**: Not Started
**File**: `backend/app/core/pi_agent_base.af`
**Changes**: Update `user_persona_profile` description (line ~24) to prepend:

```
Before updating this block, you MUST call update_user_persona_profile_in_db() with the persona_handle you've identified to ensure proper database association and shared memory attachment.

Available personas can be discovered via list_available_personas() tool. Persona handles follow the format <industry>_<professional_role> (e.g., 'qsr_real_estate', 'tobacco_consumer_insights').

If you identify a new professional role/industry combination not in the existing taxonomy, you may create a new persona by calling update_user_persona_profile_in_db() with a properly formatted handle.

After calling the tool, update this block to: (1) Identify which known persona(s) match the user's role, industry, and analytical patterns; (2) Note their professional role, industry, key metrics, typical workflows; (3) Associate multiple personas if relevant. DO NOT store: specific POI names, addresses, proprietary insights, or personal information (those go in human block or archival memory).
```

### 7. Register Persona Tools with Letta

**Status**: Not Started
**File**: `backend/app/core/letta_client.py`
**Changes**: Update `register_mock_tools()` function to include:

```python
from agent.tools import placer_tools, persona_tools

tool_functions = [
    # Existing placer tools...
    placer_tools.search_places,
    placer_tools.get_place_summary,
    placer_tools.compare_performance,
    placer_tools.get_trade_area_profile,
    placer_tools.get_audience_profile,
    placer_tools.get_visit_flows,
    # New persona tools
    persona_tools.list_available_personas,
    persona_tools.update_user_persona_profile_in_db,
]
```

### 8. Create Persona Lifecycle Hook

**Status**: Not Started
**File**: `backend/app/db/events.py` (new file)
**Implementation**:

```python
from sqlalchemy import event
from app.models.persona import Persona
from app.core.letta_client import create_letta_client
from app.services.persona_service import get_or_create_persona_shared_block
import os

@event.listens_for(Persona, 'after_insert')
def create_persona_shared_block(mapper, connection, target):
    """
    Create Letta shared memory block when new Persona is inserted.

    This ensures every persona has a corresponding shared experience block.
    """
    letta_base_url = os.getenv("LETTA_BASE_URL", "http://localhost:8283")
    letta_token = os.getenv("LETTA_SERVER_PASSWORD")

    try:
        letta_client = create_letta_client(letta_base_url, letta_token)
        # Note: This runs synchronously in DB context, may need async handling
        get_or_create_persona_shared_block(letta_client, target.persona_handle)
    except Exception as e:
        print(f"Warning: Could not create shared block for persona {target.persona_handle}: {e}")
```

**Also update**: `backend/app/db/session.py` to import events module:

```python
from app.db import events  # noqa: F401 - needed to register event listeners
```

### 9. Update seed.py with Persona Associations

**Status**: Not Started
**File**: `backend/app/db/seed.py`
**Changes**:

1. After creating Sarah and Daniel users with agents
2. Query personas by handle (`qsr_real_estate`, `tobacco_consumer_insights`)
3. Call `assign_persona_to_user()` for each user-persona pair
4. Call `attach_persona_blocks_to_agents_of_users_with_persona_handle()` for each persona to attach blocks to their agents

### 10. Testing

**Status**: Not Started
**File**: `backend/tests/letta/test_persona_shared_memory.py` (new file)
**Test Cases**:

1. Create persona → verify shared block created with correct label/value/description
2. Associate user with persona → verify block attached to user's agent
3. Multiple users with same persona → verify same block attached to all agents
4. Agent updates shared block → verify all agents see updated value
5. New persona creation via tool → verify Persona record created, block created, bridge created
6. Idempotence → attaching same block multiple times doesn't cause errors

## Open Questions & Considerations

### 1. Tool Database Session Injection

**Question**: How do Letta tools receive `AsyncSession` dependencies?
**Options**:

- Investigate if Letta supports dependency injection context
- Create global session factory pattern for tools
- Pass session via tool execution wrapper

**Decision**: TBD after investigating Letta SDK capabilities

### 2. Migration Dependencies

**Question**: Should v007 depend on v006 to ensure personas exist?
**Current**: v007 drops persona_handle from another table, doesn't reference Persona directly
**Decision**: Check v007 content, add `depends_on` if needed

### 3. Lifecycle Hook Async Handling

**Question**: SQLAlchemy event runs synchronously, but Letta client operations may be async
**Options**:

- Use synchronous Letta client wrapper
- Queue block creation for async processing
- Accept synchronous execution in event context

**Decision**: TBD based on testing

### 4. Initial Persona Block Creation in Migration

**Question**: Should v006 migration create Letta blocks explicitly?
**Issue**: Lifecycle hook won't fire during bulk insert operations
**Decision**: Yes - migration should create blocks explicitly after inserting Persona records

## Success Criteria

✅ Personas table seeded with `qsr_real_estate` and `tobacco_consumer_insights`
✅ Each persona has corresponding `{handle}_service_experience` shared block in Letta
✅ Sarah and Daniel's agents have persona blocks attached
✅ Agent can call `list_available_personas()` and see taxonomy
✅ Agent can call `update_user_persona_profile_in_db()` to associate user
✅ Shared block updates propagate to all agents with same persona
✅ Agent can create new persona with proper handle format
✅ New persona triggers block creation and attachment
✅ System is idempotent - repeated operations don't cause errors

## Timeline Estimate

- Steps 1-3: 30 minutes (migrations)
- Steps 4-5: 1 hour (service layer and tools)
- Steps 6-7: 20 minutes (config and registration)
- Steps 8-9: 40 minutes (lifecycle hook and seed updates)
- Step 10: 1 hour (testing and validation)

**Total**: ~3.5 hours
