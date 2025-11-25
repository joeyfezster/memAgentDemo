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

### Developed Memory Mechanisms

1. Conversational message memory: previous messages in conversation are stored and retrieved as context for future messages and compiled into the next llm turn
1. Long-term conversational retrieval memory: all previous conversations and messages are stored in a document store + vector store (PostgreSQL's JSONB + pgvector). Relevant past messages can be retrieved via keyword, embedding, hibrid, time-bound retrieval strategies (these must be provided to the agent as a tool)

### Tech Stack & Frameworks

1. FastAPI for backend due to its performance, async support, and modern features
1. React with Vite for frontend for fast development and modern tooling
1. PostgreSQL + PGVector as the database for reliability and robustness
1. Docker and Docker Compose for containerization and easy local setup
1. Pip for Python dependency management
1. Anthropic's Claude 3 as the LLM for its capabilities and alignment features
1. Bare bones orchestration layer without agent frameworks

### AI Interaction Guardrails

1. configured linters and precommit hooks to help standardize code quality across ai contributions
1. created CI jobs with functional front and backend tests to bolster confidence in ai generated code

## Additional Recommended Improvements

### Agent Model

1. The conversation history is passed completely as context to the LLM for each turn, with no summarization or trimming for now. One way to address this could be a clever summarization strategy for conversation with messages that go beyond some threshold

### Memory Model

1. A basic keyword-based retrieval tool has been implemented, and an embedding-based retrieval tool is in progress. Further retrieval strategies could be added.

### Cost Model

1. Implement a cost tracking system to monitor per-query token usage, embedding costs, and overall expenses related to memory operations.
1. Create a credit system for effective pricing per consumption of data + analytics (tokens).

### Governance

1. Add a tool permission management aspect to the agent model.
1. Token budgets and cost tracking per user/agent.

### Data Model

1.

### Switching Costs

1. Both the LLM providers and the backend postgres db are somewhat modular and swappable, but the switching costs are non-trivial as i've not focused on the absolute decoupling. A particular point is the tool model.

### CI

1. Add precommit and lint jobs to ci for better code quality enforcement, covering cases of misconfigured local setups
1. Add a 2-tier review process; initial ai review followed by human review to catch nuanced issues ai might miss
1. Add CI tests for end-to-end user flows to catch integration issues between front and backend, this is partially implemented.

## Out of Scope

1. Security posture
1. UI/UX design
1. Observability (logging, monitoring, alerting)
