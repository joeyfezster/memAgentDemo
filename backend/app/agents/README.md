# Agent System Documentation

This directory contains a memory-enabled multi-agent system built with the Letta framework.

## Overview

The agent system implements a three-agent architecture for handling analytical requests:

1. **Routing Agent**: Entry point that analyzes requests and routes to appropriate analyst
2. **Specialized Analyst** (Financial): Handles financial/quantitative analysis
3. **Generalist Analyst**: Handles general analytical tasks and fallback requests

## Architecture

### Why Letta?

[Letta](https://www.letta.com/) is a platform for building stateful AI agents with advanced memory capabilities. Key benefits:

- **Persistent Memory**: Agents maintain memory across sessions via memory blocks
- **Archival Storage**: Long-term storage and retrieval of past analyses
- **Self-Learning**: Agents update their own knowledge based on interactions
- **Agent Communication**: Built-in tools for agent-to-agent messaging

### Memory System

Each agent uses two types of memory:

**Memory Blocks (In-Context)**
- Always visible to the agent
- Self-editable via `memory_insert` and `memory_replace` tools
- Define agent persona, strategies, and knowledge
- Persist across sessions

**Archival Memory (External Storage)**
- Searchable database for facts and past analyses
- Accessed via `archival_memory_insert` and `archival_memory_search` tools
- Enables agents to reference past work
- Grows over time as agents store findings

### Agent Details

#### Routing Agent
- **Purpose**: Intelligent request dispatcher
- **Memory Blocks**:
  - `persona`: Role and responsibilities
  - `routing_strategy`: Current routing rules (self-updating)
  - `available_agents`: Knowledge of analyst capabilities
- **Tools**: `send_message` (for routing to analysts)
- **Learning**: Updates routing strategy based on successful patterns

#### Specialized Analyst (Financial)
- **Purpose**: Financial and quantitative analysis
- **Specializations**: Financial statements, ROI, revenue modeling, market analysis
- **Memory Blocks**:
  - `persona`: Identity as financial analyst
  - `methodologies`: Analytical methods used
  - `domain_knowledge`: Financial domain expertise
- **Tools**: `archival_memory_insert`, `archival_memory_search`
- **Learning**: Refines methodologies and grows domain knowledge

#### Generalist Analyst
- **Purpose**: General analytical tasks and fallback
- **Capabilities**: Research, synthesis, comparative analysis, strategic thinking
- **Memory Blocks**:
  - `persona`: Identity as generalist analyst
  - `analytical_approaches`: Methods for different request types
  - `learning_history`: Patterns learned from diverse requests
- **Tools**: `archival_memory_insert`, `archival_memory_search`
- **Learning**: Discovers which approaches work for different request types

## Usage

### Basic Setup

```python
from app.agents import get_agent_service, AnalysisRequest

# Get the global service instance
service = get_agent_service()

# Initialize agents (first time only, or after restart)
await service.initialize()
```

### Processing Analysis Requests

```python
# Create an analysis request
request = AnalysisRequest(
    user_id="user_123",
    query="Analyze the financial performance of Company X in Q4 2024",
    context={"company": "Company X", "period": "Q4 2024"}  # Optional
)

# Process the request (automatic routing)
response = await service.process_analysis_request(request)

# Access the results
print(f"Result: {response.result}")
print(f"Routed to: {response.routed_to}")
print(f"Reasoning: {response.routing_reasoning}")
print(f"Processing time: {response.processing_time_ms}ms")
```

### Monitoring Agent State

```python
from app.agents import AgentType

# Get detailed info about an agent
agent_info = await service.get_agent_info(AgentType.SPECIALIZED_ANALYST)

# Inspect memory blocks
for block in agent_info.memory_blocks:
    print(f"{block.label}: {block.value}")

# Check system status
status = await service.get_system_status()
print(f"Status: {status.status}")
print(f"Active agents: {len(status.agents)}")
```

### Direct Agent Access (Advanced)

```python
# Access specific analyst directly (bypassing routing)
result = service._specialized_analyst.analyze(
    query="Calculate NPV for this project",
    user_id="user_123",
    context={"discount_rate": 0.08}
)

# Check agent memory state
memory = service._specialized_analyst.get_memory_state()
print(f"Methodologies: {memory['methodologies']}")
```

## Configuration

### Environment Variables

Required environment variable in `.env`:

```bash
# Letta API Key (REQUIRED)
# Get your key from https://app.letta.com/settings
LETTA_API_KEY=your_api_key_here

# Optional: Custom Letta server URL
# Only needed if using self-hosted Letta
LETTA_BASE_URL=https://your-letta-instance.com
```

### Agent Configuration

Agent configurations are defined in `config.py`:

- **Memory block templates**: Define initial agent knowledge
- **Agent types**: Enum of available agent types
- **Tool configurations**: Specify which Letta tools each agent uses
- **Model selection**: Choose LLM model (default: GPT-4)

To modify agent behavior:
1. Edit memory block templates in `config.py`
2. Restart the service to create new agents with updated config
3. Agents will further evolve their memory based on interactions

## File Structure

```
agents/
├── __init__.py              # Module exports
├── README.md                # This file
├── config.py                # Agent configurations and memory templates
├── schemas.py               # Pydantic models for API
├── service.py               # Main orchestration service
├── routing_agent.py         # Routing agent implementation
├── specialized_analyst.py   # Financial analyst implementation
└── generalist_analyst.py    # Generalist analyst implementation
```

## Testing

Comprehensive functional tests are in `tests/test_agents.py`.

Run tests:
```bash
# All agent tests
pytest tests/test_agents.py -v

# Specific test class
pytest tests/test_agents.py::TestRoutingLogic -v

# Specific test
pytest tests/test_agents.py::TestRoutingLogic::test_route_financial_query_to_specialist -v
```

**Note**: Tests require `LETTA_API_KEY` to be set and will create/delete real Letta agents.

## Integration Points

### Future API Integration

The agent system is designed to be integrated with FastAPI routes (not included yet):

```python
# Future: app/api/agents.py
from fastapi import APIRouter, Depends
from app.agents import get_agent_service, AnalysisRequest

router = APIRouter()

@router.post("/analyze")
async def analyze(request: AnalysisRequest):
    service = get_agent_service()
    return await service.process_analysis_request(request)
```

### Frontend Integration

The schema models in `schemas.py` define the contract for frontend integration:

- **POST /analyze**: Submit analysis requests
- **GET /agents**: List all agents and their status
- **GET /agents/{type}**: Get detailed agent info including memory state
- **GET /status**: System health check

## Best Practices

### For Developers

1. **Don't Mock in Tests**: Use real Letta API calls to validate actual behavior
2. **Respect Memory Autonomy**: Let agents manage their own memory blocks
3. **Monitor Memory Evolution**: Periodically check how agents' knowledge grows
4. **Handle Errors Gracefully**: Letta API calls can fail; implement retries
5. **Rate Limiting**: Be mindful of API rate limits in production

### For Agents

1. **Clear Memory Blocks**: Use descriptive, structured content in memory blocks
2. **Selective Archival Storage**: Store significant findings, not every interaction
3. **Update Strategies**: Allow routing strategy and methodologies to evolve
4. **Context Management**: Keep memory blocks concise to fit in context window

## Extending the System

### Adding a New Specialized Agent

1. **Define Configuration** (`config.py`):
   ```python
   MARKETING_ANALYST_MEMORY_BLOCKS = [...]
   AgentType.MARKETING_ANALYST = "marketing_analyst"
   ```

2. **Create Implementation** (`marketing_analyst.py`):
   ```python
   class MarketingAnalystAgent:
       # Similar structure to SpecializedAnalystAgent
   ```

3. **Update Service** (`service.py`):
   ```python
   # Add to initialize() method
   marketing_agent_id = self._create_agent(AgentType.MARKETING_ANALYST)
   self._marketing_analyst = MarketingAnalystAgent(...)
   ```

4. **Update Router**:
   - Modify router memory block to include new agent
   - Router will learn when to route to new analyst

### Customizing Memory Blocks

Memory blocks can be updated in `config.py`. Changes take effect on next agent creation:

```python
SPECIALIZED_ANALYST_MEMORY_BLOCKS = [
    {
        "label": "persona",
        "value": "Updated persona with new capabilities..."
    },
    # Add new blocks as needed
    {
        "label": "risk_assessment_framework",
        "value": "Framework for assessing risks..."
    }
]
```

## Troubleshooting

### Common Issues

**"Letta API key not provided"**
- Set `LETTA_API_KEY` environment variable
- Or pass to `AgentService(letta_api_key="...")`

**"Agent not initialized"**
- Call `await service.initialize()` before processing requests
- Or let auto-initialization occur on first request

**Slow Response Times**
- Letta API calls involve LLM inference (3-10 seconds typical)
- Consider implementing caching for repeated queries
- Use async patterns to handle concurrent requests

**Memory Blocks Not Updating**
- Agents self-update memory over time, not immediately
- Check if agent's persona encourages memory updates
- Some updates may require multiple interactions to trigger

## Performance Considerations

- **Initialization**: Creating agents takes 5-15 seconds (do once on startup)
- **Routing**: 2-5 seconds per routing decision
- **Analysis**: 5-20 seconds depending on complexity
- **Total Request Time**: 10-30 seconds typical
- **Concurrent Requests**: Service handles concurrency via Letta's infrastructure

## Security Notes

- **API Key**: Never commit `LETTA_API_KEY` to version control
- **User Data**: User queries and analyses are sent to Letta's servers
- **Memory Persistence**: Agent memory persists on Letta's infrastructure
- **Self-Hosted Option**: Use `LETTA_BASE_URL` to point to self-hosted Letta for data privacy

## Resources

- [Letta Documentation](https://docs.letta.com/)
- [Letta GitHub](https://github.com/letta-ai/letta)
- [Multi-Agent Systems Guide](https://docs.letta.com/guides/agents/multi-agent)
- [Memory Management](https://docs.letta.com/guides/agents/memory)

## License

Part of memAgentDemo project. See root LICENSE file.
