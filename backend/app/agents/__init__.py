"""
Agent Module

This module provides a memory-enabled multi-agent system using the Letta framework.
It implements a three-agent architecture:

1. Routing Agent: Dispatches requests to appropriate analysts
2. Specialized Analyst: Handles financial/quantitative analysis
3. Generalist Analyst: Handles general analytical requests

Key Features:
- Persistent memory across sessions via Letta memory blocks
- Archival memory for storing and retrieving past analyses
- Self-learning agents that improve over time
- Agent-to-agent communication for routing

Usage:
    from app.agents import get_agent_service, AgentService, AnalysisRequest

    # Get the service instance
    service = get_agent_service()

    # Initialize agents (first time only)
    await service.initialize()

    # Process an analysis request
    request = AnalysisRequest(
        user_id="user_123",
        query="Analyze Company X's Q4 financial performance"
    )
    response = await service.process_analysis_request(request)

See Also:
    - config.py: Agent configurations and memory block templates
    - service.py: Main orchestration service
    - schemas.py: API request/response models
"""

# Export main service components
from .service import AgentService, get_agent_service

# Export schemas for API layer
from .schemas import (
    AnalysisRequest,
    AnalysisResponse,
    AgentInfo,
    AgentDetailResponse,
    AgentSystemStatus,
    AgentMessageRequest,
    AgentMessageResponse,
    MemoryBlock,
)

# Export config types for type hints
from .config import AgentType

__all__ = [
    # Service
    "AgentService",
    "get_agent_service",
    # Request/Response schemas
    "AnalysisRequest",
    "AnalysisResponse",
    "AgentMessageRequest",
    "AgentMessageResponse",
    # Info/Status schemas
    "AgentInfo",
    "AgentDetailResponse",
    "AgentSystemStatus",
    "MemoryBlock",
    # Types
    "AgentType",
]
