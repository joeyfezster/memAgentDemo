---
title: Parallel tool calling | letta-sdk
description: Enable agents to call multiple tools simultaneously for efficient parallel execution.
---

When an agent calls multiple tools, Letta can execute them concurrently instead of sequentially.

Parallel tool calling has two configuration levels:

- **Agent LLM config**: Controls whether the LLM can request multiple tool calls at once
- **Individual tool settings**: Controls whether requested tools actually execute in parallel or sequentially

## Model Support

Parallel tool calling is supported for OpenAI and Anthropic models.

## Enabling Parallel Tool Calling

### Agent Configuration

Set `parallel_tool_calls: true` in the agent’s LLM config:

- [TypeScript](#tab-panel-374)
- [Python](#tab-panel-375)

```
const agent = await client.agents.create({
  llm_config: {
    model: "anthropic/claude-sonnet-4-20250514",
    parallel_tool_calls: true,
  },
});
```

```
agent = client.agents.create(
    llm_config={
        "model": "anthropic/claude-sonnet-4-20250514",
        "parallel_tool_calls": True
    }
)
```

### Tool Configuration

Individual tools must opt-in to parallel execution:

- [TypeScript](#tab-panel-372)
- [Python](#tab-panel-373)

```
await client.tools.update(toolId, {
  enable_parallel_execution: true,
});
```

```
client.tools.update(
    tool_id=tool_id,
    enable_parallel_execution=True
)
```

By default, tools execute sequentially (`enable_parallel_execution=False`).

Danger

Only enable parallel execution for tools safe to run concurrently. Tools that modify shared state or have ordering dependencies should remain sequential.

## ADE Configuration

### Agent Toggle

1. Open **Settings** → **LLM Config**
2. Enable **“Parallel tool calls”**

### Tool Toggle

1. Open the **Tools** panel
2. Click a tool to open it
3. Go to the **Settings** tab
4. Enable **“Enable parallel execution”**

## Execution Behavior

When the agent calls multiple tools:

- Sequential tools execute one-by-one
- Parallel-enabled tools execute concurrently
- Mixed: sequential tools complete first, then parallel tools execute together

Example:

```
Agent calls:
  - search_web (parallel: true)
  - search_database (parallel: true)
  - send_message (parallel: false)


Execution:
  1. send_message executes
  2. search_web AND search_database execute concurrently
```

## Limitations

- Parallel execution is automatically disabled when [tool rules](/guides/agents/tool-rules/index.md) are configured
- Only enable for tools safe to run concurrently (e.g., read-only operations)
- Tools that modify shared state should remain sequential
