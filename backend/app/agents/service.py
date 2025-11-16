"""
Agent Service Module

This is the main orchestration service that manages the multi-agent system.
It coordinates the lifecycle and interactions of all agents.

Design decisions:
1. Singleton pattern for service ensures consistent state across requests
2. Lazy initialization of agents on first request (not on import)
3. Service layer abstracts Letta implementation details from API layer
4. Provides high-level methods for common operations

Architecture:
- Service owns the Letta client connection
- Service creates and manages all agent instances
- Service coordinates the flow: routing -> analysis -> response
- Service handles error cases and fallbacks
"""

import os
import time
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from letta_client import Letta

from .config import AgentType, AGENT_CONFIGS, DEFAULT_MODEL
from .schemas import (
    AnalysisRequest,
    AnalysisResponse,
    AgentInfo,
    AgentDetailResponse,
    MemoryBlock,
    AgentSystemStatus
)
from .routing_agent import RoutingAgent
from .specialized_analyst import SpecializedAnalystAgent
from .generalist_analyst import GeneralistAnalystAgent


class AgentService:
    """
    Main service for managing the multi-agent system.

    This service:
    - Initializes connection to Letta
    - Creates and manages all agents
    - Orchestrates request routing and analysis
    - Provides health and status information
    """

    def __init__(self, letta_api_key: Optional[str] = None, letta_base_url: Optional[str] = None):
        """
        Initialize the agent service.

        Args:
            letta_api_key: API key for Letta service (if None, reads from env)
            letta_base_url: Base URL for Letta service (if None, uses default)

        Design decisions:
        - API key from environment variable for security (don't hardcode)
        - Base URL configurable to support different environments (dev/staging/prod)
        - Lazy agent initialization (agents created on first use, not in __init__)
        """
        # Get Letta API key from environment if not provided
        # Using LETTA_API_KEY as the environment variable name (Letta convention)
        self.letta_api_key = letta_api_key or os.getenv("LETTA_API_KEY")

        if not self.letta_api_key:
            raise ValueError(
                "Letta API key not provided. Set LETTA_API_KEY environment variable "
                "or pass letta_api_key parameter."
            )

        # Initialize Letta client
        # If base_url is not provided, Letta client uses its default
        self.letta_base_url = letta_base_url
        self.letta_client = self._create_letta_client()

        # Agent instances (initialized lazily)
        self._router: Optional[RoutingAgent] = None
        self._specialized_analyst: Optional[SpecializedAnalystAgent] = None
        self._generalist_analyst: Optional[GeneralistAnalystAgent] = None

        # Store Letta agent IDs for reference
        self._agent_ids: Dict[AgentType, str] = {}

        # Track initialization status
        self._initialized = False

    def _create_letta_client(self) -> Letta:
        """
        Create and configure the Letta client.

        Design note: Separated into its own method for easier testing and
        potential retry logic in production.
        """
        client_kwargs = {"token": self.letta_api_key}

        if self.letta_base_url:
            client_kwargs["base_url"] = self.letta_base_url

        return Letta(**client_kwargs)

    async def initialize(self) -> None:
        """
        Initialize all agents in the system.

        This creates the three Letta agents with their respective memory blocks
        and sets up the routing relationships.

        Design decisions:
        1. Call this explicitly rather than in __init__ for better control
        2. Async to support potential async Letta SDK in future
        3. Idempotent - can be called multiple times safely
        4. Creates agents in order: analysts first, then router
           (router needs to know about analysts)

        Note: Currently Letta SDK is synchronous, but we use async here
        for future compatibility and to match FastAPI's async patterns.
        """
        if self._initialized:
            return  # Already initialized

        try:
            # Create specialized analyst agent
            specialized_agent_id = self._create_agent(AgentType.SPECIALIZED_ANALYST)
            self._agent_ids[AgentType.SPECIALIZED_ANALYST] = specialized_agent_id
            self._specialized_analyst = SpecializedAnalystAgent(
                self.letta_client,
                specialized_agent_id
            )

            # Create generalist analyst agent
            generalist_agent_id = self._create_agent(AgentType.GENERALIST_ANALYST)
            self._agent_ids[AgentType.GENERALIST_ANALYST] = generalist_agent_id
            self._generalist_analyst = GeneralistAnalystAgent(
                self.letta_client,
                generalist_agent_id
            )

            # Create routing agent
            router_agent_id = self._create_agent(AgentType.ROUTER)
            self._agent_ids[AgentType.ROUTER] = router_agent_id
            self._router = RoutingAgent(self.letta_client, router_agent_id)

            # Register analysts with router
            self._router.register_analyst(
                AgentType.SPECIALIZED_ANALYST,
                specialized_agent_id
            )
            self._router.register_analyst(
                AgentType.GENERALIST_ANALYST,
                generalist_agent_id
            )

            self._initialized = True

        except Exception as e:
            # Clean up any partially created agents on failure
            await self._cleanup_agents()
            raise RuntimeError(f"Failed to initialize agent system: {str(e)}")

    def _create_agent(self, agent_type: AgentType) -> str:
        """
        Create a Letta agent of the specified type.

        Args:
            agent_type: Type of agent to create

        Returns:
            The Letta agent ID

        Design decisions:
        1. Uses memory blocks from AGENT_CONFIGS
        2. Uses DEFAULT_MODEL (GPT-4) for all agents
        3. Returns just the ID for lightweight storage

        Note: Letta persists agents on their servers, so agents survive
        service restarts. In production, you might want to check if agents
        already exist before creating new ones.
        """
        config = AGENT_CONFIGS[agent_type]

        # Create the agent with Letta
        agent_state = self.letta_client.agents.create(
            model=DEFAULT_MODEL,
            memory_blocks=config["memory_blocks"],
            # Note: Tool configuration would go here
            # Letta has some built-in tools (send_message, archival_memory_*)
            # Custom tools would be added via tools parameter
        )

        # Extract and return the agent ID
        return agent_state.id

    async def _cleanup_agents(self) -> None:
        """
        Clean up agents in case of initialization failure.

        This deletes any partially created agents to avoid orphaned resources.

        Design note: This is a safety mechanism for initialization failures.
        In production, you might want more sophisticated cleanup logic.
        """
        for agent_type, agent_id in self._agent_ids.items():
            try:
                self.letta_client.agents.delete(agent_id=agent_id)
            except Exception:
                # Log but don't raise - best effort cleanup
                pass

        self._agent_ids.clear()
        self._router = None
        self._specialized_analyst = None
        self._generalist_analyst = None

    async def process_analysis_request(
        self,
        request: AnalysisRequest
    ) -> AnalysisResponse:
        """
        Process an analysis request through the multi-agent system.

        Flow:
        1. Send request to routing agent
        2. Routing agent decides which analyst to use
        3. Forward request to selected analyst
        4. Return analyst's response with routing metadata

        Args:
            request: The analysis request from the user

        Returns:
            AnalysisResponse with result and routing information

        Design decisions:
        - Single entry point for all analysis requests
        - Routing is transparent to the caller
        - Timing information included for monitoring
        - Graceful fallback to generalist on routing errors
        """
        if not self._initialized:
            await self.initialize()

        start_time = time.time()
        request_id = str(uuid.uuid4())

        try:
            # Step 1: Get routing decision
            routing_decision = self._router.route_request(
                user_query=request.query,
                user_id=request.user_id,
                context=request.context
            )

            # Step 2: Get the appropriate analyst agent
            if routing_decision.target_agent_type == AgentType.SPECIALIZED_ANALYST:
                analyst = self._specialized_analyst
            else:
                analyst = self._generalist_analyst

            # Step 3: Execute the analysis
            result = analyst.analyze(
                query=request.query,
                user_id=request.user_id,
                context=request.context
            )

            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000

            # Step 4: Build and return response
            return AnalysisResponse(
                request_id=request_id,
                result=result,
                routed_to=routing_decision.target_agent_type,
                routing_reasoning=routing_decision.reasoning,
                agent_id=self._agent_ids[routing_decision.target_agent_type],
                processing_time_ms=processing_time_ms
            )

        except Exception as e:
            # On error, provide a fallback response
            # In production, you'd want more sophisticated error handling
            processing_time_ms = (time.time() - start_time) * 1000

            return AnalysisResponse(
                request_id=request_id,
                result=f"Error processing request: {str(e)}",
                routed_to=AgentType.GENERALIST_ANALYST,  # Default fallback
                routing_reasoning="Error occurred during routing or analysis",
                agent_id=self._agent_ids.get(AgentType.GENERALIST_ANALYST, "unknown"),
                processing_time_ms=processing_time_ms
            )

    async def get_agent_info(self, agent_type: AgentType) -> AgentDetailResponse:
        """
        Get detailed information about a specific agent.

        Args:
            agent_type: Type of agent to query

        Returns:
            Detailed agent information including memory blocks

        Design note: Useful for monitoring and debugging agent state.
        """
        if not self._initialized:
            await self.initialize()

        agent_id = self._agent_ids.get(agent_type)
        if not agent_id:
            raise ValueError(f"Agent type {agent_type} not initialized")

        # Get agent state from Letta
        agent_state = self.letta_client.agents.get(agent_id=agent_id)

        # Extract memory blocks
        memory_blocks = []
        if hasattr(agent_state, 'memory') and hasattr(agent_state.memory, 'blocks'):
            for block in agent_state.memory.blocks:
                if hasattr(block, 'label') and hasattr(block, 'value'):
                    memory_blocks.append(MemoryBlock(
                        label=block.label,
                        value=block.value
                    ))

        return AgentDetailResponse(
            agent_id=agent_id,
            agent_type=agent_type,
            description=AGENT_CONFIGS[agent_type]["description"],
            memory_blocks=memory_blocks,
            created_at=datetime.now()  # Letta might provide actual creation time
        )

    async def get_system_status(self) -> AgentSystemStatus:
        """
        Get overall system status.

        Returns:
            Status of the entire agent system

        Design note: Health check endpoint to verify system is operational.
        """
        try:
            if not self._initialized:
                return AgentSystemStatus(
                    status="uninitialized",
                    agents=[],
                    letta_connected=True,  # We have a client
                    errors=["Agent system not yet initialized"]
                )

            # Build agent info list
            agents = []
            for agent_type, agent_id in self._agent_ids.items():
                agents.append(AgentInfo(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    description=AGENT_CONFIGS[agent_type]["description"],
                    created_at=None  # Could fetch from Letta if available
                ))

            return AgentSystemStatus(
                status="healthy",
                agents=agents,
                letta_connected=True,
                errors=None
            )

        except Exception as e:
            return AgentSystemStatus(
                status="unhealthy",
                agents=[],
                letta_connected=False,
                errors=[str(e)]
            )


# Global service instance
# In production, this might be managed by a dependency injection system
_service_instance: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """
    Get the global agent service instance.

    This implements a simple singleton pattern. In production FastAPI apps,
    you might use dependency injection instead.

    Returns:
        The global AgentService instance
    """
    global _service_instance

    if _service_instance is None:
        _service_instance = AgentService()

    return _service_instance
