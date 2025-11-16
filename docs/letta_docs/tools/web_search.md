---
title: Web search | letta-sdk
description: Enable agents to search the web and retrieve current information with built-in web search tools.
---

The `web_search` and `fetch_webpage` tools enables Letta agents to search the internet for current information, research, and general knowledge using [Exa](https://exa.ai)’s AI-powered search engine.

Note

On [Letta Cloud](/guides/cloud/overview/index.md), these tools work out of the box. For self-hosted deployments, you’ll need to [configure an Exa API key](#self-hosted-setup).

## Web Search

### Adding Web Search to an Agent

- [Python](#tab-panel-427)
- [TypeScript](#tab-panel-428)

```
from letta import Letta


client = Letta(token="LETTA_API_KEY")


agent = client.agents.create(
model="openai/gpt-4o",
embedding="openai/text-embedding-3-small",
tools=["web_search"],
memory_blocks=[
{
"label": "persona",
"value": "I'm a research assistant who uses web search to find current information and cite sources."
}
]
)
```

```
import { LettaClient } from "@letta-ai/letta-client";


const client = new LettaClient({ token: "LETTA_API_KEY" });


const agent = await client.agents.create({
  model: "openai/gpt-4o",
  embedding: "openai/text-embedding-3-small",
  tools: ["web_search"],
  memoryBlocks: [
    {
      label: "persona",
      value:
        "I'm a research assistant who uses web search to find current information and cite sources.",
    },
  ],
});
```

### Usage Example

```
response = client.agents.messages.create(
    agent_id=agent.id,
    messages=[
        {
            "role": "user",
            "content": "What are the latest developments in agent-based AI systems?"
        }
    ]
)
```

Your agent can now choose to use `web_search` when it needs current information.

## Self-Hosted Setup

For self-hosted Letta servers, you’ll need an Exa API key.

### Get an API Key

1. Sign up at [dashboard.exa.ai](https://dashboard.exa.ai/)
2. Copy your API key
3. See [Exa pricing](https://docs.exa.ai) for rate limits and costs

### Configuration Options

- [Docker](#tab-panel-429)
- [Docker Compose](#tab-panel-430)
- [Per-Agent Configuration](#tab-panel-431)

Terminal window

```
docker run \
  -v ~/.letta/.persist/pgdata:/var/lib/postgresql/data \
  -p 8283:8283 \
  -e OPENAI_API_KEY="your_openai_key" \
  -e EXA_API_KEY="your_exa_api_key" \
  letta/letta:latest
```

```
version: "3.8"
services:
  letta:
    image: letta/letta:latest
    ports:
      - "8283:8283"
    environment:
      - OPENAI_API_KEY=your_openai_key
      - EXA_API_KEY=your_exa_api_key
    volumes:
      - ~/.letta/.persist/pgdata:/var/lib/postgresql/data
```

```
agent = client.agents.create(
    model="openai/gpt-4o",
    embedding="openai/text-embedding-3-small",
    tools=["web_search"],
    tool_env_vars={
        "EXA_API_KEY": "your_exa_api_key"
    }
)
```

## Tool Parameters

The `web_search` tool supports advanced filtering and search customization:

| Parameter              | Type        | Default  | Description                                                       |
| ---------------------- | ----------- | -------- | ----------------------------------------------------------------- |
| `query`                | `str`       | Required | The search query to find relevant web content                     |
| `num_results`          | `int`       | 10       | Number of results to return (1-100)                               |
| `category`             | `str`       | None     | Focus search on specific content types (see below)                |
| `include_text`         | `bool`      | False    | Whether to retrieve full page content (usually overflows context) |
| `include_domains`      | `List[str]` | None     | List of domains to include in search results                      |
| `exclude_domains`      | `List[str]` | None     | List of domains to exclude from search results                    |
| `start_published_date` | `str`       | None     | Only return content published after this date (ISO format)        |
| `end_published_date`   | `str`       | None     | Only return content published before this date (ISO format)       |
| `user_location`        | `str`       | None     | Two-letter country code for localized results (e.g., “US”)        |

### Available Categories

Use the `category` parameter to focus your search on specific content types:

| Category           | Best For                                      | Example Query                                |
| ------------------ | --------------------------------------------- | -------------------------------------------- |
| `company`          | Corporate information, company websites       | ”Tesla energy storage solutions”             |
| `research paper`   | Academic papers, arXiv, research publications | ”transformer architecture improvements 2025” |
| `news`             | News articles, current events                 | ”latest AI policy developments”              |
| `pdf`              | PDF documents, reports, whitepapers           | ”climate change impact assessment”           |
| `github`           | GitHub repositories, open source projects     | ”python async web scraping libraries”        |
| `tweet`            | Twitter/X posts, social media discussions     | ”reactions to new GPT release”               |
| `personal site`    | Blogs, personal websites, portfolios          | ”machine learning tutorial blogs”            |
| `linkedin profile` | LinkedIn profiles, professional bios          | ”AI research engineers at Google”            |
| `financial report` | Earnings reports, financial statements        | ”Apple Q4 2024 earnings”                     |

### Return Format

The tool returns a JSON-encoded string containing:

```
{
  "query": "search query",
  "results": [
    {
      "title": "Page title",
      "url": "https://example.com",
      "published_date": "2025-01-15",
      "author": "Author name",
      "highlights": ["Key excerpt 1", "Key excerpt 2"],
      "summary": "AI-generated summary of the content",
      "text": "Full page content (only if include_text=true)"
    }
  ]
}
```

## Best Practices

### 1. Guide When to Search

Provide clear instructions to your agent about when web search is appropriate:

```
memory_blocks=[
    {
        "label": "persona",
        "value": "I'm a helpful assistant. I use web_search for current events, recent news, and topics requiring up-to-date information. I cite my sources."
    }
]
```

### 2. Combine with Archival Memory

Use web search for external/current information, and archival memory for your organization’s internal data:

```
# Create agent with both web_search and archival memory tools
agent = client.agents.create(
    model="openai/gpt-4o",
    embedding="openai/text-embedding-3-small",
    tools=["web_search", "archival_memory_search", "archival_memory_insert"],
    memory_blocks=[
        {
            "label": "persona",
            "value": "I use web_search for current events and external research. I use archival_memory_search for company-specific information and internal documents."
        }
    ]
)
```

See the [Archival Memory documentation](/guides/agents/archival-memory/index.md) for more information.

### 3. Craft Effective Search Queries

Exa uses neural search that understands semantic meaning. Your agent will generally form good queries naturally, but you can improve results by guiding it to:

- **Be descriptive and specific**: “Latest research on RLHF techniques for language models” is better than “RLHF research”
- **Focus on topics, not keywords**: “How companies are deploying AI agents in customer service” works better than “AI agents customer service deployment”
- **Use natural language**: The search engine understands conversational queries like “What are the environmental impacts of Bitcoin mining?”
- **Specify time ranges when relevant**: Guide your agent to use date filters for time-sensitive queries

Example instruction in memory:

```
memory_blocks=[
    {
        "label": "search_strategy",
        "value": "When searching, I craft clear, descriptive queries that focus on topics rather than keywords. I use the category and date filters when appropriate to narrow results."
    }
]
```

### 4. Manage Context Window

By default, `include_text` is `False` to avoid context overflow. The tool returns highlights and AI-generated summaries instead, which are more concise:

```
memory_blocks=[
    {
        "label": "search_guidelines",
        "value": "I avoid setting include_text=true unless specifically needed, as full text usually overflows the context window. Highlights and summaries are usually sufficient."
    }
]
```

## Common Patterns

### Research Assistant

```
agent = client.agents.create(
    model="openai/gpt-4o",
    tools=["web_search"],
    memory_blocks=[
        {
            "label": "persona",
            "value": "I'm a research assistant. I search for relevant information, synthesize findings from multiple sources, and provide citations."
        }
    ]
)
```

### News Monitor

```
agent = client.agents.create(
    model="openai/gpt-4o-mini",
    tools=["web_search"],
    memory_blocks=[
        {
            "label": "persona",
            "value": "I monitor news and provide briefings on AI industry developments."
        },
        {
            "label": "topics",
            "value": "Focus: AI/ML, agent systems, LLM advancements"
        }
    ]
)
```

### Customer Support

```
agent = client.agents.create(
    model="openai/gpt-4o",
    tools=["web_search"],
    memory_blocks=[
        {
            "label": "persona",
            "value": "I help customers by checking documentation, service status pages, and community discussions for solutions."
        }
    ]
)
```

## Troubleshooting

### Agent Not Using Web Search

Check:

1. Tool is attached: `"web_search"` in agent’s tools list
2. Instructions are clear about when to search
3. Model has good tool-calling capabilities (GPT-4, Claude 3+)

```
# Verify tools
agent = client.agents.retrieve(agent_id=agent.id)
print([tool.name for tool in agent.tools])
```

### Missing EXA_API_KEY

If you see errors about missing API keys on self-hosted deployments:

Terminal window

```
# Check if set
echo $EXA_API_KEY


# Set for session
export EXA_API_KEY="your_exa_api_key"


# Docker example
docker run -e EXA_API_KEY="your_exa_api_key" letta/letta:latest
```

## When to Use Web Search

| Use Case             | Tool              | Why                   |
| -------------------- | ----------------- | --------------------- |
| Current events, news | `web_search`      | Real-time information |
| External research    | `web_search`      | Broad internet access |
| Internal documents   | Archival memory   | Fast, static data     |
| User preferences     | Memory blocks     | In-context, instant   |
| General knowledge    | Pre-trained model | No search needed      |

## Fetch Webpage

- [Python](#tab-panel-432)
- [TypeScript](#tab-panel-433)

```
from letta import Letta


client = Letta(token="LETTA_API_KEY")


agent = client.agents.create(
model="openai/gpt-4o",
tools=["fetch_webpage"],
memory_blocks=[{
"label": "persona",
"value": "I can fetch and read webpages to answer questions about online content."
}]
)
```

```
import { LettaClient } from "@letta-ai/letta-client";


const client = new LettaClient({ token: "LETTA_API_KEY" });


const agent = await client.agents.create({
  model: "openai/gpt-4o",
  tools: ["fetch_webpage"],
  memoryBlocks: [
    {
      label: "persona",
      value:
        "I can fetch and read webpages to answer questions about online content.",
    },
  ],
});
```

## Tool Parameters

| Parameter | Type  | Description                     |
| --------- | ----- | ------------------------------- |
| `url`     | `str` | The URL of the webpage to fetch |

## Return Format

The tool returns webpage content as text/markdown.

**With Exa API (if configured):**

```
{
  "title": "Page title",
  "published_date": "2025-01-15",
  "author": "Author name",
  "text": "Full page content in markdown"
}
```

**Fallback (without Exa):** Returns markdown-formatted text extracted from the HTML.

## How It Works

The tool uses a multi-tier approach:

1. **Exa API** (if `EXA_API_KEY` is configured): Uses Exa’s content extraction
2. **Trafilatura** (fallback): Open-source text extraction to markdown
3. **Readability + html2text** (final fallback): HTML cleaning and conversion

## Self-Hosted Setup

For enhanced fetching on self-hosted servers, optionally configure an Exa API key. Without it, the tool still works using open-source extraction.

### Optional: Configure Exa

- [Docker](#tab-panel-434)
- [Docker Compose](#tab-panel-435)
- [Per-Agent](#tab-panel-436)

Terminal window

```
docker run \
  -e EXA_API_KEY="your_exa_api_key" \
  letta/letta:latest
```

```
services:
  letta:
    environment:
      - EXA_API_KEY=your_exa_api_key
```

```
agent = client.agents.create(
    tools=["fetch_webpage"],
    tool_env_vars={
        "EXA_API_KEY": "your_exa_api_key"
    }
)
```

## Common Patterns

### Documentation Reader

```
agent = client.agents.create(
    model="openai/gpt-4o",
    tools=["fetch_webpage", "web_search"],
    memory_blocks=[{
        "label": "persona",
        "value": "I search for documentation with web_search and read it with fetch_webpage."
    }]
)
```

### Research Assistant

```
agent = client.agents.create(
    model="openai/gpt-4o",
    tools=["fetch_webpage", "archival_memory_insert"],
    memory_blocks=[{
        "label": "persona",
        "value": "I fetch articles and store key insights in archival memory for later reference."
    }]
)
```

### Content Summarizer

```
agent = client.agents.create(
    model="openai/gpt-4o",
    tools=["fetch_webpage"],
    memory_blocks=[{
        "label": "persona",
        "value": "I fetch webpages and provide summaries of their content."
    }]
)
```

## When to Use

| Use Case              | Tool                                  | Why                |
| --------------------- | ------------------------------------- | ------------------ |
| Read specific webpage | `fetch_webpage`                       | Direct URL access  |
| Find webpages to read | `web_search`                          | Discovery first    |
| Read + search in one  | `web_search` with `include_text=true` | Combined operation |
| Multiple pages        | `fetch_webpage`                       | Iterate over URLs  |

## Related Documentation

- [Utilities Overview](/guides/agents/prebuilt-tools/index.md)
- [Web Search](/guides/agents/web-search/index.md)
- [Run Code](/guides/agents/run-code/index.md)
- [Custom Tools](/guides/agents/custom-tools/index.md)
- [Tool Variables](/guides/agents/tool-variables/index.md)
