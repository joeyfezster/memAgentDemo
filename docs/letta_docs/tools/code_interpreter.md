---
title: Code interpreter | letta-sdk
description: Enable agents to execute code safely with the code execution tool.
---

The `run_code` tool enables Letta agents to execute code in a secure sandboxed environment. Useful for data analysis, calculations, API calls, and programmatic computation.

Note

On [Letta Cloud](/guides/cloud/overview/index.md), this tool works out of the box. For self-hosted deployments, you’ll need to [configure an E2B API key](#self-hosted-setup).

Danger

Each execution runs in a **fresh environment** - variables, files, and state do not persist between runs.

## Quick Start

- [Python](#tab-panel-376)
- [TypeScript](#tab-panel-377)

```
from letta import Letta


client = Letta(token="LETTA_API_KEY")


agent = client.agents.create(
model="openai/gpt-4o",
tools=["run_code"],
memory_blocks=[{
"label": "persona",
"value": "I can run Python code for data analysis and API calls."
}]
)
```

```
import { LettaClient } from "@letta-ai/letta-client";


const client = new LettaClient({ token: "LETTA_API_KEY" });


const agent = await client.agents.create({
  model: "openai/gpt-4o",
  tools: ["run_code"],
  memoryBlocks: [
    {
      label: "persona",
      value: "I can run Python code for data analysis and API calls.",
    },
  ],
});
```

## Tool Parameters

| Parameter  | Type  | Options                           | Description          |
| ---------- | ----- | --------------------------------- | -------------------- |
| `code`     | `str` | Required                          | The code to execute  |
| `language` | `str` | `python`, `js`, `ts`, `r`, `java` | Programming language |

## Return Format

```
{
  "results": ["Last expression value"],
  "logs": {
    "stdout": ["Print statements"],
    "stderr": ["Error output"]
  },
  "error": "Error details if execution failed"
}
```

**Output types:**

- `results[]`: Last expression value (Jupyter-style)
- `logs.stdout`: Print statements and standard output
- `logs.stderr`: Error messages
- `error`: Present if execution failed

## Supported Languages

| Language       | Key Limitations                                           |
| -------------- | --------------------------------------------------------- |
| **Python**     | None - full ecosystem available                           |
| **JavaScript** | No npm packages - built-in Node modules only              |
| **TypeScript** | No npm packages - built-in Node modules only              |
| **R**          | No tidyverse - base R only                                |
| **Java**       | JShell-style execution - no traditional class definitions |

### Python

Full Python ecosystem with common packages pre-installed:

- **Data**: numpy, pandas, scipy, scikit-learn
- **Web**: requests, aiohttp, beautifulsoup4
- **Utilities**: matplotlib, PyYAML, Pillow

Check available packages:

```
import pkg_resources
print([d.project_name for d in pkg_resources.working_set])
```

### JavaScript & TypeScript

No npm packages available - only built-in Node modules.

```
// Works
const fs = require("fs");
const http = require("http");


// Fails
const axios = require("axios");
```

### R

Base R only - no tidyverse packages.

```
# Works
mean(c(1, 2, 3))


# Fails
library(ggplot2)
```

### Java

JShell-style execution - statement-level only.

```
// Works
System.out.println("Hello");
int x = 42;


// Fails
public class Main {
    public static void main(String[] args) { }
}
```

## Network Access

The sandbox has full network access for HTTP requests, API calls, and DNS resolution.

```
import requests


response = requests.get('https://api.github.com/repos/letta-ai/letta')
data = response.json()
print(f"Stars: {data['stargazers_count']}")
```

## No State Persistence

Variables, files, and state do not carry over between executions. Each `run_code` call is completely isolated.

```
# First execution
x = 42


# Second execution (separate run_code call)
print(x)  # Error: NameError: name 'x' is not defined
```

**Implications:**

- Must re-import libraries each time
- Files written to disk are lost
- Cannot build up state across executions

## Self-Hosted Setup

For self-hosted servers, configure an E2B API key. [E2B](https://e2b.dev) provides the sandbox infrastructure.

- [Docker](#tab-panel-378)
- [Docker Compose](#tab-panel-379)
- [Per-Agent](#tab-panel-380)

Terminal window

```
docker run \
  -e E2B_API_KEY="your_e2b_api_key" \
  letta/letta:latest
```

```
services:
  letta:
    environment:
      - E2B_API_KEY=your_e2b_api_key
```

```
agent = client.agents.create(
    tools=["run_code"],
    tool_env_vars={
        "E2B_API_KEY": "your_e2b_api_key"
    }
)
```

## Common Patterns

### Data Analysis

```
agent = client.agents.create(
    model="openai/gpt-4o",
    tools=["run_code"],
    memory_blocks=[{
        "label": "persona",
        "value": "I use Python with pandas and numpy for data analysis."
    }]
)
```

### API Integration

```
agent = client.agents.create(
    model="openai/gpt-4o",
    tools=["run_code", "web_search"],
    memory_blocks=[{
        "label": "persona",
        "value": "I fetch data from APIs using run_code and search docs with web_search."
    }]
)
```

### Statistical Analysis

```
agent = client.agents.create(
    model="openai/gpt-4o",
    tools=["run_code"],
    memory_blocks=[{
        "label": "persona",
        "value": "I perform statistical analysis using scipy and numpy."
    }]
)
```

## When to Use

| Use Case          | Tool            | Why                      |
| ----------------- | --------------- | ------------------------ |
| Data analysis     | `run_code`      | Full Python data stack   |
| Math calculations | `run_code`      | Programmatic computation |
| Live API data     | `run_code`      | Network + processing     |
| Web scraping      | `run_code`      | requests + BeautifulSoup |
| Simple search     | `web_search`    | Purpose-built            |
| Persistent data   | Archival memory | State persistence        |

## Related Documentation

- [Utilities Overview](/guides/agents/prebuilt-tools/index.md)
- [Web Search](/guides/agents/web-search/index.md)
- [Fetch Webpage](/guides/agents/fetch-webpage/index.md)
- [Custom Tools](/guides/agents/custom-tools/index.md)
- [Tool Variables](/guides/agents/tool-variables/index.md)
