import httpx
import asyncio

async def test_mem0():
    """Example usage of Mem0 service"""
    base_url = "http://localhost:8009"
    headers = {
        "x-tenant-id": "test-tenant",
        "x-actor-id": "test-actor"
    }
    
    async with httpx.AsyncClient() as client:
        # Store a memory
        response = await client.post(
            f"{base_url}/memory/store",
            json={
                "content": "User prefers dark mode interfaces",
                "metadata": {"category": "preferences"},
                "ttl": 3600
            },
            headers=headers
        )
        print(f"Stored memory: {response.json()}")
        
        # Search memories
        response = await client.post(
            f"{base_url}/memory/search",
            json={"query": "dark mode", "limit": 5},
            headers=headers
        )
        print(f"Search results: {response.json()}")
        
        # Get recent memories
        response = await client.get(
            f"{base_url}/memory/recent?limit=5",
            headers=headers
        )
        print(f"Recent memories: {response.json()}")

if __name__ == "__main__":
    asyncio.run(test_mem0())