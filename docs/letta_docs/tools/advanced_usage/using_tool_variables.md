---
title: Using tool variables | letta-sdk
description: Pass dynamic variables to tools for context-aware function execution.
---

You can use **tool variables** to specify environment variables available to your custom tools. For example, if you set a tool variable `PASSWORD` to `banana`, then write a custom function that prints `os.getenv('PASSWORD')` in the tool, the function will print `banana`.

## Assigning tool variables in the ADE

To assign tool variables in the Agent Development Environment (ADE), click on **Env Vars** to open the **Environment Variables** viewer:

![](/images/env_vars_button.png)

Once in the **Environment Variables** viewer, click **+** to add a new tool variable if one does not exist.

![](/images/tool_variables.png)

## Assigning tool variables in the API / SDK

You can also assign tool variables on agent creation in the API with the `tool_exec_environment_variables` parameter:

- [{7-9}](#tab-panel-420)
- [{5-7}](#tab-panel-421)
- [TypeScript {5-7}](#tab-panel-422)

curl

```
curl -X POST https://api.letta.com/v1/agents \
     -H "Authorization: Bearer $LETTA_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
  "memory_blocks": [],
  "llm":"openai/gpt-4o-mini",
  "tool_exec_environment_variables": {
      "API_KEY": "your-api-key-here"
  }
}'
```

python

```
agent_state = client.agents.create(
    memory_blocks=[],
    model="openai/gpt-4o-mini",
    tool_exec_environment_variables={
        "API_KEY": "your-api-key-here"
    }
)
```

```
const agentState = await client.agents.create({
  memoryBlocks: [],
  model: "openai/gpt-4o-mini",
  toolExecEnvironmentVariables: {
    API_KEY: "your-api-key-here",
  },
});
```
