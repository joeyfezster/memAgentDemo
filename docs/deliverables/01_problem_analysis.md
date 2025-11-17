## Problem Analysis: Memory in Pi

### 1. Scale and Representation of Memory

- **Context window as scarce resource:** The fundamental constraint driving memory system design is limited context window size. Not all memories can be stuffed into context for every interaction, requiring careful selection and retrieval strategies.
- **Growth of short- and long-term memory:** As chat history and repeated use grow, both short- and long-term memory can become very large, while only a small slice is relevant to any given utterance.
- **Representation form:** Not all memory should be unstructured text. Some data (POIs, time ranges, filters, KPIs, strategies) are better as structured records, some as full text, and we need a strategy for which form to use when.
- **Granularity and chunking:** If you chunk too coarsely you pull in irrelevant junk; too finely and you lose necessary context. Chunk size/boundaries become a core part of memory quality.

### 2. Memory Relevance and Consistency over Time

- **When to read/write memory:** The system needs explicit policies for when an agent should query memory, when it should summarize and write back, and how to avoid over-eager memory use or infinite tool-call loops.
- **Self-Editing Memory:** Agents can benefit from mechanisms to review, correct, and update their own memories over time. As new information is acquired or circumstances change, memories must be editable to maintain accuracy and relevance.
- **Memory as perception, not truth:** Memories represent the agent's perception of an intersubjective reality that changes over time. They are not immutable facts but interpretations that must be managed, edited, and versioned as circumstances evolve. The system needs a conflict strategy: overwrite, keep both with timestamps, and/or maintain a “current truth” view. Memory decay and versioning strategies can help manage this.

### 3. Memory Hierarchy

- **Layered scopes hierarchy:** Memory exists at multiple distinct levels with clear boundaries:

  - **Conversation-level:** Short-term, task-focused context (current session)
  - **Agent-user level:** Cross-conversation history between specific user and agent
  - **User-level:** Personal facts, preferences, and context across all interactions
  - **Team-level:** Shared knowledge within a working group
  - **Organization-level:** Company-wide standards, priorities, and patterns
  - **Platform-level:** Cross-customer patterns and best practices

  Each level needs explicit rules for access, interaction, precedence, and override behavior (e.g., user preferences override team defaults).

- **Race Conditions:** Shared memory blocks (team/org/platform level) can experience race conditions, requiring a re-implementation of write strategies such as versioning, locking, or append-only logs to prevent data loss or overwrites.
- **Tenant isolation, privacy, and IP:** Platform-wide patterns are valuable. If a super-user has previously executed an analytical pattern that can benefit other users, platform-wide memory allows this. However, customer-specific insights and results are that customer’s IP. Memory retrieval must enforce strict multi-tenant isolation so one customer’s analysis results can’t leak into another’s, even indirectly through “helpful patterns.”
- **RBAC:** When managing cross-user and cross-org memory, we need role-based access controls to govern who can read/write/promote/demote memories at each scope (user, team, org, platform).
- **Regulatory and compliance concerns:** Persistent memory interacts with GDPR/CCPA-style requirements: surfacing what’s stored, enabling deletion (“right to be forgotten”), and providing auditability (what memories were used in an answer). Given placer.ai's USA focus, this may not be an immediate concern, but if globalization is in the long-term strategy, then it should be.
- **Abuse and poisoning risks:** If users or internal power users can promote arbitrary content into shared memory or platform patterns, you risk memory poisoning, systemic bias, and hard-to-debug behavior changes. Promotion from org-level to platform-level needs review and governance.

### 5. Cost, performance, UX, and evaluation

- **Latency and cost budgets:** Every memory operation (embed, search, summarize, stuff into context) adds token cost and latency. Cost creep can be controlled if different UX paths are given explicit budgets for how much memory work is allowed.
- **Cost tracking and monetization:** Production systems need:
  - Per-query token usage monitoring (input + output + memory operations)
  - Embedding costs for memory storage and retrieval
  - Credit system for consumption-based pricing (data access + analytics + memory)
  - Cost attribution per user/org/query type for analytics and billing
- **Evaluating memory's value:** We need metrics to know if memory helps:
  - Hit-rate when a prior solution exists (cache effectiveness)
  - Quality lift vs no-memory baselines (A/B testing)
  - Reduction in repeated questions (user efficiency)
  - User-reported personalization quality (satisfaction surveys)
  - Query reduction for subsequent users in same persona (efficiency gains)
- **User mental model and control:** Users should have a clear sense of what the system "remembers," be able to inspect/edit/delete important memories, and understand (at least at a high level) when prior work is being reused.
- **Avoiding creepy or wrong personalization:** Long-term memory that's slightly wrong or too personal can feel worse than stateless behavior. Sensitive or high-impact memories may need stricter collection and recall rules, or explicit user opt-in.
- **Observability:** Given that we have new system primitives (agent memories), we need new methods to observe and understand their behavior in production.
