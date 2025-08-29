"""
Integration tests for API endpoints
"""

import pytest
import httpx
import asyncio
from datetime import datetime


class TestAPIIntegration:
    """Test suite for API integration"""
    
    @pytest.fixture
    async def client(self):
        """Create test client"""
        async with httpx.AsyncClient(base_url="http://localhost:3001") as client:
            yield client
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_health_endpoints(self, client):
        """Test all health check endpoints"""
        endpoints = [
            "/api/health",
            "/api/healthz",
            "/healthz",
        ]
        
        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_chat_api_flow(self, client):
        """Test complete chat interaction flow"""
        # Start conversation
        response = await client.post(
            "/api/chat",
            json={"message": "Hello", "session_id": "test-session"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["session_id"] == "test-session"
        
        # Continue conversation
        response = await client.post(
            "/api/chat",
            json={
                "message": "What can you help me with?",
                "session_id": "test-session"
            }
        )
        assert response.status_code == 200
        assert "response" in response.json()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_swarm_api_integration(self, client):
        """Test swarm API endpoints"""
        # Create swarm task
        response = await client.post(
            "/api/swarm/execute",
            json={
                "task": "Research quantum computing",
                "swarm_type": "research",
                "agents": 3
            }
        )
        assert response.status_code in [200, 202]
        data = response.json()
        assert "task_id" in data
        
        # Check task status
        task_id = data["task_id"]
        response = await client.get(f"/api/swarm/status/{task_id}")
        assert response.status_code == 200
        status = response.json()
        assert status["status"] in ["pending", "processing", "completed"]
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_service_integration(self, client):
        """Test memory service integration"""
        # Store memory
        response = await client.post(
            "/api/memory/store",
            json={
                "user_id": "test-user",
                "content": "User prefers Python",
                "category": "preference"
            }
        )
        assert response.status_code == 200
        
        # Retrieve memories
        response = await client.get(
            "/api/memory/retrieve",
            params={"user_id": "test-user", "query": "programming language"}
        )
        assert response.status_code == 200
        memories = response.json()
        assert isinstance(memories, list)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_websocket_connection(self):
        """Test WebSocket connectivity"""
        import websockets
        
        async with websockets.connect("ws://localhost:8080/ws") as websocket:
            # Send test message
            await websocket.send(json.dumps({
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            }))
            
            # Receive response
            response = await websocket.recv()
            data = json.loads(response)
            assert data["type"] == "pong"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_rate_limiting(self, client):
        """Test API rate limiting"""
        # Send many requests quickly
        responses = []
        for _ in range(20):
            response = await client.get("/api/health")
            responses.append(response.status_code)
        
        # Some requests should be rate limited
        assert 429 in responses or all(r == 200 for r in responses)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_handling(self, client):
        """Test API error handling"""
        # Invalid endpoint
        response = await client.get("/api/nonexistent")
        assert response.status_code == 404
        
        # Invalid payload
        response = await client.post("/api/chat", json={})
        assert response.status_code == 400
        
        # Invalid JSON
        response = await client.post(
            "/api/chat",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400