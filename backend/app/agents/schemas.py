"""
Agent Schemas Module

Defines Pydantic models for agent-related API requests and responses.
These schemas provide:
- Type validation for API inputs/outputs
- Automatic API documentation via FastAPI
- Serialization/deserialization of agent data

Design decisions:
1. Separate request and response models for clarity
2. Include optional fields for flexibility in API evolution
3. Use descriptive field names and examples for better API documentation
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

from .config import AgentType


# ============================================================================
# Request Schemas
# ============================================================================

class AgentCreateRequest(BaseModel):
    """
    Request model for creating a new agent.

    This is used when manually creating agents (primarily for testing/admin).
    In normal operation, agents are initialized on service startup.
    """
    agent_type: AgentType = Field(
        ...,
        description="Type of agent to create"
    )
    custom_memory_blocks: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Optional custom memory blocks to override defaults"
    )
    model_config = ConfigDict(use_enum_values=True)


class AnalysisRequest(BaseModel):
    """
    Request model for submitting an analysis task to the agent system.

    This is the primary entry point for user requests. The routing agent
    will receive this and determine which analyst should handle it.
    """
    user_id: str = Field(
        ...,
        description="Unique identifier for the user making the request",
        examples=["user_123"]
    )
    query: str = Field(
        ...,
        description="The analytical question or task to be performed",
        examples=["Analyze the financial performance of Company X in Q4 2024"]
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context or metadata for the analysis"
    )


class AgentMessageRequest(BaseModel):
    """
    Request model for sending a direct message to a specific agent.

    Used for testing and debugging agent interactions.
    """
    agent_id: str = Field(
        ...,
        description="Letta agent ID to send message to"
    )
    message: str = Field(
        ...,
        description="Message content to send to the agent"
    )


# ============================================================================
# Response Schemas
# ============================================================================

class MemoryBlock(BaseModel):
    """
    Represents a single memory block from a Letta agent.

    Memory blocks are the in-context memory that agents can self-edit.
    This model is used to expose agent memory state via API.
    """
    label: str = Field(
        ...,
        description="Label/name of the memory block"
    )
    value: str = Field(
        ...,
        description="Current content of the memory block"
    )


class AgentInfo(BaseModel):
    """
    Basic information about an agent.

    Used for listing agents and showing their current status.
    """
    agent_id: str = Field(
        ...,
        description="Letta-assigned unique identifier for the agent"
    )
    agent_type: AgentType = Field(
        ...,
        description="Type of agent (router, specialized_analyst, or generalist_analyst)"
    )
    description: str = Field(
        ...,
        description="Human-readable description of agent's purpose"
    )
    created_at: Optional[datetime] = Field(
        None,
        description="Timestamp when agent was created"
    )
    model_config = ConfigDict(use_enum_values=True)


class AgentDetailResponse(BaseModel):
    """
    Detailed information about a specific agent.

    Includes memory blocks to show what the agent currently "knows".
    Useful for debugging and monitoring agent state.
    """
    agent_id: str
    agent_type: AgentType
    description: str
    memory_blocks: List[MemoryBlock] = Field(
        ...,
        description="Current state of agent's memory blocks"
    )
    created_at: Optional[datetime] = None
    model_config = ConfigDict(use_enum_values=True)


class AnalysisResponse(BaseModel):
    """
    Response from an analysis request.

    Contains the result of the analysis and metadata about which agent
    handled it and how it was routed.
    """
    request_id: str = Field(
        ...,
        description="Unique identifier for this analysis request"
    )
    result: str = Field(
        ...,
        description="The analytical result or answer from the agent"
    )
    routed_to: AgentType = Field(
        ...,
        description="Which analyst agent handled this request"
    )
    routing_reasoning: Optional[str] = Field(
        None,
        description="Explanation of why this agent was selected"
    )
    agent_id: str = Field(
        ...,
        description="Specific Letta agent ID that processed the request"
    )
    processing_time_ms: Optional[float] = Field(
        None,
        description="Time taken to process the request in milliseconds"
    )
    model_config = ConfigDict(use_enum_values=True)


class AgentMessageResponse(BaseModel):
    """
    Response from sending a message to an agent.

    Used for testing and debugging agent interactions.
    """
    agent_id: str
    messages: List[Dict[str, Any]] = Field(
        ...,
        description="List of message objects returned by the agent"
    )
    final_response: Optional[str] = Field(
        None,
        description="Extracted final text response from the agent"
    )


class AgentSystemStatus(BaseModel):
    """
    Overall status of the agent system.

    Provides health check information and agent availability.
    """
    status: str = Field(
        ...,
        description="Overall system status",
        examples=["healthy", "degraded", "unhealthy"]
    )
    agents: List[AgentInfo] = Field(
        ...,
        description="List of all active agents in the system"
    )
    letta_connected: bool = Field(
        ...,
        description="Whether connection to Letta service is active"
    )
    errors: Optional[List[str]] = Field(
        None,
        description="Any errors or warnings about the agent system"
    )


# ============================================================================
# Internal Schemas (for service layer, not exposed via API)
# ============================================================================

class RoutingDecision(BaseModel):
    """
    Internal model representing a routing decision made by the router agent.

    This is used internally by the service layer to track routing logic.
    Not directly exposed via API.
    """
    target_agent_type: AgentType
    reasoning: str
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score for this routing decision (0-1)"
    )
    model_config = ConfigDict(use_enum_values=True)
