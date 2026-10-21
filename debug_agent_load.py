#!/usr/bin/env python3
"""Debug script to check agent loading."""

import sys
import os

# Add the backend directory to the path so we can import axiom modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from axiom.registry.agent import AgentRegistryLoader

def test_agent_loading():
    """Test agent loading."""
    print("Testing agent loading...")

    # Create an agent loader instance
    agent_loader = AgentRegistryLoader()

    # Try to load the axiom agent
    print("\n1. Trying to load agent 'axiom':")
    try:
        detail = agent_loader.load_detail("axiom")
        if detail is None:
            print("   Agent detail is None (agent not found)")
        else:
            print(f"   Agent detail loaded: {detail}")
            print(f"   Agent ID: {detail.id}")
            print(f"   Agent permissions: {detail.permissions}")
            if hasattr(detail.permissions, 'can'):
                print(f"   Can permissions: {detail.permissions.can}")
            if hasattr(detail.permissions, 'cannot'):
                print(f"   Cannot permissions: {detail.permissions.cannot}")
    except Exception as e:
        print(f"   Exception loading agent: {e}")
        import traceback
        traceback.print_exc()

    # Try to load the atlas agent for comparison
    print("\n2. Trying to load agent 'atlas':")
    try:
        detail = agent_loader.load_detail("atlas")
        if detail is None:
            print("   Agent detail is None (agent not found)")
        else:
            print(f"   Agent detail loaded: {detail}")
            print(f"   Agent ID: {detail.id}")
            print(f"   Agent permissions: {detail.permissions}")
            if hasattr(detail.permissions, 'can'):
                print(f"   Can permissions: {detail.permissions.can}")
            if hasattr(detail.permissions, 'cannot'):
                print(f"   Cannot permissions: {detail.permissions.cannot}")
    except Exception as e:
        print(f"   Exception loading agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent_loading()