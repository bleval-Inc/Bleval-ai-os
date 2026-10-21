#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from axiom.config import settings
from axiom.engine.intelligence import IntelligenceEngine

def test_gateway_disabled():
    print('Testing Smart Router with GATEWAY DISABLED')
    print('=' * 50)

    # Temporarily override the environment variable
    os.environ['AXIOM_USE_GATEWAY_FOR_INTELLIGENCE'] = 'false'
    # Reload settings? Since settings uses @property, we just need to recreate the engine
    # because the settings instance is global but its properties read from os.getenv each time.
    # So we can just create a new engine and it will read the updated env var.

    # Create intelligence engine
    engine = IntelligenceEngine()

    # Get the smart router
    router = engine.router

    # Check gateway settings
    print(f'use_gateway_for_intelligence: {settings.use_gateway_for_intelligence}')
    print(f'GATEWAY_API_BASE_URL: {os.getenv("GATEWAY_API_BASE_URL", "Not set")}')
    print()

    # Get providers
    providers = router.get_available_providers()
    print(f'Number of providers registered: {len(providers)}')
    gateway_available = False
    for provider in providers:
        if provider['name'] == 'external-gateway':
            print(f'  Gateway provider available: {provider["available"]}')
            gateway_available = provider['available']
            break

    print()

    # Test routing for general tasks
    print('Testing task routing for GENERAL category (gateway disabled):')
    print('-' * 60)
    general_task = "Hello, how are you today?"
    route_info = router.get_route_for_task(general_task)
    print(f'Task: "{general_task}"')
    print(f'Category: {route_info["task_category"]}')
    print(f'Selected provider: {route_info["selected_provider"]}')

    if gateway_available:
        # Gateway is available but should not be selected because disabled
        if route_info["selected_provider"] != "external-gateway":
            print('* Gateway correctly NOT selected for GENERAL tasks when disabled')
        else:
            print('x Gateway incorrectly selected for GENERAL tasks when disabled')
    else:
        print('! Gateway not available (should not happen)')

    print()

    # Ensure it falls back to an NVIDIA provider
    selected = route_info["selected_provider"]
    if selected.startswith("nvidia-"):
        print(f'* Selected provider is NVIDIA: {selected}')
    else:
        print(f'x Selected provider is not NVIDIA: {selected}')

if __name__ == '__main__':
    test_gateway_disabled()