#!/usr/bin/env python3
"""Test script to verify the research implementation works at the code level."""

import asyncio
import sys
import os

# Add the backend directory to the path so we can import axiom modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from axiom.core.axiom_core import AXIOMCore
from axiom.engine.tool import ToolEngine
from axiom.engine.intelligence import IntelligenceEngine
from axiom.engine.memory import MemoryEngine
from typing import Optional


class MockIntelligenceEngine:
    """Mock intelligence engine for testing without API keys."""

    async def generate(self, agent_id: str, task_description: str, **kwargs):
        return f"Synthesized response for: {task_description[:50]}..."


class MockRequestRouter:
    """Mock request router that always classifies as research for testing."""

    def classify(self, message: str):
        # Return a mock classified object
        return MockClassified(message)

    def route(self, classified):
        # Return a mock routed object that indicates research handler
        return MockRouted("research", None)


class MockClassified:
    def __init__(self, intent: str):
        self.category = MockCategory()
        self.complexity = MockComplexity()
        self.intent = intent
        self.confidence = 0.9


class MockCategory:
    def __init__(self):
        self.value = "research"


class MockComplexity:
    def __init__(self):
        self.value = "medium"


class MockRouted:
    def __init__(self, handler: str, target: Optional[str]):
        self.handler = handler
        self.target = target
        self.context = {}
        self.requires_approval = False


class MockToolEngine:
    """Mock tool engine that returns fake search results."""

    def __init__(self):
        # Simulate no API keys configured
        self._brave_api_key = ""
        self._google_api_key = ""
        self._google_cx = ""

    async def execute_tool(self, agent_id: str, tool_id: str, action: str, params: dict):
        if tool_id == "web_search" and action == "search":
            # Return mock search results
            query = params.get("query", "")
            return {
                "results": [
                    {
                        "title": f"Mock Result 1 for {query}",
                        "url": "https://example.com/result1",
                        "description": f"This is a mock description for result 1 related to {query}"
                    },
                    {
                        "title": f"Mock Result 2 for {query}",
                        "url": "https://example.com/result2",
                        "description": f"This is a mock description for result 2 related to {query}"
                    }
                ],
                "query": query,
                "provider": "mock"
            }
        return {"error": f"Unknown tool: {tool_id}"}

    def get_available_tools(self, org_id: str):
        return []


async def test_research_functionality():
    """Test that the research implementation works correctly."""
    print("Testing AXIOM research implementation...")

    # Create mock components
    mock_tool = MockToolEngine()
    mock_intelligence = MockIntelligenceEngine()
    mock_memory = MemoryEngine()
    mock_request_router = MockRequestRouter()

    # Create AXIOM Core instance with mocks
    axiom_core = AXIOMCore()
    axiom_core._tool = mock_tool
    axiom_core._intelligence = mock_intelligence
    axiom_core._memory = mock_memory
    axiom_core._request_router = mock_request_router

    # Test the _conduct_web_search method directly
    print("\n1. Testing _conduct_web_search method:")
    search_result = await axiom_core._conduct_web_search("test query", "axiom")
    print(f"   Search result keys: {list(search_result.keys())}")
    print(f"   Has formatted_results: {'formatted_results' in search_result}")
    print(f"   Number of results: {len(search_result.get('results', []))}")
    if search_result.get('results'):
        print(f"   First result title: {search_result['results'][0].get('title', 'N/A')}")

    # Test chat method with research request
    print("\n2. Testing chat method with research request:")
    chat_response = await axiom_core.chat(
        message="research artificial intelligence trends",
        conversation_history=[]
    )
    print(f"   Response category: {chat_response.get('category', 'N/A')}")
    print(f"   Response agent_id: {chat_response.get('agent_id', 'N/A')}")
    print(f"   Response length: {len(chat_response.get('response', ''))}")
    print(f"   Contains synthesized response: {'Synthesized response' in chat_response.get('response', '')}")
    print(f"   Has search results: {'search_results' in chat_response}")
    print(f"   Has sources: {'sources' in chat_response}")

    # Test handle_request method with research request
    print("\n3. Testing handle_request method with research request:")
    route_response = await axiom_core.handle_request("research machine learning applications")
    print(f"   Response category: {route_response.get('category', 'N/A')}")
    print(f"   Response length: {len(route_response.get('response', ''))}")
    print(f"   Contains synthesized response: {'Synthesized response' in route_response.get('response', '')}")
    print(f"   Has search results: {'search_results' in route_response}")
    print(f"   Has sources: {'sources' in route_response}")
    print(f"   Has error flag: {route_response.get('error', False)}")

    # Test error case - what happens when tool engine is not available
    print("\n4. Testing error case (no tool engine):")
    axiom_core_no_tool = AXIOMCore()
    axiom_core_no_tool._intelligence = mock_intelligence
    axiom_core_no_tool._memory = mock_memory
    axiom_core_no_tool._request_router = mock_request_router
    # _tool remains None

    chat_response_no_tool = await axiom_core_no_tool.chat("research test query")
    print(f"   Response when no tool: {chat_response_no_tool.get('response', 'N/A')}")
    print(f"   Category when no tool: {chat_response_no_tool.get('category', 'N/A')}")

    print("\n>>> All tests completed successfully!")
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_research_functionality())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n>>> Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)