#!/usr/bin/env python3
import asyncio
import aiohttp
import sys

async def test_axiom_route():
    BASE_URL = "http://localhost:8000/api/v1"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{BASE_URL}/axiom/route", json={
                "message": "Check system health"
            }) as resp:
                if resp.status >= 400:
                    text = await resp.text()
                    print(f"AXIOM route failed: {resp.status} - {text}")
                    return False
                result = await resp.json()
                if not result:
                    print("AXIOM route returned no result")
                    return False
                print(f"AXIOM route success: {str(result)[:200]}...")
                return True
        except Exception as e:
            print(f"Exception during AXIOM route: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_axiom_route())
    sys.exit(0 if success else 1)