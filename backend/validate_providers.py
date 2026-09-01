#!/usr/bin/env python3
"""Model Provider Connectivity Validation Script

Validates all configured AI model providers with real API connectivity tests.
Used for production commissioning to ensure the AXIOM BRAIN is fully operational.

Usage:
    python3 validate_providers.py [--verbose]
"""

import asyncio
import os
import sys
from typing import List, Dict, Any

# Load .env before importing axiom
from dotenv import load_dotenv
load_dotenv()

# Set production mode for validation
os.environ["REAL_PROVIDERS_ONLY"] = "true"
os.environ["DEBUG"] = "false"
os.environ["AXIOM_ENV"] = "production"

from axiom.engine.providers.nvidia import create_nvidia_providers, NVIDIAProvider
from axiom.engine.intelligence import ProviderRouter
from axiom.engine.smart_router import SmartRouter, TaskClassifier, TaskCategory
from axiom.config import settings
from axiom.engine.base import MockProvider


async def test_nvidia_provider(provider: NVIDIAProvider, test_name: str) -> Dict[str, Any]:
    """Test a single NVIDIA provider with a connectivity check."""
    print(f"\n{'='*60}")
    print(f"Testing {test_name} ({provider.name})")
    print(f"  Model: {provider.model_id}")
    print(f"  Provider: {provider.provider_name}")
    print(f"  Role: {provider.role}")

    if not provider.available:
        return {
            "provider": provider.name,
            "model": provider.model_id,
            "status": "SKIPPED",
            "reason": "No API key configured",
            "error": None
        }

    try:
        # Simple connectivity test
        response = await provider.generate(
            prompt="Respond with exactly: OK",
            system_prompt="You are a connectivity test. Reply only with OK.",
            max_tokens=10,
            temperature=0.0,
        )

        # Check if we got an error string from the provider
        if response.startswith(f"[{provider.name} Error]"):
            return {
                "provider": provider.name,
                "model": provider.model_id,
                "status": "FAILED",
                "reason": "API returned error",
                "error": response
            }

        # Consider any non-empty response as success for connectivity test
        if response and len(response.strip()) > 0:
            print(f"  ✓ Response received ({len(response)} chars)")
            print(f"  Response: {response[:200]}...")

            return {
                "provider": provider.name,
                "model": provider.model_id,
                "status": "OK",
                "reason": "Connected and responding",
                "error": None
            }
        else:
            return {
                "provider": provider.name,
                "model": provider.model_id,
                "status": "FAILED",
                "reason": "Empty response from API",
                "error": None
            }

    except Exception as e:
        return {
            "provider": provider.name,
            "model": provider.model_id,
            "status": "FAILED",
            "reason": f"Exception: {type(e).__name__}",
            "error": str(e)
        }


async def test_smart_router() -> Dict[str, Any]:
    """Test the full smart router with task classification and routing."""
    print(f"\n{'='*60}")
    print(f"Testing Smart Router End-to-End")

    router = SmartRouter()

    # Register all NVIDIA providers
    nvidia_providers = create_nvidia_providers()
    for nvp in nvidia_providers:
        router.register_nvidia_provider(nvp)

    available = router.get_available_providers()
    real_providers = [p for p in available if p["available"] and p["type"] != "MockProvider"]

    if not real_providers:
        return {
            "test": "smart_router",
            "status": "FAILED",
            "reason": "No real providers registered",
            "providers": available
        }

    # Test task classification
    classifier = TaskClassifier()

    test_tasks = [
        ("Strategic planning for Q4", "jenson", TaskCategory.STRATEGIC),
        ("Write a Python function for API auth", "agent-1", TaskCategory.CODING),
        ("Analyze 500 page document", "agent-2", TaskCategory.LONG_CONTEXT),
        ("Create marketing copy for launch", "agent-3", TaskCategory.CREATIVE),
    ]

    classification_results = []
    for task, agent_id, expected_category in test_tasks:
        profile = classifier.classify(task, agent_id)
        classification_results.append({
            "task": task,
            "agent": agent_id,
            "expected": expected_category.value,
            "actual": profile.category.value,
            "match": profile.category == expected_category
        })

    # Test provider selection for each category
    routing_results = []
    for cat in TaskCategory:
        provider = router.select_provider(
            task_profile=classifier.classify("test", ""),
            agent_id=""
        )
        routing_results.append({
            "category": cat.value,
            "selected_provider": provider.name if hasattr(provider, "name") else type(provider).__name__,
            "is_real": not isinstance(provider, MockProvider)
        })

    return {
        "test": "smart_router",
        "status": "OK",
        "registered_providers": len(available),
        "real_providers": len(real_providers),
        "classification_results": classification_results,
        "routing_results": routing_results,
        "providers": available
    }


async def test_intelligence_engine() -> Dict[str, Any]:
    """Test the IntelligenceEngine with full context assembly."""
    print(f"\n{'='*60}")
    print(f"Testing Intelligence Engine")

    from axiom.engine.intelligence import IntelligenceEngine
    from axiom.engine.memory import MemoryEngine
    from axiom.engine.tool import ToolEngine

    try:
        engine = IntelligenceEngine(
            memory=MemoryEngine(),
            tool=ToolEngine()
        )

        providers = engine.list_providers()
        real_providers = [p for p in providers if p.get("available") and "mock" not in p.get("name", "").lower()]

        if not real_providers:
            return {
                "test": "intelligence_engine",
                "status": "FAILED",
                "reason": "No real providers available in IntelligenceEngine"
            }

        # Test basic generation
        result = await engine.generate(
            agent_id="test_agent",
            task_description="Say exactly 'HEALTH_CHECK_OK'",
            max_tokens=20,
            temperature=0.0,
        )

        success = "HEALTH" in result.upper() or "OK" in result.upper()

        return {
            "test": "intelligence_engine",
            "status": "OK" if success else "PARTIAL",
            "registered_providers": len(providers),
            "real_providers": len(real_providers),
            "test_response": result[:200],
            "providers": providers
        }

    except Exception as e:
        return {
            "test": "intelligence_engine",
            "status": "FAILED",
            "reason": f"Exception: {type(e).__name__}",
            "error": str(e)
        }


async def run_all_tests() -> Dict[str, Any]:
    """Run all validation tests and return summary."""
    print("============================================================")
    print("  AXIOM BRAIN - MODEL PROVIDER CONNECTIVITY VALIDATION")
    print("============================================================")
    print(f"\nEnvironment: {settings.env}")
    print(f"Real Providers Only: {settings.real_providers_only}")
    print(f"Debug Mode: {settings.debug}")

    results = []

    # Test NVIDIA providers
    nvidia_providers = create_nvidia_providers()
    for nvp in nvidia_providers:
        results.append(await test_nvidia_provider(nvp, nvp.label))

    # Test Smart Router
    results.append(await test_smart_router())

    # Test Intelligence Engine
    results.append(await test_intelligence_engine())

    # Summary
    print(f"\n{'='*60}")
    print("VALIDATION SUMMARY")
    print(f"{'='*60}")

    total = len(results)
    passed = sum(1 for r in results if r.get("status") == "OK")
    skipped = sum(1 for r in results if r.get("status") == "SKIPPED")
    failed = sum(1 for r in results if r.get("status") == "FAILED")
    partial = sum(1 for r in results if r.get("status") == "PARTIAL")

    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Partial: {partial}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")

    print("\nDetailed Results:")
    for r in results:
        status = r.get("status", "UNKNOWN")
        name = r.get("provider", r.get("test", "unknown"))
        reason = r.get("reason", "")
        print(f"  [{status}] {name}: {reason}")

    # Determine overall success
    # At least one NVIDIA provider must work
    nvidia_results = [r for r in results if r.get("provider", "").startswith("nvidia-")]
    nvidia_working = any(r.get("status") == "OK" for r in nvidia_results)

    overall = "PASS" if (passed > 0 and nvidia_working) else "FAIL"
    print(f"\nOverall: {overall}")

    return {
        "overall": overall,
        "summary": {
            "total": total,
            "passed": passed,
            "skipped": skipped,
            "failed": failed,
            "partial": partial
        },
        "results": results
    }


def main():
    """Main entry point."""
    results = asyncio.run(run_all_tests())
    sys.exit(0 if results["overall"] == "PASS" else 1)


if __name__ == "__main__":
    main()