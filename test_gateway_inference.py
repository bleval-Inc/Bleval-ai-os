#!/usr/bin/env python3
"""Verify real gateway inference through the AXIOM Intelligence Engine."""

import asyncio
import os
import sys
from typing import Any

# Ensure the AXIOM backend package can be imported when this script is run
# from the repository root.
BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from axiom.config import settings
from axiom.engine.intelligence import IntelligenceEngine


UNIQUE_TOKEN = "AXIOM_LIVE_GATEWAY_TEST_12345"
PREFERRED_PROVIDER = "external-gateway"
TIMEOUT_SECONDS = 150


async def test_gateway_inference() -> bool:
    """Run a real inference request and validate the generated response."""

    print("Testing Real Gateway Inference with Unique Test Token")
    print("=" * 55)

    gateway_enabled = bool(settings.use_gateway_for_intelligence)
    print(f"use_gateway_for_intelligence: {gateway_enabled}")
    print(f"Preferred provider: {PREFERRED_PROVIDER}")
    print(f"Expected token: {UNIQUE_TOKEN}")
    print()

    if not gateway_enabled:
        print("FAIL: Gateway inference is disabled in AXIOM settings.")
        return False

    engine = IntelligenceEngine()
    test_prompt = (
        f"Return exactly this token and nothing else: {UNIQUE_TOKEN}"
    )

    print(f'Sending prompt: "{test_prompt}"')

    try:
        result: Any = await asyncio.wait_for(
            engine.generate_raw(
                prompt=test_prompt,
                preferred_provider=PREFERRED_PROVIDER,
                max_tokens=64,
                temperature=0.0,
            ),
            timeout=TIMEOUT_SECONDS,
        )

        print("\nResponse:")
        print(result)

        if not isinstance(result, str):
            print(
                "\nFAIL: The engine returned an unexpected response type: "
                f"{type(result).__name__}"
            )
            return False

        if not result.strip():
            print("\nFAIL: The engine returned an empty response.")
            return False

        if result.startswith("[") and "Error]" in result:
            print("\nFAIL: The provider reported an inference error.")
            return False

        if UNIQUE_TOKEN not in result:
            print("\nFAIL: The expected token was not found.")
            print("The response does not satisfy the inference test.")
            return False

        print("\nPASS: The expected token was found in the response.")
        print(
            "NOTE: This validates the engine response, but provider "
            "telemetry or gateway logs are needed to independently "
            "confirm which upstream model handled the request."
        )
        return True

    except asyncio.TimeoutError:
        print(
            f"\nFAIL: Inference timed out after {TIMEOUT_SECONDS} seconds."
        )
        return False

    except Exception as exc:
        print(f"\nFAIL: {type(exc).__name__}: {exc}")
        return False


def main() -> int:
    """Run the asynchronous test and propagate its result to the shell."""

    try:
        success = asyncio.run(test_gateway_inference())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        return 130
    except Exception as exc:
        print(f"\nFAIL: Unexpected {type(exc).__name__}: {exc}")
        return 1

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
