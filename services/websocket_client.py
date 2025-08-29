"""
WebSocket Client for Agent Communication
"""

import asyncio
import httpx
import json
from typing import Dict, Optional, Callable
from datetime import datetime

class AgentWebSocketClient:
    """WebSocket client for agents to communicate in real-time"""
    
    def __init__(self, agent_id: str, hub_url: str = "http://localhost:8096"):
        self.agent_id = agent_id
        self.hub_url = hub_url
        self.connected = False
    
    async def send_message(self, message: Dict) -> bool:
        """Send message to all subscribers via REST API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.hub_url}/agent/{self.agent_id}/message",
                    json=message,
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Failed to send message: {e}")
            return False
    
    async def update_status(self, status: Dict) -> bool:
        """Update agent status"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.hub_url}/agent/{self.agent_id}/status",
                    json=status,
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Failed to update status: {e}")
            return False
    
    async def send_progress(self, task: str, progress: float, details: str = None):
        """Send progress update"""
        message = {
            "type": "progress",
            "task": task,
            "progress": progress,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_message(message)
    
    async def send_result(self, task: str, result: Dict):
        """Send task result"""
        message = {
            "type": "result",
            "task": task,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_message(message)
    
    async def send_error(self, task: str, error: str):
        """Send error message"""
        message = {
            "type": "error",
            "task": task,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_message(message)
    
    async def send_log(self, level: str, message: str):
        """Send log message"""
        log_message = {
            "type": "log",
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_message(log_message)

class SwarmWebSocketReporter:
    """Reports swarm execution progress via WebSocket"""
    
    def __init__(self, swarm_id: str, hub_url: str = "http://localhost:8096"):
        self.client = AgentWebSocketClient(f"swarm-{swarm_id}", hub_url)
        self.swarm_id = swarm_id
        self.start_time = None
    
    async def start_execution(self, task: str, swarm_type: str):
        """Report execution start"""
        self.start_time = datetime.now()
        await self.client.update_status({
            "state": "executing",
            "task": task,
            "swarm_type": swarm_type,
            "start_time": self.start_time.isoformat()
        })
        await self.client.send_log("info", f"Starting {swarm_type} swarm for: {task}")
    
    async def report_step(self, step: str, progress: float):
        """Report execution step"""
        await self.client.send_progress(step, progress, f"Executing: {step}")
    
    async def report_finding(self, finding: Dict):
        """Report intermediate finding"""
        await self.client.send_message({
            "type": "finding",
            "data": finding,
            "timestamp": datetime.now().isoformat()
        })
    
    async def complete_execution(self, result: Dict):
        """Report execution completion"""
        duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        await self.client.update_status({
            "state": "completed",
            "duration": duration,
            "completion_time": datetime.now().isoformat()
        })
        
        await self.client.send_result(
            f"Swarm execution {self.swarm_id}",
            {
                **result,
                "execution_time": duration
            }
        )
    
    async def report_error(self, error: str):
        """Report execution error"""
        await self.client.update_status({
            "state": "error",
            "error": error,
            "error_time": datetime.now().isoformat()
        })
        await self.client.send_error(f"Swarm execution {self.swarm_id}", error)

# Example usage for testing
async def test_websocket_client():
    """Test the WebSocket client"""
    agent = AgentWebSocketClient("test-agent-001")
    
    # Update status
    await agent.update_status({
        "state": "active",
        "task": "Testing WebSocket communication"
    })
    
    # Send progress updates
    for i in range(0, 101, 20):
        await agent.send_progress("Test task", i/100, f"Progress: {i}%")
        await asyncio.sleep(1)
    
    # Send result
    await agent.send_result("Test task", {
        "status": "success",
        "data": "Test completed successfully"
    })

if __name__ == "__main__":
    asyncio.run(test_websocket_client())