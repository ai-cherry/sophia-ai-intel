"""
WebSocket Hub - Real-time communication between agents and dashboard
"""

import asyncio
import json
import uuid
from typing import Dict, Set, List, Optional
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Sophia WebSocket Hub")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    """Manages WebSocket connections and message routing"""
    
    def __init__(self):
        # Active connections by client_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Agent subscriptions (agent_id -> Set of client_ids)
        self.agent_subscriptions: Dict[str, Set[str]] = {}
        # Client subscriptions (client_id -> Set of agent_ids)
        self.client_subscriptions: Dict[str, Set[str]] = {}
        # Message history for replay
        self.message_history: Dict[str, List[Dict]] = {}
        # Agent status tracking
        self.agent_status: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = set()
        
        # Send connection confirmation
        await self.send_personal_message({
            "type": "connection",
            "status": "connected",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }, client_id)
        
        print(f"✓ Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Clean up subscriptions
        if client_id in self.client_subscriptions:
            for agent_id in self.client_subscriptions[client_id]:
                if agent_id in self.agent_subscriptions:
                    self.agent_subscriptions[agent_id].discard(client_id)
            del self.client_subscriptions[client_id]
        
        print(f"✗ Client {client_id} disconnected")
    
    async def send_personal_message(self, message: Dict, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error sending to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast_to_agent_subscribers(self, agent_id: str, message: Dict):
        """Broadcast message to all clients subscribed to an agent"""
        if agent_id not in self.agent_subscriptions:
            self.agent_subscriptions[agent_id] = set()
        
        # Store in history
        if agent_id not in self.message_history:
            self.message_history[agent_id] = []
        self.message_history[agent_id].append(message)
        
        # Keep only last 100 messages per agent
        if len(self.message_history[agent_id]) > 100:
            self.message_history[agent_id] = self.message_history[agent_id][-100:]
        
        # Send to all subscribers
        for client_id in self.agent_subscriptions[agent_id].copy():
            await self.send_personal_message(message, client_id)
    
    async def subscribe_to_agent(self, client_id: str, agent_id: str):
        """Subscribe client to agent updates"""
        if agent_id not in self.agent_subscriptions:
            self.agent_subscriptions[agent_id] = set()
        
        self.agent_subscriptions[agent_id].add(client_id)
        self.client_subscriptions[client_id].add(agent_id)
        
        # Send subscription confirmation
        await self.send_personal_message({
            "type": "subscription",
            "action": "subscribed",
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat()
        }, client_id)
        
        # Send recent history if available
        if agent_id in self.message_history:
            recent = self.message_history[agent_id][-10:]  # Last 10 messages
            for msg in recent:
                await self.send_personal_message({
                    **msg,
                    "replay": True
                }, client_id)
        
        # Send current agent status if available
        if agent_id in self.agent_status:
            await self.send_personal_message({
                "type": "agent_status",
                "agent_id": agent_id,
                "status": self.agent_status[agent_id],
                "timestamp": datetime.now().isoformat()
            }, client_id)
    
    async def unsubscribe_from_agent(self, client_id: str, agent_id: str):
        """Unsubscribe client from agent updates"""
        if agent_id in self.agent_subscriptions:
            self.agent_subscriptions[agent_id].discard(client_id)
        
        if client_id in self.client_subscriptions:
            self.client_subscriptions[client_id].discard(agent_id)
        
        await self.send_personal_message({
            "type": "subscription",
            "action": "unsubscribed",
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat()
        }, client_id)
    
    async def update_agent_status(self, agent_id: str, status: Dict):
        """Update and broadcast agent status"""
        self.agent_status[agent_id] = {
            **status,
            "last_update": datetime.now().isoformat()
        }
        
        # Broadcast status update
        await self.broadcast_to_agent_subscribers(agent_id, {
            "type": "agent_status",
            "agent_id": agent_id,
            "status": self.agent_status[agent_id],
            "timestamp": datetime.now().isoformat()
        })

# Global connection manager
manager = ConnectionManager()

@app.get("/")
async def root():
    return {
        "service": "Sophia WebSocket Hub",
        "status": "active",
        "connections": len(manager.active_connections),
        "monitored_agents": len(manager.agent_status)
    }

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Main WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Handle different message types
            message_type = data.get("type")
            
            if message_type == "subscribe":
                agent_id = data.get("agent_id")
                if agent_id:
                    await manager.subscribe_to_agent(client_id, agent_id)
            
            elif message_type == "unsubscribe":
                agent_id = data.get("agent_id")
                if agent_id:
                    await manager.unsubscribe_from_agent(client_id, agent_id)
            
            elif message_type == "agent_message":
                # Agent sending update to subscribers
                agent_id = data.get("agent_id")
                if agent_id:
                    await manager.broadcast_to_agent_subscribers(agent_id, {
                        **data,
                        "timestamp": datetime.now().isoformat()
                    })
            
            elif message_type == "agent_status":
                # Update agent status
                agent_id = data.get("agent_id")
                status = data.get("status", {})
                if agent_id:
                    await manager.update_agent_status(agent_id, status)
            
            elif message_type == "ping":
                # Respond to ping
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, client_id)
            
            elif message_type == "broadcast":
                # Broadcast to all clients (admin function)
                for cid in manager.active_connections:
                    await manager.send_personal_message({
                        **data,
                        "broadcast": True,
                        "timestamp": datetime.now().isoformat()
                    }, cid)
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)

@app.post("/agent/{agent_id}/message")
async def send_agent_message(agent_id: str, message: Dict):
    """REST endpoint for agents to send messages to subscribers"""
    await manager.broadcast_to_agent_subscribers(agent_id, {
        **message,
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat(),
        "source": "rest_api"
    })
    
    return {
        "status": "sent",
        "agent_id": agent_id,
        "subscribers": len(manager.agent_subscriptions.get(agent_id, set()))
    }

@app.post("/agent/{agent_id}/status")
async def update_agent_status(agent_id: str, status: Dict):
    """REST endpoint to update agent status"""
    await manager.update_agent_status(agent_id, status)
    
    return {
        "status": "updated",
        "agent_id": agent_id,
        "current_status": manager.agent_status.get(agent_id)
    }

@app.get("/agents")
async def list_agents():
    """List all monitored agents and their status"""
    return {
        "agents": [
            {
                "agent_id": agent_id,
                "status": status,
                "subscribers": len(manager.agent_subscriptions.get(agent_id, set()))
            }
            for agent_id, status in manager.agent_status.items()
        ]
    }

@app.get("/connections")
async def list_connections():
    """List all active WebSocket connections"""
    return {
        "connections": [
            {
                "client_id": client_id,
                "subscriptions": list(manager.client_subscriptions.get(client_id, set()))
            }
            for client_id in manager.active_connections
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8096)