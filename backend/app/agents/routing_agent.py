"""
Routing Agent Implementation

The routing agent is the entry point for all user requests. It analyzes
incoming queries and determines which analyst agent should handle them.

Design decisions:
1. Uses Letta's memory blocks to store routing strategy and learn from patterns
2. Maintains awareness of all available agents via 'available_agents' memory block
3. Uses send_message tool (built into Letta) for agent-to-agent communication
4. Stores routing history in memory to improve future routing decisions

Architecture:
- Router doesn't directly process analytical requests
- It acts as an intelligent dispatcher/orchestrator
- Learning capability: updates routing_strategy block based on successful patterns
"""

from typing import Dict, Any, Optional, List
from letta_client import Letta
from .config import AgentType, AGENT_CONFIGS
from .schemas import RoutingDecision


class RoutingAgent:
    """
    Routing Agent that dispatches requests to appropriate analyst agents.

    The routing agent uses Letta's memory system to maintain and evolve its
    routing strategy over time. It doesn't have hardcoded routing rules;
    instead, the rules live in its editable memory blocks.
    """

    def __init__(self, letta_client: Letta, agent_id: str):
        """
        Initialize the routing agent.

        Args:
            letta_client: Connected Letta client instance
            agent_id: Letta agent ID for this routing agent

        Design note: We store the agent_id rather than the full agent object
        to keep this lightweight and avoid serialization issues.
        """
        self.client = letta_client
        self.agent_id = agent_id
        self._agent_registry: Dict[AgentType, str] = {}

    def register_analyst(self, agent_type: AgentType, agent_id: str) -> None:
        """
        Register an analyst agent that this router can dispatch to.

        This builds the routing table that maps agent types to their Letta agent IDs.
        The router needs to know these IDs to use the send_message tool.

        Args:
            agent_type: Type of analyst agent (SPECIALIZED_ANALYST or GENERALIST_ANALYST)
            agent_id: Letta agent ID for the analyst

        Design note: We maintain this registry in memory rather than in the agent's
        memory blocks because agent IDs are infrastructure concerns, not knowledge
        that the agent needs to reason about.
        """
        if agent_type == AgentType.ROUTER:
            raise ValueError("Cannot register a router as an analyst")
        self._agent_registry[agent_type] = agent_id

    def update_available_agents_memory(self) -> None:
        """
        Update the router's memory block with current available agents.

        This syncs the agent's knowledge with the actual registered agents.
        We do this as a separate step rather than automatically because
        we want explicit control over when agent memory is updated.

        Design note: Using Letta's block update API to modify the agent's memory.
        This is preferred over having the agent update itself because it ensures
        consistency during initialization.
        """
        # Get current memory blocks to find the 'available_agents' block
        agent_state = self.client.agents.get(agent_id=self.agent_id)

        # Build the updated content for available_agents block
        agents_info = "Available analyst agents:\n"
        for agent_type, agent_id in self._agent_registry.items():
            config = AGENT_CONFIGS[agent_type]
            agents_info += f"- {agent_type.value} (ID: {agent_id}): {config['description']}\n"

        # Find and update the available_agents memory block
        # Note: In production, you'd use the block update API
        # For now, we'll note this as a TODO for when agents are created
        # The initial memory blocks will be set during agent creation

    def route_request(
        self,
        user_query: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Determine which analyst agent should handle a user request.

        This method sends the user's query to the routing agent's Letta instance,
        which uses its memory blocks (routing_strategy, available_agents) to decide.

        Args:
            user_query: The user's analytical question or request
            user_id: Unique identifier for the user
            context: Optional additional context about the request

        Returns:
            RoutingDecision with target agent type and reasoning

        Design decisions:
        1. We send a structured message to the routing agent asking for a decision
        2. The agent uses its persona and routing_strategy memory to reason
        3. We parse the agent's response to extract the routing decision
        4. The agent can update its routing_strategy based on patterns it learns

        Note: This is a synchronous call. For production, consider async implementation.
        """
        # Construct the routing request message
        routing_prompt = self._build_routing_prompt(user_query, user_id, context)

        # Send message to the routing agent
        # The agent will use its memory blocks to determine routing
        response = self.client.agents.messages.create(
            agent_id=self.agent_id,
            messages=[{
                "role": "user",
                "content": routing_prompt
            }]
        )

        # Parse the agent's response to extract routing decision
        # The agent should respond with which analyst to use and why
        decision = self._parse_routing_response(response)

        return decision

    def _build_routing_prompt(
        self,
        user_query: str,
        user_id: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Build a prompt for the routing agent to analyze.

        The prompt should be clear and structured to help the agent make
        a good decision using its routing_strategy memory block.

        Design note: We use a structured format to make it easy for the agent
        to extract the relevant information and apply its routing strategy.
        """
        prompt = f"""New analysis request needs routing:

User ID: {user_id}
Query: {user_query}"""

        if context:
            prompt += f"\nAdditional Context: {context}"

        prompt += """

Please determine which analyst agent should handle this request:
1. Specialized Analyst (Financial) - for financial/quantitative analysis
2. Generalist Analyst - for other analytical tasks

Respond with your decision in this format:
ROUTE_TO: [agent_type]
REASONING: [your reasoning]

Use your routing_strategy memory block to guide your decision.
"""
        return prompt

    def _parse_routing_response(self, response: Any) -> RoutingDecision:
        """
        Parse the routing agent's response to extract the routing decision.

        Args:
            response: Response object from Letta agent

        Returns:
            RoutingDecision with target agent and reasoning

        Design note: This is a simple parser for the expected format.
        In production, you might want more robust parsing or use structured outputs.
        """
        # Extract the text content from the response
        # Letta returns a list of message objects
        response_text = ""
        if hasattr(response, 'messages') and response.messages:
            for msg in response.messages:
                if hasattr(msg, 'content') and msg.content:
                    response_text += msg.content + "\n"

        # Parse the ROUTE_TO and REASONING fields
        route_to = None
        reasoning = ""

        for line in response_text.split('\n'):
            if line.startswith('ROUTE_TO:'):
                route_to_str = line.replace('ROUTE_TO:', '').strip().lower()
                # Map the string to AgentType
                if 'specialized' in route_to_str or 'financial' in route_to_str:
                    route_to = AgentType.SPECIALIZED_ANALYST
                elif 'generalist' in route_to_str:
                    route_to = AgentType.GENERALIST_ANALYST
            elif line.startswith('REASONING:'):
                reasoning = line.replace('REASONING:', '').strip()

        # Default to generalist if parsing failed
        if route_to is None:
            route_to = AgentType.GENERALIST_ANALYST
            reasoning = "Failed to parse routing decision; defaulting to generalist analyst"

        return RoutingDecision(
            target_agent_type=route_to,
            reasoning=reasoning
        )

    def get_target_agent_id(self, agent_type: AgentType) -> str:
        """
        Get the Letta agent ID for a given agent type.

        Args:
            agent_type: Type of agent to get ID for

        Returns:
            Letta agent ID

        Raises:
            KeyError if agent type not registered
        """
        if agent_type not in self._agent_registry:
            raise KeyError(f"Agent type {agent_type} not registered with router")
        return self._agent_registry[agent_type]

    @property
    def registered_agents(self) -> Dict[AgentType, str]:
        """Get the current registry of agents."""
        return self._agent_registry.copy()
