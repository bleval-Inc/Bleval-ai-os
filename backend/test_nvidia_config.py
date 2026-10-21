#!/usr/bin/env python3
"""Test NVIDIA provider configuration"""

import sys
import os

# Add the backend directory to the path so we can import axiom modules
backend_path = os.path.join(os.path.dirname(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

try:
    from axiom.engine.providers.nvidia import create_nvidia_providers
    from axiom.engine.intelligence import IntelligenceEngine
    from axiom.engine.memory import MemoryEngine
    from axiom.engine.tool import ToolEngine

    print("=== NVIDIA PROVIDER CONFIGURATION ===")
    providers = create_nvidia_providers()
    print(f"Found {len(providers)} configured NVIDIA providers:")
    for i, p in enumerate(providers, 1):
        print(f"  {i}. {p.label}")
        print(f     Model: {p.model_id}")
        print(f     Provider: {p.provider_name}")
        print(f     Role: {p.role}")
        print(f     Available: {p.available}")
        print(f     API Key Configured: {bool(p._config.api_key)}")
        print()

    print("=== INTELLIGENCE ENGINE STATUS ===")
    engine = IntelligenceEngine(
        memory=MemoryEngine(),
        tool=ToolEngine()
    )

    print(f"Has real provider: {engine.has_real_provider}")

    providers_info = engine.list_providers()
    print(f"Available providers in intelligence engine:")
    for provider in providers_info:
        status = "[AVAILABLE]" if provider.get("available") else "[UNAVAILABLE]"
        print(f"  {provider['name']}: {status}")
        if 'model' in provider:
            print(f"    Model: {provider['model']}")
        if 'role' in provider:
            print(f"    Role: {provider['role']}")

    print("\n=== TASK ROUTING EXAMPLES ===")
    test_cases = [
        ("Strategic planning for Q4", "jenson"),
        ("Write a Python function to process data", "coding-agent"),
        ("Analyze a large document", "analysis-agent"),
        ("Create marketing copy", "marketing-agent"),
        ("Simple question: What is 2+2?", "general-agent"),
    ]

    for task, agent in test_cases:
        route_info = engine.get_route_for_task(task, agent)
        print(f"\nTask: {task}")
        print(f"Agent: {agent}")
        print(f"Category: {route_info['task_category']}")
        print(f"Complexity: {route_info['complexity']}")
        print(f"Selected Provider: {route_info['selected_provider']}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()