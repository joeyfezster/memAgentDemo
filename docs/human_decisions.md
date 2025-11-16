# Project Decisions made by Human

## Core Ideas of an LLM-based Memory System

1. The context window is a scarce resource
1. Memories can be contextualized to the LLM via context-window stuffing (direct provisioning) or by informing the LLM of their potential existence (indirect provisioning), and subsequently allowing the LLM to retrieve them (e.g. via tool calls)
1. Memories are perceptions of an intersubjective reality, which can change over time, and therefore must be managed and edited accordingly.
1. There is a scope hierarchy for memories: conversation level (short term), agent-user level, user-level, team-level, org-level, platform-level
1. Memories can be structured (e.g. user data, POIs, successful analytical patterns) or unstructured (text blobs)
1. Some (but not all) memories can become less relevant over time

### Challenges of Memory Systems

1. Not all memories are always relevant. Deciding what is worth remembering and later retrieving is a core challenge
1. There are significant risks around privacy, multi-tenancy, regulatory compliance, and memory poisoning that must be managed carefully
1. Users should have visibility and control over what is remembered about them
1. Cost and latency of memory operations must be managed to avoid runaway expenses and poor UX
1. Evaluating the effectiveness of memory in improving agent performance is critical

## Development Decisions

### Tech Stack & Frameworks

1. FastAPI for backend due to its performance, async support, and modern features
1. React with Vite for frontend for fast development and modern tooling
1. PostgreSQL as the database for reliability and robustness
1. Docker and Docker Compose for containerization and easy local setup
1. Poetry for Python dependency management to ensure reproducible environments [regretting this somewhat]
1. letta for memory-enabled ai agents, but this choice is not recommended for prod. an understanding of the existing architecture is needed before making a concrete go-forward recommendation

### Letta Vs Mem0

1. While Mem0 is stated to be more production-ready, Letta is genuinely open-source and is much easier to self-host and modify. Chosen for this demo project for that reason.
1. Letta has ~20K stars and 150 contributors on GitHub, with a vibrant recent commit history, though only two merged PRs in the past month.
1. Letta does not have the concept of 'threads' or 'conversations' they believe all agent interactions should be part of the persistent memory.
   - my initial reaction is to profoundly disagree with this, as short-term-memory can be useful for ensuring the agent is focused on the current task, and reduces the potential noise from unrelated past interactions

## AI Interaction Guardrails

1. configured linters and precommit hooks to help standardize code quality across ai contributions
1. created CI jobs with functional front and backend tests to bolster confidence in ai generated code

## Additional Recommended Improvements

### Agent Model

1. This solution uses a single agent per user model. While this simplifies implementation and context continuity, it makes task-specialization more difficult. 'learned expertise' gets cluttered as the single agent has to retain the expertise across multiple tasks across multiple users. Task-specialized agents remove one complexity axis (task type).
1. the letta agent model is flexible enough

```mermaid

```

### Governance

1. Add a periodic cleanup job to remove PII from cross-user shared memory blocks

### Data Model

1. User taxonomy - having defined personas is great, but the `user_profile` block can be leveraged to discover new types of users over time. This will require a periodic discovery/review job.
1. shared object model between front and backend (e.g. User, Conversation, Message, etc) to reduce duplication and potential drift

### CI

1. Add precommit and lint jobs to ci for better code quality enforcement, covering cases of misconfigured local setups
1. Add a 2-tier review process; initial ai review followed by human review to catch nuanced issues ai might miss

## Out of Scope

1. Security posture
1. UI/UX design
