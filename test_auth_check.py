#!/usr/bin/env python3
"""Test script to check ToolEngine authorization."""

import asyncio
import sys
import os

# Add the backend directory to the path so we can import axiom modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from axiom.engine.tool import ToolEngine

async def test_tool_authorization():
    """Test ToolEngine authorization with different agent IDs."""
    print("Testing ToolEngine authorization...")

    # Create a tool engine instance
    tool_engine = ToolEngine()

    # Test with non-existent agent
    print("\n1. Testing with non-existent agent 'axiom':")
    try:
        result = await tool_engine.execute_tool(
            agent_id="axiom",
            tool_id="web_search",
            action="search",
            params={"query": "test query", "max_results": 10}
        )
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Exception: {e}")

    # Test with existing agent that should have research capabilities
    print("\n2. Testing with existing agent 'atlas' (has lead-research):")
    try:
        result = await tool_engine.execute_tool(
            agent_id="atlas",
            tool_id="web_search",
            action="search",
            params={"query": "test query", "max_results": 10}
        )
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Exception: {e}")

    # Test with jenson (executive)
    print("\n3. Testing with existing agent 'jenson' (executive):")
    try:
        result = await tool_engine.execute_tool(
            agent_id="jenson",
            tool_id="web_search",
            action="search",
            params={"query": "test query", "max_results": 10}
        )
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Exception: {e}")

if __name__ == "__main__":
    try:
        result = asyncio.run(test_tool_authorization())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n>>> Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)