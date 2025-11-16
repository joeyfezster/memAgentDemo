"""
Agent Configuration Module

This module defines the configuration for all Letta agents in the system.
It includes:
- Agent personas and system prompts
- Memory block templates
- Agent type definitions
- Tool configurations

Design decisions:
1. Using Letta's memory blocks instead of traditional system prompts for better persistence
   - Memory blocks are self-editable by agents, enabling learning over time
   - Blocks persist across sessions, unlike ephemeral context
2. Each agent type has distinct memory block templates that define their role and capabilities
3. Routing agent uses 'routing_history' block to learn from past routing decisions
"""

from enum import Enum
from typing import Dict, List


class AgentType(Enum):
    """
    Enum defining the types of agents in our multi-agent system.

    - ROUTER: Orchestrates requests and routes to appropriate analysts
    - SPECIALIZED_ANALYST: Handles domain-specific analytical tasks (financial analysis)
    - GENERALIST_ANALYST: Handles general analytical tasks and fallback requests
    """
    ROUTER = "router"
    SPECIALIZED_ANALYST = "specialized_analyst"
    GENERALIST_ANALYST = "generalist_analyst"


# Memory block templates for each agent type
# Memory blocks are Letta's way of giving agents persistent, editable memory
# They are always in-context, unlike archival memory which requires retrieval

ROUTER_MEMORY_BLOCKS = [
    {
        "label": "persona",
        "value": (
            "I am the Routing Agent. My primary responsibility is to analyze incoming "
            "user requests and determine which analyst agent is best suited to handle them. "
            "I maintain knowledge of all available analysts and their specializations. "
            "I prioritize routing to specialized analysts when the request matches their domain, "
            "and fall back to the generalist analyst for other requests. "
            "I learn from successful routing patterns and adapt over time."
        )
    },
    {
        "label": "routing_strategy",
        "value": (
            "Current routing strategy:\n"
            "1. Financial/quantitative analysis requests → Specialized Analyst\n"
            "2. Requests about stocks, markets, revenue, costs, ROI, financial metrics → Specialized Analyst\n"
            "3. All other analytical requests → Generalist Analyst\n"
            "4. Ambiguous requests → Ask clarifying questions or default to Generalist Analyst\n\n"
            "This strategy can be updated based on successful routing patterns."
        )
    },
    {
        "label": "available_agents",
        "value": (
            "Available analyst agents:\n"
            "- Specialized Analyst (Financial): Handles financial analysis, quantitative analysis, "
            "market research, financial modeling\n"
            "- Generalist Analyst: Handles general analytical tasks, research, synthesis, "
            "and any requests outside specialized domains"
        )
    }
]

SPECIALIZED_ANALYST_MEMORY_BLOCKS = [
    {
        "label": "persona",
        "value": (
            "I am a Specialized Financial Analyst Agent. I focus on financial and quantitative analysis. "
            "My expertise includes: financial statement analysis, market research, "
            "ROI calculations, revenue modeling, cost-benefit analysis, and financial forecasting. "
            "I use rigorous analytical methods and cite data sources when available. "
            "I maintain a repository of past analyses in my archival memory to improve future work."
        )
    },
    {
        "label": "methodologies",
        "value": (
            "Key analytical methodologies I employ:\n"
            "- Financial ratio analysis (liquidity, profitability, efficiency ratios)\n"
            "- Discounted cash flow (DCF) analysis\n"
            "- Comparative market analysis\n"
            "- Trend analysis and forecasting\n"
            "- Scenario and sensitivity analysis\n\n"
            "I continuously refine these methodologies based on outcomes."
        )
    },
    {
        "label": "domain_knowledge",
        "value": (
            "Financial analysis domain knowledge:\n"
            "- Understanding of financial statements (balance sheet, income statement, cash flow)\n"
            "- Market dynamics and economic indicators\n"
            "- Investment analysis principles\n"
            "- Risk assessment frameworks\n\n"
            "This knowledge is updated as I learn from new analyses."
        )
    }
]

GENERALIST_ANALYST_MEMORY_BLOCKS = [
    {
        "label": "persona",
        "value": (
            "I am a Generalist Analyst Agent. I handle a wide variety of analytical requests "
            "that don't fall within specialized domains. My capabilities include: "
            "general research, data synthesis, comparative analysis, problem decomposition, "
            "and strategic thinking. I adapt my approach based on the nature of each request "
            "and learn from diverse analytical challenges."
        )
    },
    {
        "label": "analytical_approaches",
        "value": (
            "General analytical approaches I use:\n"
            "- Problem decomposition and structured thinking\n"
            "- Research synthesis from multiple sources\n"
            "- Comparative analysis and pattern recognition\n"
            "- Root cause analysis\n"
            "- SWOT analysis for strategic questions\n"
            "- Systems thinking for complex problems\n\n"
            "I select and adapt approaches based on request type."
        )
    },
    {
        "label": "learning_history",
        "value": (
            "Track record of analytical tasks:\n"
            "- Types of requests successfully handled\n"
            "- Approaches that yielded best results\n"
            "- Areas where I've developed deeper knowledge\n\n"
            "This section updates as I complete more analyses."
        )
    }
]


# Configuration mapping for easy access
AGENT_CONFIGS: Dict[AgentType, Dict] = {
    AgentType.ROUTER: {
        "memory_blocks": ROUTER_MEMORY_BLOCKS,
        "description": "Routes user requests to appropriate analyst agents",
        # Using Letta's built-in send_message tool for agent-to-agent communication
        # This is preferred over custom HTTP-based routing as it maintains context
        "required_tools": ["send_message"],
    },
    AgentType.SPECIALIZED_ANALYST: {
        "memory_blocks": SPECIALIZED_ANALYST_MEMORY_BLOCKS,
        "description": "Specialized agent for financial and quantitative analysis",
        # Using archival memory tools to store analysis results for future reference
        # This enables the agent to learn from past analyses
        "required_tools": ["archival_memory_insert", "archival_memory_search"],
    },
    AgentType.GENERALIST_ANALYST: {
        "memory_blocks": GENERALIST_ANALYST_MEMORY_BLOCKS,
        "description": "Generalist agent for diverse analytical tasks",
        # Similar to specialized analyst, uses archival memory for learning
        "required_tools": ["archival_memory_insert", "archival_memory_search"],
    }
}


# Default Letta configuration
# Using GPT-4 as it provides better reasoning for complex analytical tasks
# Could be configured via environment variables in production
DEFAULT_MODEL = "openai/gpt-4"

# Alternative models that could be used:
# - "openai/gpt-3.5-turbo" - faster, cheaper, but less capable
# - "anthropic/claude-2" - good alternative with different strengths
# - Local models via Ollama integration if needed for privacy
