---
title: Memory blocks | letta-sdk
description: Create and manage structured memory blocks that persist in agent context windows.
---

Note

Interested in learning more about the origin of memory blocks? Read our [blog post](https://www.letta.com/blog/memory-blocks).

## What are memory blocks?

Memory blocks are structured sections of the agent’s context window that persist across all interactions. They are always visible - no retrieval needed.

**Memory blocks are Letta’s core abstraction.** Create a block with a descriptive label and the agent learns how to use it. This simple mechanism enables capabilities impossible with traditional context management.

**Key properties:**

- **Agent-managed** - Agents autonomously organize information based on block labels
- **Flexible** - Use for any purpose: knowledge, guidelines, state tracking, scratchpad space
- **Shareable** - Multiple agents can access the same block; update once, visible everywhere
- **Always visible** - Blocks stay in context, never need retrieval

**Examples:**

- Store tool usage guidelines so agents avoid past mistakes
- Maintain working memory in a scratchpad block
- Mirror external state (user’s current document) for real-time awareness
- Share read-only policies across all agents from a central source
- Coordinate multi-agent systems: parent agents watch subagent result blocks update in real-time
- Enable emergent behavior: add `performance_tracking` or `emotional_state` and watch agents start using them

Memory blocks aren’t just storage - they’re a coordination primitive that enables sophisticated agent behavior.

## Memory block structure

Memory blocks represent a section of an agent’s context window. An agent may have multiple memory blocks, or none at all. A memory block consists of:

- A `label`, which is a unique identifier for the block
- A `description`, which describes the purpose of the block
- A `value`, which is the contents/data of the block
- A `limit`, which is the size limit (in characters) of the block

## The importance of the `description` field

When making memory blocks, it’s crucial to provide a good `description` field that accurately describes what the block should be used for. The `description` is the main information used by the agent to determine how to read and write to that block. Without a good description, the agent may not understand how to use the block.

Because `persona` and `human` are two popular block labels, Letta autogenerates default descriptions for these blocks if you don’t provide them. If you provide a description for a memory block labelled `persona` or `human`, the default description will be overridden.

For `persona`, a good default is:

> The persona block: Stores details about your current persona, guiding how you behave and respond. This helps you to maintain consistency and personality in your interactions.

For `human`, a good default is:

> The human block: Stores key details about the person you are conversing with, allowing for more personalized and friend-like conversation.

## Read-only blocks

Memory blocks are read-write by default (so the agent can update the block using memory tools), but can be set to read-only by setting the `read_only` field to `true`. When a block is read-only, the agent cannot update the block.

Read-only blocks are useful when you want to give an agent access to information (for example, a shared memory block about an organization), but you don’t want the agent to be able to make potentially destructive changes to the block.

## Creating an agent with memory blocks

When you create an agent, you can specify memory blocks to also be created with the agent. For most chat applications, we recommend create a `human` block (to represent memories about the user) and a `persona` block (to represent the agent’s persona).

- [TypeScript](#tab-panel-329)
- [Python](#tab-panel-330)

```
// install letta-client with `npm install @letta-ai/letta-client`
import { LettaClient } from "@letta-ai/letta-client";


// create a client connected to Letta Cloud
const client = new LettaClient({
  token: process.env.LETTA_API_KEY,
});


// create an agent with two basic self-editing memory blocks
const agentState = await client.agents.create({
  memoryBlocks: [
    {
      label: "human",
      value: "The human's name is Bob the Builder.",
      limit: 5000,
    },
    {
      label: "persona",
      value: "My name is Sam, the all-knowing sentient AI.",
      limit: 5000,
    },
  ],
  model: "openai/gpt-4o-mini",
});
```

python

```
# install letta_client with `pip install letta-client`
from letta_client import Letta
import os


# create a client connected to Letta Cloud
client = Letta(token=os.getenv("LETTA_API_KEY"))


# create an agent with two basic self-editing memory blocks
agent_state = client.agents.create(
    memory_blocks=[
        {
          "label": "human",
          "value": "The human's name is Bob the Builder.",
          "limit": 5000
        },
        {
          "label": "persona",
          "value": "My name is Sam, the all-knowing sentient AI.",
          "limit": 5000
        }
    ],
    model="openai/gpt-4o-mini"
)
```

When the agent is created, the corresponding blocks are also created and attached to the agent, so that the block value will be in the context window.

## Creating and attaching memory blocks

You can also directly create blocks and attach them to an agent. This can be useful if you want to create blocks that are shared between multiple agents. If multiple agents are attached to a block, they will all have the block data in their context windows (essentially providing shared memory).

Below is an example of creating a block directory, and attaching the block to two agents by specifying the `block_ids` field.

- [TypeScript](#tab-panel-321)
- [Python](#tab-panel-322)

```
// create a persisted block, which can be attached to agents
const block = await client.blocks.create({
  label: "organization",
  description: "A block to store information about the organization",
  value: "Organization: Letta",
  limit: 4000,
});


// create an agent with both a shared block and its own blocks
const sharedBlockAgent1 = await client.agents.create({
  name: "shared_block_agent1",
  memoryBlocks: [
    {
      label: "persona",
      value: "I am agent 1",
    },
  ],
  blockIds: [block.id],
  model: "openai/gpt-4o-mini",
});


// create another agent with the same shared block
const sharedBlockAgent2 = await client.agents.create({
  name: "shared_block_agent2",
  memoryBlocks: [
    {
      label: "persona",
      value: "I am agent 2",
    },
  ],
  blockIds: [block.id],
  model: "openai/gpt-4o-mini",
});
```

python

```
# create a persisted block, which can be attached to agents
block = client.blocks.create(
    label="organization",
    description="A block to store information about the organization",
    value="Organization: Letta",
    limit=4000,
)


# create an agent with both a shared block and its own blocks
shared_block_agent1 = client.agents.create(
    name="shared_block_agent1",
    memory_blocks=[
        {
            "label": "persona",
            "value": "I am agent 1"
        },
    ],
    block_ids=[block.id],
    model="openai/gpt-4o-mini"
)


# create another agent sharing the block
shared_block_agent2 = client.agents.create(
    name="shared_block_agent2",
    memory_blocks=[
        {
            "label": "persona",
            "value": "I am agent 2"
        },
    ],
    block_ids=[block.id],
    model="openai/gpt-4o-mini"
)
```

You can also attach blocks to existing agents:

- [TypeScript](#tab-panel-315)
- [Python](#tab-panel-316)

```
await client.agents.blocks.attach(agent.id, block.id);
```

```
client.agents.blocks.attach(agent_id=agent.id, block_id=block.id)
```

You can see all agents attached to a block by using the `block_id` field in the [blocks retrieve](/api-reference/blocks/retrieve/index.md) endpoint.

## Managing blocks

### Retrieving a block

You can retrieve the contents of a block by ID. This is useful when blocks store finalized reports, code outputs, or other data you want to extract for use outside the agent.

- [TypeScript](#tab-panel-319)
- [Python](#tab-panel-320)

````
console.log(block.value); // access the block's content ``` ```python Python
block = client.blocks.retrieve(block.id) print(block.value) # access the
block's content ```






</TabItem>
</Tabs>


### Listing blocks


You can list all blocks, optionally filtering by label or searching by label text. This is useful for finding blocks across your project.


<Tabs>
<TabItem label="TypeScript">


```typescript TypeScript
// list all blocks
const blocks = await client.blocks.list();


// filter by label
const humanBlocks = await client.blocks.list({
label: "human"
});


// search by label text
const searchResults = await client.blocks.list({
labelSearch: "organization"
});
````

```
# list all blocks
blocks = client.blocks.list()


# filter by label
human_blocks = client.blocks.list(label="human")


# search by label text
search_results = client.blocks.list(label_search="organization")
```

### Modifying a block

You can directly modify a block’s content, limit, description, or other properties. This is particularly useful for:

- External scripts that provide up-to-date information to agents (e.g., syncing a text file to a block)
- Updating shared blocks that multiple agents reference
- Programmatically managing block content outside of agent interactions

* [TypeScript](#tab-panel-323)
* [Python](#tab-panel-324)

```
// update the block's value - completely replaces the content
await client.blocks.modify(block.id, {
  value: "Updated organization information: Letta - Building agentic AI",
});


// update multiple properties
await client.blocks.modify(block.id, {
  value: "New content",
  limit: 6000,
  description: "Updated description",
});
```

```
# update the block's value - completely replaces the content
client.blocks.modify(
    block.id,
    value="Updated organization information: Letta - Building agentic AI"
)


# update multiple properties
client.blocks.modify(
    block.id,
    value="New content",
    limit=6000,
    description="Updated description"
)
```

Danger

**Setting `value` completely replaces the entire block content** - it is not an append operation. If multiple processes (agents or external scripts) modify the same block concurrently, the last write wins and overwrites all earlier changes. To avoid data loss: - Set blocks to **read-only** if you don’t want agents to modify them - Only modify blocks directly in controlled scenarios where overwriting is acceptable - Ensure your application logic accounts for full replacements, not merges

### Deleting a block

You can delete a block when it’s no longer needed. Note that deleting a block will remove it from all agents that have it attached.

- [TypeScript](#tab-panel-314)

`typescript TypeScript await client.blocks.delete(block.id); ``python Python client.blocks.delete(block_id=block.id)`

### Inspecting block usage

See which agents have a block attached:

- [TypeScript](#tab-panel-325)
- [Python](#tab-panel-326)

```
// list all agents that use this block
const agentsWithBlock = await client.blocks.agents.list(block.id);
console.log(`Used by ${agentsWithBlock.length} agents:`);
for (const agent of agentsWithBlock) {
  console.log(`  - ${agent.name}`);
}


// with pagination
const agentsPage = await client.blocks.agents.list(block.id, {
  limit: 10,
  order: "asc",
});
```

```
# list all agents that use this block
agents_with_block = client.blocks.agents.list(block_id=block.id)
print(f"Used by {len(agents_with_block)} agents:")
for agent in agents_with_block:
    print(f"  - {agent.name}")


# with pagination
agents_page = client.blocks.agents.list(
    block_id=block.id,
    limit=10,
    order="asc"
)
```

## Agent-scoped block operations

### Listing an agent’s blocks

You can retrieve all blocks attached to a specific agent. This shows you the complete memory configuration for that agent.

- [TypeScript](#tab-panel-327)
- [Python](#tab-panel-328)

````
client.agents.blocks.list(agent.id); ``` ```python Python agent_blocks =
client.agents.blocks.list(agent_id=agent.id) ```






</TabItem>
</Tabs>


### Retrieving an agent's block by label


Instead of using a block ID, you can retrieve a block from a specific agent using its label. This is useful when you want to inspect what the agent currently knows about a specific topic.


<Tabs>
<TabItem label="TypeScript">


```typescript TypeScript // get the agent's current knowledge about the human
const humanBlock = await client.agents.blocks.retrieve( agent.id, "human" );
console.log(humanBlock.value); ``` ```python Python # get the agent's current
knowledge about the human human_block = client.agents.blocks.retrieve(
agent_id=agent.id, block_label="human" ) print(human_block.value) ```




</TabItem>
</Tabs>


### Modifying an agent's block


You can modify a block through the agent-scoped endpoint using the block's label. This is useful for updating agent-specific memory without needing to know the block ID.


<Tabs>
<TabItem label="TypeScript">


```typescript TypeScript
// update the agent's human block
await client.agents.blocks.modify(agent.id, "human", {
  value: "The human's name is Alice. She prefers Python over TypeScript."
});
````

```
# update the agent's human block
client.agents.blocks.modify(
    agent_id=agent.id,
    block_label="human",
    value="The human's name is Alice. She prefers Python over TypeScript."
)
```

### Detaching blocks from agents

You can detach a block from an agent’s context window. This removes the block from the agent’s memory without deleting the block itself.

- [TypeScript](#tab-panel-317)
- [Python](#tab-panel-318)

```
await client.agents.blocks.detach(agent.id, block.id);
```

```
client.agents.blocks.detach(agent_id=agent.id, block_id=block.id)
```
