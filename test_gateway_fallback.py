#!/usr/bin/env python3
"""Test script to verify smart router falls back correctly when gateway is not available."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from axiom.config import settings
from axiom.engine.intelligence import IntelligenceEngine
from axiom.engine.smart_router import SmartRouter

def test_gateway_fallback():
    print('Testing Smart Router Gateway Fallback Behavior')
    print('=' * 50)

    # Temporarily disable gateway by changing environment
    old_use_gateway = os.environ.get('AXIOM_USE_GATEWAY_FOR_INTELLIGENCE')
    old_base_url = os.environ.get('GATEWAY_API_BASE_URL')
    old_api_key = os.environ.get('GATEWAY_API_KEY')
    old_model = os.environ.get('GATEWAY_MODEL')

    try:
        # Disable gateway
        os.environ['AXIOM_USE_GATEWAY_FOR_INTELLIGENCE'] = 'false'

        print('Testing with GATEWAY DISABLED:')
        print(f'use_gateway_for_intelligence: {settings.use_gateway_for_intelligence}')
        print()

        # Create intelligence engine
        engine = IntelligenceEngine()

        # Get the smart router
        router = engine.router

        # Check what providers are registered
        providers = router.get_available_providers()
        print(f'Number of providers registered: {len(providers)}')

        gateway_providers = [p for p in providers if p['name'] == 'external-gateway']
        print(f'Gateway providers found: {len(gateway_providers)}')
        print()

        # Test routing for general tasks
        print('Testing task routing for GENERAL category (gateway disabled):')
        print('-' * 60)

        general_task = "Hello, how are you today?"
        route_info = router.get_route_for_task(general_task)

        print(f'Task: "{general_task}"')
        print(f'Category: {route_info["task_category"]}')
        print(f'Selected provider: {route_info["selected_provider"]}')

        # Should NOT be gateway since it's disabled
        if route_info["selected_provider"] != "external-gateway":
            print('* Gateway correctly NOT selected when disabled')
            print(f'  Selected provider: {route_info["selected_provider"]} (expected NVIDIA provider)')
        else:
            print('x Gateway incorrectly selected when disabled')

        print()

    finally:
        # Restore environment
        if old_use_gateway is not None:
            os.environ['AXIOM_USE_GATEWAY_FOR_INTELLIGENCE'] = old_use_gateway
        else:
            os.environ.pop('AXIOM_USE_GATEWAY_FOR_INTELLIGENCE', None)

        if old_base_url is not None:
            os.environ['GATEWAY_API_BASE_URL'] = old_base_url
        else:
            os.environ.pop('GATEWAY_API_BASE_URL', None)

        if old_api_key is not None:
            os.environ['GATEWAY_API_KEY'] = old_api_key
        else:
            os.environ.pop('GATEWAY_API_KEY', None)

        if old_model is not None:
            os.environ['GATEWAY_MODEL'] = old_model
        else:
            os.environ.pop('GATEWAY_MODEL', None)

    # Test with gateway enabled again
    print('Testing with GATEWAY ENABLED (after restore):')
    print(f'use_gateway_for_intelligence: {settings.use_gateway_for_intelligence}')
    print()

    # Create intelligence engine
    engine = IntelligenceEngine()

    # Get the smart router
    router = engine.router

    # Check what providers are registered
    providers = router.get_available_providers()
    print(f'Number of providers registered: {len(providers)}')

    gateway_providers = [p for p in providers if p['name'] == 'external-gateway']
    print(f'Gateway providers found: {len(gateway_providers)}')
    if gateway_providers:
        print(f'Gateway available: {gateway_providers[0]["available"]}')
    print()

    # Test routing for general tasks
    print('Testing task routing for GENERAL category (gateway enabled):')
    print('-' * 60)

    general_task = "Hello, how are you today?"
    route_info = router.get_route_for_task(general_task)

    print(f'Task: "{general_task}"')
    print(f'Category: {route_info["task_category"]}')
    print(f'Selected provider: {route_info["selected_provider"]}')

    # Should be gateway since it's enabled
    if route_info["selected_provider"] == "external-gateway":
        print('* Gateway correctly selected when enabled')
    else:
        print('x Gateway NOT selected when enabled')
        print(f'  Selected provider: {route_info["selected_provider"]}')

if __name__ == '__main__':
    test_gateway_fallback()