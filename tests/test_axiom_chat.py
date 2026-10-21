#!/usr/bin/env python3
import asyncio
import aiohttp
import sys

async def test_axiom_chat():
    BASE_URL = "http://localhost:8000/api/v1"
    async with aiohttp.ClientSession() as session:
        # Test AXIOM chat
        try:
            async with session.post(f"{BASE_URL}/axiom/chat", json={
                "message": "Hello, system status check",
                "conversation_history": [],
            }) as resp:
                if resp.status >= 400:
                    text = await resp.text()
                    print(f"AXIOM chat failed: {resp.status} - {text}")
                    return False
                result = await resp.json()
                if not result.get("response"):
                    print("AXIOM chat returned no response")
                    return False
                print(f"AXIOM chat success: {result.get('response')[:100]}...")
                return True
        except Exception as e:
            print(f"Exception during AXIOM chat: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_axiom_chat())
    sys.exit(0 if success else 1)