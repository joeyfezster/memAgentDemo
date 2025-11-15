## Problem Analysis: Memory in Pi

### 1. Scale, relevance, and representation of memory
- **Growth of short- and long-term memory:** As chat history and repeated use grow, both short- and long-term memory can become very large, while only a small slice is relevant to any given utterance.
- **Signal vs noise:** Raw logs contain a lot of junk (greetings, dead-ends, random exploration). There needs to be a clear policy for what becomes memory (stable facts, conclusions, validated insights) vs what’s ignored.
- **Representation form:** Not all memory should be unstructured text. Some data (POIs, time ranges, filters, KPIs, strategies) are better as structured records, some as full text, and we need a strategy for which form to use when.
- **Granularity and chunking:** If you chunk too coarsely you pull in irrelevant junk; too finely and you lose necessary context. Chunk size/boundaries become a core part of memory quality.

### 2. Time, staleness, and consistency of facts
- **Staleness and versioning:** User/org priorities, geos, and strategies change. Memory needs aging/decay, TTLs, and versioned facts (“as of Q4 2023…”) so stale information doesn’t drive new answers.
- **Conflicting truths over time:** Users will say things that contradict earlier statements (“we focus on malls” → “we’re shifting to open-air”). The system needs a conflict strategy: overwrite, keep both with timestamps, and/or maintain a “current truth” view.

### 3. Cross-chat, agent, and platform-wide memory
- **Cross-chat / cross-agent memory:** Traditional chat history in the context window gives only local, short-term memory. Pi needs long-term memory across chats and the ability for agents to “see” relevant prior work from other sessions, without exposing unrelated or sensitive content.
- **Layered scopes:** Memory exists at multiple levels within the user (current task, previous tasks, other/fuller context s.a. email, slack, etc) as well as cross-users (teams, orgs, placer.ai platform). We need clear rules for how these layers interact, which layer is read first, and how overrides work (personal vs team vs org defaults).
- **Tenant isolation, privacy, and IP:** Platform-wide patterns are valuable. If a super-user has previously executed an analytical pattern that can benefit other users, platform-wide memory allows this. However, customer-specific insights and results are that customer’s IP. Memory retrieval must enforce strict multi-tenant isolation so one customer’s analysis results can’t leak into another’s, even indirectly through “helpful patterns.” 
- **RBAC-like controls:** When managing cross-user and cross-org memory, we need role-based access controls to govern who can read/write/promote/demote memories at each scope (user, team, org, platform).
- **Regulatory and compliance concerns:** Persistent memory interacts with GDPR/CCPA-style requirements: surfacing what’s stored, enabling deletion (“right to be forgotten”), and providing auditability (what memories were used in an answer). Given placer.ai's USA focus, this may not be an immediate concern, but if globalization is in the long-term strategy, then it should be.
- **Abuse and poisoning risks:** If users or internal power users can promote arbitrary content into shared memory or platform patterns, you risk memory poisoning, systemic bias, and hard-to-debug behavior changes. Promotion from org-level to platform-level needs review and governance.

### 4. Agent behavior, orchestration, and tooling
- **When to read/write memory:** The system needs explicit policies for when an agent should query memory, when it should summarize and write back, and how to avoid over-eager memory use or infinite tool-call loops.
- **Tool and model robustness:** Memory access usually goes through tools/function calls. If schemas are too complex or prompts unclear, models will misuse or ignore memory. Schemas must be simple and consistent enough for reliable use.
- **Multi-agent coordination:** With specialized agents (POI search, benchmarking, reporting, etc.), we must distinguish between shared memory and agent-private state, and prevent agents from clobbering or overwriting each other’s important memories.

### 5. Cost, performance, UX, and evaluation
- **Latency and cost budgets:** Every memory operation (embed, search, summarize, stuff into context) adds token cost and latency. Cost creep can be controlled if different UX paths are given explicit budgets for how much memory work is allowed.
- **Evaluating memory’s value:** We need metrics to know if memory helps: hit-rate when a prior solution exists, quality lift vs no-memory baselines, reduction in repeated questions, and user-reported personalization.
- **User mental model and control:** Users should have a clear sense of what the system “remembers,” be able to inspect/edit/delete important memories, and understand (at least at a high level) when prior work is being reused.
- **Avoiding creepy or wrong personalization:** Long-term memory that’s slightly wrong or too personal can feel worse than stateless behavior. Sensitive or high-impact memories may need stricter collection and recall rules, or explicit user opt-in.
