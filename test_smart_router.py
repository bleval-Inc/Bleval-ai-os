#!/usr/bin/env python3
"""Test script to verify smart router prioritizes gateway for general tasks."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from axiom.config import settings
from axiom.engine.intelligence import IntelligenceEngine
from axiom.engine.smart_router import SmartRouter
from axiom.engine.providers.external import ExternalAPIProvider

def test_gateway_prioritization():
    print('Testing Smart Router Gateway Prioritization')
    print('=' * 50)

    # Check gateway settings
    print(f'use_gateway_for_intelligence: {settings.use_gateway_for_intelligence}')
    print(f'GATEWAY_API_BASE_URL: {os.getenv("GATEWAY_API_BASE_URL", "Not set")}')
    print(f'GATEWAY_API_KEY: {"Set" if os.getenv("GATEWAY_API_KEY") else "Not set"}')
    print(f'GATEWAY_MODEL: {os.getenv("GATEWAY_MODEL", "Not set")}')
    print()

    # Create intelligence engine
    engine = IntelligenceEngine()

    # Get the smart router
    router = engine.router

    # Check what providers are registered
    providers = router.get_available_providers()
    print(f'Number of providers registered: {len(providers)}')

    for i, provider in enumerate(providers):
        print(f'  {i+1}. {provider["name"]} (available: {provider["available"]})')

    print()

    # Check if gateway provider is registered
    gateway_providers = [p for p in providers if p['name'] == 'external-gateway']
    if gateway_providers:
        provider = gateway_providers[0]
        print(f'* Gateway provider found: {provider["name"]}')
        print(f'  Available: {provider["available"]}')
    else:
        print('x Gateway provider NOT found')
        return

    print()

    # Test routing for general tasks
    print('Testing task routing for GENERAL category:')
    print('-' * 40)

    # Test a simple general task
    general_task = "Hello, how are you today?"
    route_info = router.get_route_for_task(general_task)

    print(f'Task: "{general_task}"')
    print(f'Category: {route_info["task_category"]}')
    print(f'Selected provider: {route_info["selected_provider"]}')

    # Check if gateway is selected for general task
    if route_info["selected_provider"] == "external-gateway":
        print('* Gateway is correctly prioritized for GENERAL tasks')
    else:
        print('x Gateway is NOT prioritized for GENERAL tasks')
        print(f'  Selected provider: {route_info["selected_provider"]}')

    print()

    # Test routing for other categories to ensure we didn't break them
    print('Testing task routing for other categories:')
    print('-' * 40)

    test_cases = [
        ("What is the strategic vision for our company?", "STRATEGIC"),
        ("Write a Python function to sort a list", "CODING"),
        ("Analyze this 100-page document for key insights", "LONG_CONTEXT"),
        ("Create a workflow to automate customer onboarding", "AGENTIC"),
        ("Write a marketing copy for our new product", "CREATIVE"),
        ("Review the quarterly sales performance data", "ANALYSIS"),
    ]

    for task_desc, expected_category in test_cases:
        route_info = router.get_route_for_task(task_desc)
        selected = route_info["selected_provider"]
        category = route_info["task_category"]

        # For non-general tasks, gateway should NOT be selected (unless it's also the best NVIDIA option)
        # But we mainly want to ensure we didn't break the routing
        status = "*" if category == expected_category else "x"
        print(f'{status} {category}: {selected}')

        if category != expected_category:
            print(f'  Expected: {expected_category}, Got: {category}')

if __name__ == '__main__':
    test_gateway_prioritization()