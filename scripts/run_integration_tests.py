#!/usr/bin/env python3
"""Run Axiom AI OS integration tests with proper configuration."""

import asyncio
import subprocess
import sys
from pathlib import Path


async def run_tests():
    """Run the integration test suite."""

    project_root = Path(__file__).parent.parent

    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("Installing pytest...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"], check=True)

    # Check dependencies
    dependencies = [
        "psutil",
        "pydantic",
        "aiohttp",
        "pyyaml",
    ]
    for dep in dependencies:
        try:
            __import__(dep)
        except ImportError:
            print(f"Installing {dep}...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)

    # Run tests
    test_file = project_root / "tests" / "test_integration_full.py"
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "-v",
        "--asyncio-mode=auto",
        "--tb=short",
        "-x",  # Stop on first failure
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode


if __name__ == "__main__":
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)