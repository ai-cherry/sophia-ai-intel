#!/usr/bin/env python3
"""
Agno-Sophia Bridge - Connects Agno UI to your Sophia swarms
Run this to use Agno UI with your existing Sophia infrastructure
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional
import httpx
import asyncio
import json

app = FastAPI(title="Agno-Sophia Bridge")

# Your existing Sophia services
SOPHIA_SUPREME = "http://localhost:8300"
DIRECT_SWARM = "http://localhost:8200"
UNIFIED_SWARM = "http://localhost:8100"

class AgnoMessage(BaseModel):
    messages: List[Dict]
    mode: Optional[str] = None

@app.post("/api/chat")
async def agno_chat(body: AgnoMessage):
    """
    Agno UI compatible endpoint that routes to your Sophia services
    """
    # Extract user message
    user_messages = [m["content"] for m in body.messages if m["role"] == "user"]
    user_text = " ".join(user_messages)
    
    # Route to Sophia Supreme
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Try Sophia Supreme first
            response = await client.post(
                f"{SOPHIA_SUPREME}/chat",
                json={"message": user_text}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Format for Agno UI
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": data.get("response", "Processing...")
                        }
                    }],
                    "metadata": {
                        "orchestrator": data.get("orchestrator", "Sophia"),
                        "actions": data.get("actions_taken", [])
                    }
                }
        except:
            pass
        
        # Fallback to Direct Swarm
        try:
            response = await client.post(
                f"{DIRECT_SWARM}/chat",
                json={"message": user_text}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": data.get("response", "Processing...")
                        }
                    }]
                }
        except:
            pass
    
    # Default response
    return {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": f"Processing: {user_text}"
            }
        }]
    }

@app.get("/healthz")
def health():
    return {"status": "healthy", "bridge": "agno-sophia"}

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("AGNO-SOPHIA BRIDGE")
    print("Connecting Agno UI to your Sophia swarms")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8400)