---
title: JSON mode & structured output | letta-sdk
description: Use JSON mode to structure agent outputs in valid JSON format for downstream processing.
---

Letta provides two ways to get structured JSON output from agents: **Structured Generation through Tools** (recommended) and the `response_format` parameter.

## Quick Comparison

Note

**Recommended**: Use **Structured Generation through Tools** - works with all providers (Anthropic, OpenAI, Google, etc.) and integrates naturally with Letta’s tool-calling architecture.

Note

**Structured Generation through Tools**:

- ✅ Universal provider compatibility
- ✅ Both reasoning AND structured output
- ✅ Per-message control
- ✅ Works even as “dummy tool” for pure formatting

Danger

**`response_format` parameter**:

- ⚠️ OpenAI-compatible providers only (NOT Anthropic)
- ⚠️ Persistent agent state (affects all future responses)
- ✅ Built-in provider schema enforcement

## Structured Generation through Tools (Recommended)

Create a tool that defines your desired response format. The tool arguments become your structured data, and you can extract them from the tool call.

### Creating a Structured Generation Tool

- [TypeScript](#tab-panel-307)
- [Python](#tab-panel-308)

```
import { LettaClient } from "@letta-ai/letta-client";


// Create client connected to Letta Cloud
const client = new LettaClient({ token: process.env.LETTA_API_KEY });


// First create the tool
const toolCode = `def generate_rank(rank: int, reason: str):
"""Generate a ranking with explanation.


    Args:
        rank (int): The numerical rank from 1-10.
        reason (str): The reasoning behind the rank.
    """
    print("Rank generated")
    return`;


const tool = await client.tools.create({
  sourceCode: toolCode,
  sourceType: "python",
});


// Create agent with the structured generation tool
const agentState = await client.agents.create({
  model: "openai/gpt-4o-mini",
  memoryBlocks: [
    {
      label: "human",
      value:
        "The human's name is Chad. They are a food enthusiast who enjoys trying different cuisines.",
    },
    {
      label: "persona",
      value:
        "I am a helpful food critic assistant. I provide detailed rankings and reviews of different foods and restaurants.",
    },
  ],
  toolIds: [tool.id],
});
```

python

```
from letta_client import Letta


# Create client connected to Letta Cloud
import os
client = Letta(token=os.getenv("LETTA_API_KEY"))


def generate_rank(rank: int, reason: str):
    """Generate a ranking with explanation.


    Args:
        rank (int): The numerical rank from 1-10.
        reason (str): The reasoning behind the rank.
    """
    print("Rank generated")
    return


# Create the tool
tool = client.tools.create(func=generate_rank)


# Create agent with the structured generation tool
agent_state = client.agents.create(
    model="openai/gpt-4o-mini",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "human",
            "value": "The human's name is Chad. They are a food enthusiast who enjoys trying different cuisines."
        },
        {
            "label": "persona",
            "value": "I am a helpful food critic assistant. I provide detailed rankings and reviews of different foods and restaurants."
        }
    ],
    tool_ids=[tool.id]
)
```

### Using the Structured Generation Tool

- [TypeScript](#tab-panel-299)
- [Python](#tab-panel-300)

```
// Send message and instruct agent to use the tool
const response = await client.agents.messages.create(agentState.id, {
  messages: [
    {
      role: "user",
      content:
        "How do you rank sushi as a food? Please use the generate_rank tool to provide your response.",
    },
  ],
});


// Extract structured data from tool call
for (const message of response.messages) {
  if (message.messageType === "tool_call_message") {
    const args = JSON.parse(message.toolCall.arguments);
    console.log(`Rank: ${args.rank}`);
    console.log(`Reason: ${args.reason}`);
  }
}


// Example output:
// Rank: 8
// Reason: Sushi is a highly regarded cuisine known for its fresh ingredients...
```

python

```
# Send message and instruct agent to use the tool
response = client.agents.messages.create(
    agent_id=agent_state.id,
    messages=[
        {
            "role": "user",
            "content": "How do you rank sushi as a food? Please use the generate_rank tool to provide your response."
        }
    ]
)


# Extract structured data from tool call
for message in response.messages:
    if message.message_type == "tool_call_message":
        import json
        args = json.loads(message.tool_call.arguments)
        rank = args["rank"]
        reason = args["reason"]
        print(f"Rank: {rank}")
        print(f"Reason: {reason}")


# Example output:
# Rank: 8
# Reason: Sushi is a highly regarded cuisine known for its fresh ingredients...
```

The agent will call the tool, and you can extract the structured arguments:

```
{
  "rank": 8,
  "reason": "Sushi is a highly regarded cuisine known for its fresh ingredients, artistic presentation, and cultural significance."
}
```

## Using `response_format` for Provider-Native JSON Mode

The `response_format` parameter enables structured output/JSON mode from LLM providers that support it. This approach is fundamentally different from tools because **`response_format` becomes a persistent part of the agent’s state** - once set, all future responses from that agent will follow the format until explicitly changed.

Under the hood, `response_format` constrains the agent’s assistant messages to follow the specified schema, but it doesn’t affect tools - those continue to work normally with their original schemas.

Danger

**Requirements for `response_format`:**

- Only works with providers that support structured outputs (like OpenAI) - NOT Anthropic or other providers

### Basic JSON Mode

- [TypeScript](#tab-panel-301)
- [Python](#tab-panel-302)

```
import { LettaClient } from "@letta-ai/letta-client";


// Create client (Letta Cloud)
const client = new LettaClient({ token: "LETTA_API_KEY" });


// Create agent with basic JSON mode (OpenAI/compatible providers only)
const agentState = await client.agents.create({
  model: "openai/gpt-4o-mini",
  memoryBlocks: [
    {
      label: "human",
      value:
        "The human's name is Chad. They work as a data analyst and prefer clear, organized information.",
    },
    {
      label: "persona",
      value:
        "I am a helpful assistant who provides clear and well-organized responses.",
    },
  ],
  responseFormat: { type: "json_object" },
});


// Send message expecting JSON response
const response = await client.agents.messages.create(agentState.id, {
  messages: [
    {
      role: "user",
      content:
        "How do you rank sushi as a food? Please respond in JSON format with rank and reason fields.",
    },
  ],
});


for (const message of response.messages) {
  console.log(message);
}
```

python

```
from letta_client import Letta


# Create client (Letta Cloud)
client = Letta(token="LETTA_API_KEY")


# Create agent with basic JSON mode (OpenAI/compatible providers only)
agent_state = client.agents.create(
    model="openai/gpt-4o-mini",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "human",
            "value": "The human's name is Chad. They work as a data analyst and prefer clear, organized information."
        },
        {
            "label": "persona",
            "value": "I am a helpful assistant who provides clear and well-organized responses."
        }
    ],
    response_format={"type": "json_object"}
)


# Send message expecting JSON response
response = client.agents.messages.create(
    agent_id=agent_state.id,
    messages=[
        {
            "role": "user",
            "content": "How do you rank sushi as a food? Please respond in JSON format with rank and reason fields."
        }
    ]
)


for message in response.messages:
    print(message)
```

### Advanced JSON Schema Mode

For more precise control, you can use OpenAI’s `json_schema` mode with strict validation:

- [TypeScript](#tab-panel-303)
- [Python](#tab-panel-304)

```
import { LettaClient } from "@letta-ai/letta-client";


const client = new LettaClient({ token: "LETTA_API_KEY" });


// Define structured schema (from OpenAI structured outputs guide)
const responseFormat = {
  type: "json_schema",
  jsonSchema: {
    name: "food_ranking",
    schema: {
      type: "object",
      properties: {
        rank: {
          type: "integer",
          minimum: 1,
          maximum: 10,
        },
        reason: {
          type: "string",
        },
        categories: {
          type: "array",
          items: {
            type: "object",
            properties: {
              name: { type: "string" },
              score: { type: "integer" },
            },
            required: ["name", "score"],
            additionalProperties: false,
          },
        },
      },
      required: ["rank", "reason", "categories"],
      additionalProperties: false,
    },
    strict: true,
  },
};


// Create agent
const agentState = await client.agents.create({
  model: "openai/gpt-4o-mini",
  memoryBlocks: [],
});


// Update agent with response format
const updatedAgent = await client.agents.update(agentState.id, {
  responseFormat,
});


// Send message
const response = await client.agents.messages.create(agentState.id, {
  messages: [
    {
      role: "user",
      content:
        "How do you rank sushi? Include categories for taste, presentation, and value.",
    },
  ],
});


for (const message of response.messages) {
  console.log(message);
}
```

python

```
from letta_client import Letta


client = Letta(token="LETTA_API_KEY")


# Define structured schema (from OpenAI structured outputs guide)
response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "food_ranking",
        "schema": {
            "type": "object",
            "properties": {
                "rank": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10
                },
                "reason": {
                    "type": "string"
                },
                "categories": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": { "type": "string" },
                            "score": { "type": "integer" }
                        },
                        "required": ["name", "score"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["rank", "reason", "categories"],
            "additionalProperties": False
        },
        "strict": True
    }
}


# Create agent
agent_state = client.agents.create(
    model="openai/gpt-4o-mini",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[]
)


# Update agent with response format
agent_state = client.agents.update(
    agent_id=agent_state.id,
    response_format=response_format
)


# Send message
response = client.agents.messages.create(
    agent_id=agent_state.id,
    messages=[
        {"role": "user", "content": "How do you rank sushi? Include categories for taste, presentation, and value."}
    ]
)


for message in response.messages:
    print(message)
```

With structured JSON schema, the agent’s response will be strictly validated:

```
{
  "rank": 8,
  "reason": "Sushi is highly regarded for its fresh ingredients and artful presentation",
  "categories": [
    { "name": "taste", "score": 9 },
    { "name": "presentation", "score": 10 },
    { "name": "value", "score": 6 }
  ]
}
```

## Updating Agent Response Format

You can update an existing agent’s response format:

- [TypeScript](#tab-panel-305)
- [Python](#tab-panel-306)

```
// Update agent to use JSON mode (OpenAI/compatible only)
await client.agents.update(agentState.id, {
  responseFormat: { type: "json_object" },
});


// Or remove JSON mode
await client.agents.update(agentState.id, {
  responseFormat: null,
});
```

python

```
# Update agent to use JSON mode (OpenAI/compatible only)
client.agents.update(
    agent_id=agent_state.id,
    response_format={"type": "json_object"}
)


# Or remove JSON mode
client.agents.update(
    agent_id=agent_state.id,
    response_format=None
)
```
