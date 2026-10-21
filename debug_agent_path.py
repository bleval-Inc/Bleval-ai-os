#!/usr/bin/env python3
"""Debug script to check agent path resolution."""

import sys
import os
from pathlib import Path

# Add the backend directory to the path so we can import axiom modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from axiom.config import agents_path

def test_agent_paths():
    """Test agent path resolution."""
    print("Testing agent path resolution...")

    # Get the agents base path
    base_path = agents_path()
    print(f"\nAgents base path: {base_path}")
    print(f"Base path exists: {base_path.exists()}")

    # Check for top-level axiom agent
    top_level_path = base_path / "axiom.yml"
    print(f"\nTop-level axiom.yml path: {top_level_path}")
    print(f"Top-level axiom.yml exists: {top_level_path.exists()}")

    # Check for nested agent in system organization
    nested_path = base_path / "system" / "axiom" / "agent.yml"
    print(f"\nNested axiom agent.yml path: {nested_path}")
    print(f"Nested axiom agent.yml exists: {nested_path.exists()}")

    # List what's in the agents directory
    print(f"\nContents of agents base path:")
    if base_path.exists():
        for item in base_path.iterdir():
            print(f"  {item.name} ({'dir' if item.is_dir() else 'file'})")

    # List what's in the system org directory
    system_org_path = base_path / "system"
    print(f"\nContents of system org path:")
    if system_org_path.exists():
        for item in system_org_path.iterdir():
            print(f"  {item.name} ({'dir' if item.is_dir() else 'file'})")

    # List what's in the axiom agent directory
    axiom_agent_path = base_path / "system" / "axiom"
    print(f"\nContents of axiom agent path:")
    if axiom_agent_path.exists():
        for item in axiom_agent_path.iterdir():
            print(f"  {item.name} ({'dir' if item.is_dir() else 'file'})")

if __name__ == "__main__":
    test_agent_paths()