"""
Specialized Analyst Agent Implementation

This agent specializes in financial and quantitative analysis tasks.
It maintains domain-specific knowledge in memory blocks and stores
analysis results in archival memory for future reference.

Design decisions:
1. Uses memory blocks for methodologies and domain knowledge that persist across sessions
2. Uses archival memory (via archival_memory_insert) to store detailed analysis results
3. Can search archival memory (via archival_memory_search) to reference past analyses
4. Learns over time by updating its methodologies and domain_knowledge memory blocks

Benefits of this approach:
- Agent maintains long-term memory of past analyses
- Can reference similar past work to improve current analysis
- Domain knowledge evolves based on new information and successful patterns
- Memory persists even if the agent is restarted
"""

from typing import Dict, Any, Optional
from letta_client import Letta


class SpecializedAnalystAgent:
    """
    Financial/Quantitative Analysis specialist agent.

    This agent handles domain-specific analytical tasks related to finance,
    including financial statement analysis, market research, ROI calculations,
    revenue modeling, and financial forecasting.
    """

    def __init__(self, letta_client: Letta, agent_id: str):
        """
        Initialize the specialized analyst agent.

        Args:
            letta_client: Connected Letta client instance
            agent_id: Letta agent ID for this specialized analyst

        Design note: Similar to routing agent, we store minimal state here.
        The agent's knowledge lives in its Letta memory blocks, not in this Python object.
        This makes the agent stateless from the application perspective - all state
        is managed by Letta, which provides persistence.
        """
        self.client = letta_client
        self.agent_id = agent_id

    def analyze(
        self,
        query: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Perform a specialized financial/quantitative analysis.

        This method sends the analytical request to the Letta agent, which will:
        1. Use its persona and methodologies memory blocks to guide the analysis
        2. Search archival memory for relevant past analyses
        3. Perform the analysis using its domain knowledge
        4. Store the analysis result in archival memory for future reference
        5. Update its memory blocks if it learns something new

        Args:
            query: The analytical question or task
            user_id: Unique identifier for the user making the request
            context: Optional additional context (data, constraints, etc.)

        Returns:
            The analysis result as a string

        Design decisions:
        - Agent autonomously decides whether to search archival memory
        - Agent decides whether the analysis is worth storing for future reference
        - We don't explicitly instruct these steps; the agent's persona guides it
        - This allows the agent to be more intelligent and adaptive
        """
        # Build the analysis prompt
        analysis_prompt = self._build_analysis_prompt(query, user_id, context)

        # Send the request to the Letta agent
        # The agent will use its memory blocks and tools to perform analysis
        response = self.client.agents.messages.create(
            agent_id=self.agent_id,
            messages=[{
                "role": "user",
                "content": analysis_prompt
            }]
        )

        # Extract and return the analysis result
        result = self._extract_analysis_result(response)

        return result

    def _build_analysis_prompt(
        self,
        query: str,
        user_id: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Build a structured prompt for the financial analysis.

        The prompt should be clear about what's being asked while giving
        the agent flexibility in how it approaches the analysis.

        Design note: We provide context but don't micromanage the analysis approach.
        The agent's methodologies memory block guides its analytical process.
        """
        prompt = f"""Financial Analysis Request:

User: {user_id}
Question: {query}"""

        if context:
            prompt += f"\n\nAdditional Context:\n{self._format_context(context)}"

        prompt += """

Please perform a thorough financial analysis addressing this request.
Use your methodologies and domain knowledge. If relevant, search your
archival memory for similar past analyses. Store significant findings
in archival memory for future reference.

Provide a clear, well-structured analysis with:
1. Key findings and insights
2. Supporting data and calculations (if applicable)
3. Relevant caveats or limitations
4. Actionable recommendations (if appropriate)
"""
        return prompt

    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        Format the context dictionary into a readable string.

        Design note: Simple key-value formatting for now. Could be enhanced
        to handle nested structures, dataframes, etc.
        """
        return "\n".join(f"- {key}: {value}" for key, value in context.items())

    def _extract_analysis_result(self, response: Any) -> str:
        """
        Extract the analysis result from the agent's response.

        Args:
            response: Response object from Letta agent

        Returns:
            The analysis text as a string

        Design note: Letta agents may return multiple message objects
        (e.g., tool calls, thoughts, final response). We want to extract
        the substantive analytical content.
        """
        result_parts = []

        if hasattr(response, 'messages') and response.messages:
            for msg in response.messages:
                # We want user-facing messages (role="assistant")
                # Skip internal tool calls and function results
                if hasattr(msg, 'role') and msg.role == 'assistant':
                    if hasattr(msg, 'content') and msg.content:
                        result_parts.append(msg.content)

        # Join all parts to form the complete analysis
        result = "\n\n".join(result_parts)

        # If we didn't get any content, provide a fallback message
        if not result.strip():
            result = "Analysis completed, but no textual result was generated."

        return result

    def get_memory_state(self) -> Dict[str, Any]:
        """
        Retrieve the current state of this agent's memory blocks.

        This is useful for:
        - Debugging and monitoring what the agent knows
        - Inspecting how the agent's knowledge has evolved
        - Auditing the agent's domain knowledge and methodologies

        Returns:
            Dictionary mapping memory block labels to their current values

        Design note: This is a read-only operation. We don't provide a direct
        way to update memory blocks from the application layer because we want
        the agent to self-manage its memory. External updates would bypass the
        agent's learning mechanisms.
        """
        agent_state = self.client.agents.get(agent_id=self.agent_id)

        memory_blocks = {}
        if hasattr(agent_state, 'memory') and hasattr(agent_state.memory, 'blocks'):
            for block in agent_state.memory.blocks:
                if hasattr(block, 'label') and hasattr(block, 'value'):
                    memory_blocks[block.label] = block.value

        return memory_blocks

    def search_past_analyses(self, search_query: str, limit: int = 5) -> list:
        """
        Search the agent's archival memory for past analyses.

        This method allows external code to query what the agent has learned.
        The agent itself also has this capability via archival_memory_search tool.

        Args:
            search_query: Text query to search for in archival memory
            limit: Maximum number of results to return

        Returns:
            List of relevant past analysis excerpts

        Design note: This exposes the agent's archival memory to the application,
        which can be useful for building features like "show similar past analyses"
        in the UI. However, the primary consumer of archival memory is the agent itself.

        Note: This is a hypothetical API based on Letta's documentation. The exact
        implementation may vary based on the actual Letta SDK version.
        """
        # This would use Letta's archival memory search API
        # The exact implementation depends on the SDK version
        # For now, this is a placeholder for the concept

        # In practice, you'd call something like:
        # results = self.client.agents.archival_memory.search(
        #     agent_id=self.agent_id,
        #     query=search_query,
        #     limit=limit
        # )

        # For now, return empty list as this is conceptual
        return []
