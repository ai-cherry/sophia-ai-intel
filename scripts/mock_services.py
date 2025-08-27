import asyncio
import time
from typing import Dict, Any

class MockServiceProxy:
    """Provides mock implementations for Sophia AI microservices."""

    async def mock_slack_post(self, payload: Dict) -> Dict:
        """Mocks Slack post functionality."""
        await asyncio.sleep(0.1)  # Simulate network latency
        return {
            "test": "slack_post",
            "service": "comms-mcp",
            "status": "green",
            "response_time": 100,
            "error": None,
            "details": {"success": True, "message": "Mock Slack post successful."}
        }

    async def mock_crm_task_create(self, payload: Dict) -> Dict:
        """Mocks CRM task creation functionality."""
        await asyncio.sleep(0.15)  # Simulate network latency
        return {
            "test": "crm_task",
            "service": "crm-mcp",
            "status": "green",
            "response_time": 150,
            "error": None,
            "details": {"success": True, "id": "mock-task-12345", "message": "Mock CRM task created."}
        }

    async def mock_neon_select(self, payload: Dict) -> Dict:
        """Mocks Neon database connectivity."""
        await asyncio.sleep(0.08)  # Simulate network latency
        return {
            "test": "neon_select",
            "service": "analytics-mcp",
            "status": "green",
            "response_time": 80,
            "error": None,
            "details": {"success": True, "rows": [{"test_value": 1, "test_time": "2025-08-27T12:00:00Z"}], "message": "Mock Neon query successful."}
        }
