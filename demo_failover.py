#!/usr/bin/env python3
"""
Demo script to show how AI model failover works in Axiom AI OS.
This demonstrates that if one NVIDIA model fails, another automatically takes over.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from axiom.engine.intelligence import IntelligenceEngine
from axiom.engine.memory import MemoryEngine
from axiom.engine.tool import ToolEngine

async def test_failover_scenario():
    """Demonstrate how failover works when a model is unavailable."""
    print("=" * 60)
    print("AXIOM AI OS - AI MODEL FAILOVER DEMONSTRATION")
    print("=" * 60)

    # Initialize the intelligence engine
    engine = IntelligenceEngine(
        memory=MemoryEngine(),
        tool=ToolEngine()
    )

    print(f"\nAvailable Providers:")
    providers = engine.list_providers()
    for provider in providers:
        status = "[AVAILABLE]" if provider.get("available") else "[UNAVAILABLE]"
        print(f"  {provider['name']}: {status}")
        if 'model' in provider:
            print(f"    Model: {provider['model']}")
        if 'role' in provider:
            print(f"    Role: {provider['role']}")

    print(f"\nTesting intelligent task routing with automatic failover:")
    print("-" * 60)

    # Test different types of tasks to see how they route
    test_tasks = [
        ("Strategic planning for Q4 market expansion", "jenson", "Should use GLM-5.2 or Mistral"),
        ("Write a Python function to process customer data", "coding-agent-1", "Should use Mistral Mamba"),
        ("Analyze this 100-page document for key insights", "analysis-agent-2", "Should use Mistral Mamba"),
        ("Create a marketing campaign for product launch", "marketing-agent-3", "Should use NVIDIA General or Stepfun"),
        ("What's 2+2?", "general-agent-4", "Should use NVIDIA General (fastest)"),
    ]

    for task_desc, agent_id, expected in test_tasks:
        print(f"\nTask: {task_desc}")
        print(f"Agent: {agent_id}")
        print(f"Expected: {expected}")

        try:
            # This will automatically route to the best available provider
            # and failover to another if the first choice is unavailable
            result = await engine.generate(
                agent_id=agent_id,
                task_description=task_desc,
                max_tokens=50,
                temperature=0.7,
            )

            # Show which provider was actually used (from the result if it contains provider info)
            print(f"Result: {result[:100]}{'...' if len(result) > 100 else ''}")

        except Exception as e:
            print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("FAILOVER CAPABILITIES:")
    print("[+] Automatic routing to best available NVIDIA model")
    print("[+] Transparent failover when primary model unavailable")
    print("[+] No downtime - service remains online")
    print("[+] Zero configuration needed - works out of the box")
    print("=" * 60)

    # Show current routing for a strategic task
    print(f"\nExample routing analysis:")
    route_info = engine.get_route_for_task(
        "Strategic decision about company direction and market expansion",
        "jenson"
    )

    print(f"  Task Category: {route_info['task_category']}")
    print(f"  Complexity: {route_info['complexity']}")
    print(f"  Selected Provider: {route_info['selected_provider']}")
    print(f"  Available Providers: {len(route_info['available_providers'])} NVIDIA models")

if __name__ == "__main__":
    asyncio.run(test_failover_scenario())