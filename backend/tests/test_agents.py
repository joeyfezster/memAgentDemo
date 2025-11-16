"""
Functional Tests for Agent System

These tests validate the agent system using real Letta API interactions.
No mocking or stubbing is used - we test the actual functionality.

Test Strategy:
1. Test agent initialization and configuration
2. Test routing decisions with real queries
3. Test analyst agent analysis capabilities
4. Test memory persistence
5. Test end-to-end request flow

Prerequisites:
- LETTA_API_KEY environment variable must be set
- Internet connection to reach Letta service (or self-hosted Letta server)

Note: These tests will create and delete real Letta agents during execution.
They may take longer than typical unit tests due to API calls.
"""

import pytest
import os
from typing import Optional

from app.agents import (
    AgentService,
    AnalysisRequest,
    AgentType,
)
from app.agents.config import AGENT_CONFIGS


# Test configuration
TEST_LETTA_API_KEY = os.getenv("LETTA_API_KEY")
TEST_USER_ID = "test_user_123"


@pytest.fixture
def skip_if_no_api_key():
    """
    Skip tests if Letta API key is not configured.

    This allows tests to be run in CI/CD environments where the API key
    might not be available, without failing the entire test suite.
    """
    if not TEST_LETTA_API_KEY:
        pytest.skip("LETTA_API_KEY environment variable not set")


@pytest.fixture
async def agent_service(skip_if_no_api_key):
    """
    Create an agent service for testing.

    This fixture:
    - Creates a fresh agent service instance
    - Initializes all agents
    - Yields the service for use in tests
    - Cleans up agents after tests complete

    Design note: Using a fixture ensures proper cleanup even if tests fail.
    This prevents orphaned Letta agents.
    """
    service = AgentService(letta_api_key=TEST_LETTA_API_KEY)

    # Initialize the service (creates all agents)
    await service.initialize()

    yield service

    # Cleanup: delete all created agents
    # This prevents accumulation of test agents in Letta
    try:
        await service._cleanup_agents()
    except Exception as e:
        # Log but don't fail test cleanup
        print(f"Warning: Failed to cleanup agents: {e}")


class TestAgentInitialization:
    """
    Tests for agent initialization and configuration.

    These tests verify that agents are created correctly with proper
    memory blocks and configuration.
    """

    async def test_service_initialization(self, skip_if_no_api_key):
        """
        Test that agent service initializes successfully.

        Validates:
        - Service creates without errors
        - All three agents are created
        - Agent IDs are assigned
        - Service is marked as initialized
        """
        service = AgentService(letta_api_key=TEST_LETTA_API_KEY)
        await service.initialize()

        # Verify service is initialized
        assert service._initialized is True

        # Verify all agents were created
        assert AgentType.ROUTER in service._agent_ids
        assert AgentType.SPECIALIZED_ANALYST in service._agent_ids
        assert AgentType.GENERALIST_ANALYST in service._agent_ids

        # Verify agents have valid IDs
        for agent_type, agent_id in service._agent_ids.items():
            assert agent_id is not None
            assert len(agent_id) > 0

        # Cleanup
        await service._cleanup_agents()

    async def test_agent_memory_blocks_configured(self, agent_service):
        """
        Test that agents are created with correct memory blocks.

        Validates:
        - Each agent has the expected memory blocks
        - Memory blocks contain the configured initial values
        - Block labels match configuration

        This is critical for agent functionality as memory blocks define
        agent behavior and knowledge.
        """
        # Test router agent memory blocks
        router_info = await agent_service.get_agent_info(AgentType.ROUTER)
        router_labels = {block.label for block in router_info.memory_blocks}

        expected_router_labels = {block["label"] for block in AGENT_CONFIGS[AgentType.ROUTER]["memory_blocks"]}
        assert router_labels == expected_router_labels, \
            f"Router memory blocks mismatch. Expected: {expected_router_labels}, Got: {router_labels}"

        # Test specialized analyst memory blocks
        specialist_info = await agent_service.get_agent_info(AgentType.SPECIALIZED_ANALYST)
        specialist_labels = {block.label for block in specialist_info.memory_blocks}

        expected_specialist_labels = {
            block["label"] for block in AGENT_CONFIGS[AgentType.SPECIALIZED_ANALYST]["memory_blocks"]
        }
        assert specialist_labels == expected_specialist_labels, \
            f"Specialist memory blocks mismatch. Expected: {expected_specialist_labels}, Got: {specialist_labels}"

        # Test generalist analyst memory blocks
        generalist_info = await agent_service.get_agent_info(AgentType.GENERALIST_ANALYST)
        generalist_labels = {block.label for block in generalist_info.memory_blocks}

        expected_generalist_labels = {
            block["label"] for block in AGENT_CONFIGS[AgentType.GENERALIST_ANALYST]["memory_blocks"]
        }
        assert generalist_labels == expected_generalist_labels, \
            f"Generalist memory blocks mismatch. Expected: {expected_generalist_labels}, Got: {generalist_labels}"

    async def test_idempotent_initialization(self, skip_if_no_api_key):
        """
        Test that calling initialize() multiple times is safe.

        Validates:
        - Multiple calls don't create duplicate agents
        - Service remains functional after multiple initializations
        - Agent IDs remain consistent

        This is important for service restart scenarios.
        """
        service = AgentService(letta_api_key=TEST_LETTA_API_KEY)

        # Initialize once
        await service.initialize()
        first_agent_ids = service._agent_ids.copy()

        # Initialize again
        await service.initialize()
        second_agent_ids = service._agent_ids.copy()

        # Agent IDs should remain the same (no duplicates created)
        assert first_agent_ids == second_agent_ids

        # Cleanup
        await service._cleanup_agents()


class TestRoutingLogic:
    """
    Tests for routing agent decision-making.

    These tests verify that the routing agent correctly identifies
    which analyst should handle different types of requests.
    """

    async def test_route_financial_query_to_specialist(self, agent_service):
        """
        Test that financial queries are routed to the specialized analyst.

        Validates:
        - Financial/quantitative queries go to SPECIALIZED_ANALYST
        - Routing reasoning is provided
        """
        financial_queries = [
            "Analyze the ROI of this investment opportunity",
            "What is the revenue growth trend for Q4?",
            "Calculate the net present value of this project",
            "Perform a financial statement analysis for Company X"
        ]

        for query in financial_queries:
            routing_decision = agent_service._router.route_request(
                user_query=query,
                user_id=TEST_USER_ID
            )

            assert routing_decision.target_agent_type == AgentType.SPECIALIZED_ANALYST, \
                f"Query '{query}' should route to SPECIALIZED_ANALYST, got {routing_decision.target_agent_type}"
            assert routing_decision.reasoning is not None
            assert len(routing_decision.reasoning) > 0

    async def test_route_general_query_to_generalist(self, agent_service):
        """
        Test that general queries are routed to the generalist analyst.

        Validates:
        - Non-specialized queries go to GENERALIST_ANALYST
        - Routing reasoning is provided
        """
        general_queries = [
            "What are the pros and cons of remote work?",
            "Analyze the impact of AI on job markets",
            "Compare different project management methodologies",
            "What factors should I consider when choosing a vendor?"
        ]

        for query in general_queries:
            routing_decision = agent_service._router.route_request(
                user_query=query,
                user_id=TEST_USER_ID
            )

            assert routing_decision.target_agent_type == AgentType.GENERALIST_ANALYST, \
                f"Query '{query}' should route to GENERALIST_ANALYST, got {routing_decision.target_agent_type}"
            assert routing_decision.reasoning is not None
            assert len(routing_decision.reasoning) > 0


class TestAnalystFunctionality:
    """
    Tests for analyst agent analysis capabilities.

    These tests verify that analyst agents can perform their core function:
    analyzing requests and providing meaningful responses.
    """

    async def test_specialized_analyst_performs_analysis(self, agent_service):
        """
        Test that specialized analyst can perform financial analysis.

        Validates:
        - Agent responds to financial queries
        - Response contains substantive content
        - Analysis completes without errors
        """
        query = "What are the key financial metrics for evaluating a startup?"
        result = agent_service._specialized_analyst.analyze(
            query=query,
            user_id=TEST_USER_ID
        )

        # Verify we got a response
        assert result is not None
        assert len(result) > 0
        assert result != "Analysis completed, but no textual result was generated."

        # Verify response contains analytical content
        # (Looking for keywords that indicate financial analysis)
        result_lower = result.lower()
        financial_keywords = ["metric", "financial", "revenue", "cash", "profit", "valuation"]
        assert any(keyword in result_lower for keyword in financial_keywords), \
            f"Analysis result should contain financial terminology: {result}"

    async def test_generalist_analyst_performs_analysis(self, agent_service):
        """
        Test that generalist analyst can perform general analysis.

        Validates:
        - Agent responds to general analytical queries
        - Response contains substantive content
        - Analysis completes without errors
        """
        query = "What are effective strategies for improving team collaboration?"
        result = agent_service._generalist_analyst.analyze(
            query=query,
            user_id=TEST_USER_ID
        )

        # Verify we got a response
        assert result is not None
        assert len(result) > 0
        assert result != "Analysis completed, but no textual result was generated."

        # Verify response is analytical (not just an echo)
        assert len(result) > len(query)  # Should be more than just repeating the question

    async def test_analyst_memory_state_accessible(self, agent_service):
        """
        Test that analyst memory state can be retrieved.

        Validates:
        - Memory blocks are accessible
        - Memory contains expected blocks
        - Memory values are non-empty

        This is important for monitoring and debugging agent behavior.
        """
        # Test specialized analyst memory
        specialist_memory = agent_service._specialized_analyst.get_memory_state()
        assert "persona" in specialist_memory
        assert "methodologies" in specialist_memory
        assert "domain_knowledge" in specialist_memory

        # Verify memory has content
        for block_label, block_value in specialist_memory.items():
            assert len(block_value) > 0, f"Memory block '{block_label}' should have content"

        # Test generalist analyst memory
        generalist_memory = agent_service._generalist_analyst.get_memory_state()
        assert "persona" in generalist_memory
        assert "analytical_approaches" in generalist_memory
        assert "learning_history" in generalist_memory

        # Verify memory has content
        for block_label, block_value in generalist_memory.items():
            assert len(block_value) > 0, f"Memory block '{block_label}' should have content"


class TestEndToEndFlow:
    """
    Tests for the complete end-to-end request flow.

    These tests validate the entire system working together:
    routing -> analysis -> response.
    """

    async def test_financial_analysis_request_e2e(self, agent_service):
        """
        Test complete flow for a financial analysis request.

        Validates:
        - Request is routed correctly
        - Analysis is performed
        - Response includes all expected fields
        - Processing completes without errors
        """
        request = AnalysisRequest(
            user_id=TEST_USER_ID,
            query="What financial metrics should I track for a SaaS business?",
            context={"business_type": "SaaS", "stage": "growth"}
        )

        response = await agent_service.process_analysis_request(request)

        # Verify response structure
        assert response.request_id is not None
        assert response.result is not None
        assert len(response.result) > 0

        # Verify routing
        assert response.routed_to == AgentType.SPECIALIZED_ANALYST
        assert response.routing_reasoning is not None

        # Verify metadata
        assert response.agent_id is not None
        assert response.processing_time_ms is not None
        assert response.processing_time_ms > 0

    async def test_general_analysis_request_e2e(self, agent_service):
        """
        Test complete flow for a general analysis request.

        Validates:
        - Request is routed correctly to generalist
        - Analysis is performed
        - Response is complete and valid
        """
        request = AnalysisRequest(
            user_id=TEST_USER_ID,
            query="What are best practices for conducting user research?",
            context=None
        )

        response = await agent_service.process_analysis_request(request)

        # Verify response structure
        assert response.request_id is not None
        assert response.result is not None
        assert len(response.result) > 0

        # Verify routing
        assert response.routed_to == AgentType.GENERALIST_ANALYST
        assert response.routing_reasoning is not None

        # Verify metadata
        assert response.agent_id is not None
        assert response.processing_time_ms is not None
        assert response.processing_time_ms > 0


class TestSystemStatus:
    """
    Tests for system status and health monitoring.

    These tests verify that the service can report its status correctly.
    """

    async def test_get_system_status_when_initialized(self, agent_service):
        """
        Test system status report when agents are initialized.

        Validates:
        - Status is "healthy"
        - All agents are listed
        - Letta connection is reported as active
        - No errors are present
        """
        status = await agent_service.get_system_status()

        assert status.status == "healthy"
        assert status.letta_connected is True
        assert len(status.agents) == 3  # Router + 2 analysts
        assert status.errors is None or len(status.errors) == 0

        # Verify all agent types are present
        agent_types = {agent.agent_type for agent in status.agents}
        assert AgentType.ROUTER in agent_types
        assert AgentType.SPECIALIZED_ANALYST in agent_types
        assert AgentType.GENERALIST_ANALYST in agent_types

    async def test_get_system_status_when_uninitialized(self, skip_if_no_api_key):
        """
        Test system status report before initialization.

        Validates:
        - Status reflects uninitialized state
        - Appropriate error message is provided
        """
        service = AgentService(letta_api_key=TEST_LETTA_API_KEY)
        # Don't call initialize()

        status = await service.get_system_status()

        assert status.status == "uninitialized"
        assert len(status.agents) == 0
        assert status.errors is not None
        assert len(status.errors) > 0
        assert "not yet initialized" in status.errors[0].lower()


class TestErrorHandling:
    """
    Tests for error handling and edge cases.

    These tests verify the system behaves correctly in error scenarios.
    """

    async def test_process_request_before_initialization(self, skip_if_no_api_key):
        """
        Test that processing requests before initialization auto-initializes.

        Validates:
        - Service auto-initializes on first request
        - Request is processed successfully
        - Service becomes initialized
        """
        service = AgentService(letta_api_key=TEST_LETTA_API_KEY)
        # Don't call initialize() explicitly

        request = AnalysisRequest(
            user_id=TEST_USER_ID,
            query="Test query"
        )

        # This should trigger auto-initialization
        response = await service.process_analysis_request(request)

        # Verify service became initialized
        assert service._initialized is True

        # Verify request was processed
        assert response.result is not None

        # Cleanup
        await service._cleanup_agents()

    async def test_service_creation_without_api_key(self):
        """
        Test that service creation fails gracefully without API key.

        Validates:
        - Clear error message when API key is missing
        - Error is raised during initialization
        """
        # Clear environment variable temporarily
        original_key = os.environ.get("LETTA_API_KEY")
        if "LETTA_API_KEY" in os.environ:
            del os.environ["LETTA_API_KEY"]

        try:
            # Should raise ValueError
            with pytest.raises(ValueError, match="Letta API key not provided"):
                service = AgentService()  # No API key in env or parameter

        finally:
            # Restore environment variable
            if original_key:
                os.environ["LETTA_API_KEY"] = original_key


# Test execution notes:
# - These tests require LETTA_API_KEY to be set
# - Tests will create and delete real Letta agents
# - Tests may take 30-60 seconds to run due to API calls
# - Tests are safe to run multiple times (cleanup is automatic)
#
# Run with: pytest tests/test_agents.py -v
# Run specific test: pytest tests/test_agents.py::TestRoutingLogic::test_route_financial_query_to_specialist -v
# Skip slow tests: pytest tests/test_agents.py -m "not slow" (if markers are added)
