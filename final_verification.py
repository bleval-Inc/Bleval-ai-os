#!/usr/bin/env python3
"""Final verification that the gateway is prioritized for general tasks."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from axiom.config import settings
from axiom.engine.intelligence import IntelligenceEngine

def main():
    print('=== Final Verification: Gateway Prioritization ===')
    print(f'use_gateway_for_intelligence: {settings.use_gateway_for_intelligence}')
    print()

    # Create intelligence engine
    engine = IntelligenceEngine()

    # Get the smart router
    router = engine.router

    # 1. Check that gateway is registered and available
    providers = router.get_available_providers()
    gateway_providers = [p for p in providers if p['name'] == 'external-gateway']

    if not gateway_providers:
        print('FAIL: Gateway provider not registered')
        return 1

    gateway = gateway_providers[0]
    if not gateway['available']:
        print('FAIL: Gateway provider not available')
        return 1

    print('PASS: Gateway provider is registered and available')
    print()

    # 2. Test that general tasks use gateway
    general_tasks = [
        "Hello, how are you?",
        "What's the weather like today?",
        "Tell me a joke.",
        "Explain the concept of gravity in simple terms.",
    ]

    print('Testing general tasks:')
    all_general_pass = True
    for task in general_tasks:
        route_info = router.get_route_for_task(task)
        if route_info['selected_provider'] != 'external-gateway':
            print(f'  FAIL: Task "{task}" -> {route_info["selected_provider"]} (expected external-gateway)')
            all_general_pass = False
        else:
            print(f'  PASS: Task "{task}" -> {route_info["selected_provider"]}')

    if not all_general_pass:
        print()
        return 1

    print()

    # 3. Test that non-general tasks do NOT use gateway (unless gateway is also the best NVIDIA option, but we prioritize NVIDIA for those)
    # We'll test a few samples from each category and expect they don't use gateway.
    # Note: Our change only affects GENERAL category, so other categories should be unchanged.
    non_general_tests = [
        ("What is the strategic vision for our company?", "STRATEGIC"),
        ("Write a Python function to sort a list", "CODING"),
        ("Analyze this 100-page document for key insights", "LONG_CONTEXT"),
        ("Create a workflow to automate customer onboarding", "AGENTIC"),
        ("Write a marketing copy for our new product", "CREATIVE"),
        ("Review the quarterly sales performance data", "ANALYSIS"),
    ]

    print('Testing non-general tasks (should NOT use gateway):')
    all_non_general_pass = True
    for task_desc, expected_category in non_general_tests:
        route_info = router.get_route_for_task(task_desc)
        selected = route_info['selected_provider']
        category = route_info['task_category']

        # Check category matches (case-insensitive because we get the value)
        if category != expected_category.lower():
            print(f'  WARNING: Task "{task_desc}" -> category {category} (expected {expected_category.lower()})')

        # Check that gateway is NOT selected
        if selected == 'external-gateway':
            print(f'  FAIL: Task "{task_desc}" incorrectly selected gateway')
            all_non_general_pass = False
        else:
            print(f'  PASS: Task "{task_desc}" -> {selected} (no gateway)')

    if not all_non_general_pass:
        print()
        return 1

    print()
    print('=== ALL TESTS PASSED ===')
    print('The gateway is correctly prioritized for general tasks.')
    return 0

if __name__ == '__main__':
    sys.exit(main())