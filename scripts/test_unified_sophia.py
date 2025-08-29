#!/usr/bin/env python3
import asyncio
import httpx

async def test_unified_chat():
    """Test the unified chat API"""
    
    tests = [
        {"message": "research quantum computing", "expected_intent": "research"},
        {"message": "deploy analysis agent", "expected_intent": "agents"},
        {"message": "generate API code", "expected_intent": "code"},
        {"message": "plan a new feature", "expected_intent": "planning"},
        {"message": "check service health", "expected_intent": "health"},
    ]
    
    print("🧪 TESTING UNIFIED CHAT API...")
    
    async with httpx.AsyncClient() as client:
        for test in tests:
            try:
                res = await client.post(
                    "http://localhost:3000/api/chat",
                    json={"message": test["message"]}
                )
                if res.status_code == 200:
                    data = res.json()
                    intent = data.get("metadata", {}).get("intent")
                    if intent == test["expected_intent"]:
                        print(f"✅ '{test['message']}' → {intent}")
                    else:
                        print(f"❌ '{test['message']}' → {intent} (expected {test['expected_intent']})")
                else:
                    print(f"❌ '{test['message']}' → HTTP {res.status_code}")
            except Exception as e:
                print(f"❌ '{test['message']}' → Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_unified_chat())
