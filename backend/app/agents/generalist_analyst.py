"""
Generalist Analyst Agent Implementation

This agent handles analytical tasks that don't fall within specialized domains.
It serves as the fallback analyst for diverse requests and maintains broad
analytical capabilities.

Design decisions:
1. Similar architecture to specialized analyst but with broader scope
2. Uses memory blocks for analytical approaches and learning history
3. Stores diverse analysis results in archival memory
4. Adapts analytical approach based on request type
5. Learns patterns from handling diverse requests

Key difference from specialized analyst:
- Broader but shallower domain knowledge
- More flexible analytical approach selection
- Learns which approaches work best for different request types
"""

from typing import Dict, Any, Optional
from letta_client import Letta


class GeneralistAnalystAgent:
    """
    Generalist analytical agent for diverse analytical tasks.

    This agent handles requests that don't fit specialized domains, including:
    - General research and synthesis
    - Comparative analysis
    - Problem decomposition
    - Strategic analysis
    - Any analytical task outside specialized domains
    """

    def __init__(self, letta_client: Letta, agent_id: str):
        """
        Initialize the generalist analyst agent.

        Args:
            letta_client: Connected Letta client instance
            agent_id: Letta agent ID for this generalist analyst

        Design note: Same lightweight initialization as other agents.
        State lives in Letta, not in this Python object.
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
        Perform a general analytical task.

        The agent will:
        1. Review its analytical_approaches memory block to select appropriate method
        2. Search archival memory for similar past analyses
        3. Perform the analysis using selected approach
        4. Update learning_history memory block with patterns learned
        5. Store significant results in archival memory

        Args:
            query: The analytical question or task
            user_id: Unique identifier for the user making the request
            context: Optional additional context

        Returns:
            The analysis result as a string

        Design decisions:
        - Agent has more autonomy in selecting analytical approach
        - Encourages exploration of different methodologies
        - Learning history helps agent recognize what works for different request types
        - This adaptability is key for a generalist agent
        """
        # Build the analysis prompt
        analysis_prompt = self._build_analysis_prompt(query, user_id, context)

        # Send the request to the Letta agent
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
        Build a structured prompt for general analysis.

        The prompt emphasizes flexibility and encourages the agent to select
        the most appropriate analytical approach.

        Design note: Unlike the specialized analyst, we don't prescribe a specific
        analytical framework. The agent should use its analytical_approaches memory
        to select the best fit.
        """
        prompt = f"""General Analysis Request:

User: {user_id}
Question: {query}"""

        if context:
            prompt += f"\n\nAdditional Context:\n{self._format_context(context)}"

        prompt += """

Please perform a thorough analysis addressing this request.

Review your analytical_approaches memory block and select the most appropriate
method for this question. Consider searching your archival memory for similar
past analyses that might provide insights.

After completing the analysis, update your learning_history if this request
reveals new patterns or effective approaches. Store significant findings in
archival memory for future reference.

Provide a clear, well-structured analysis with:
1. Analytical approach used and why it was selected
2. Key findings and insights
3. Supporting evidence or reasoning
4. Relevant caveats or limitations
5. Practical recommendations or next steps (if appropriate)
"""
        return prompt

    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        Format the context dictionary into a readable string.

        Design note: Identical to specialized analyst's implementation.
        Could be refactored into a shared utility function.
        """
        return "\n".join(f"- {key}: {value}" for key, value in context.items())

    def _extract_analysis_result(self, response: Any) -> str:
        """
        Extract the analysis result from the agent's response.

        Args:
            response: Response object from Letta agent

        Returns:
            The analysis text as a string

        Design note: Same implementation as specialized analyst.
        This could be refactored into a base class or utility function.
        """
        result_parts = []

        if hasattr(response, 'messages') and response.messages:
            for msg in response.messages:
                # Extract user-facing messages (role="assistant")
                if hasattr(msg, 'role') and msg.role == 'assistant':
                    if hasattr(msg, 'content') and msg.content:
                        result_parts.append(msg.content)

        # Join all parts to form the complete analysis
        result = "\n\n".join(result_parts)

        # Fallback if no content was generated
        if not result.strip():
            result = "Analysis completed, but no textual result was generated."

        return result

    def get_memory_state(self) -> Dict[str, Any]:
        """
        Retrieve the current state of this agent's memory blocks.

        Useful for:
        - Monitoring the agent's learning_history to see what it has learned
        - Inspecting analytical_approaches to understand its methodologies
        - Debugging and auditing agent behavior

        Returns:
            Dictionary mapping memory block labels to their current values

        Design note: Same implementation as specialized analyst.
        Read-only to preserve agent autonomy in memory management.
        """
        agent_state = self.client.agents.get(agent_id=self.agent_id)

        memory_blocks = {}
        if hasattr(agent_state, 'memory') and hasattr(agent_state.memory, 'blocks'):
            for block in agent_state.memory.blocks:
                if hasattr(block, 'label') and hasattr(block, 'value'):
                    memory_blocks[block.label] = block.value

        return memory_blocks

    def get_learning_insights(self) -> Dict[str, Any]:
        """
        Get insights from the agent's learning history.

        This method specifically examines the learning_history memory block
        to extract patterns the agent has discovered.

        Returns:
            Dictionary with learning insights

        Design note: This is unique to the generalist agent. The learning_history
        block is particularly important for this agent because it learns across
        diverse domains. This method provides visibility into that learning.
        """
        memory_state = self.get_memory_state()

        learning_history = memory_state.get('learning_history', '')

        # Parse the learning history to extract insights
        # For now, return the raw content
        # In production, you might parse this more intelligently
        return {
            'raw_history': learning_history,
            'summary': 'Learning history tracks successful analytical approaches and patterns'
        }

    def search_past_analyses(self, search_query: str, limit: int = 5) -> list:
        """
        Search the agent's archival memory for past analyses.

        Similar to specialized analyst, but may return more diverse results
        since this agent handles varied request types.

        Args:
            search_query: Text query to search for in archival memory
            limit: Maximum number of results to return

        Returns:
            List of relevant past analysis excerpts

        Design note: Same conceptual implementation as specialized analyst.
        The archival memory will contain more varied content for this agent.

        Note: This is a hypothetical API based on Letta's documentation.
        """
        # Placeholder for Letta archival memory search
        # Exact implementation depends on SDK version

        # In practice:
        # results = self.client.agents.archival_memory.search(
        #     agent_id=self.agent_id,
        #     query=search_query,
        #     limit=limit
        # )

        return []
