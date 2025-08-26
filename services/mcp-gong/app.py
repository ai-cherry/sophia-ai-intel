#!/usr/bin/env python3
"""
Gong MCP Service - Revenue Intelligence Integration
==================================================

Gong integration for Sophia AI platform.
Provides access to call recordings, transcripts, and sales intelligence.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

import aiohttp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Environment configuration
GONG_ACCESS_TOKEN = os.getenv("GONG_ACCESS_TOKEN", "")
GONG_ACCESS_KEY = os.getenv("GONG_ACCESS_KEY", "")
TENANT = os.getenv("TENANT", "pay-ready")

app = FastAPI(
    title="Sophia AI Gong MCP Service",
    description="Revenue intelligence and call analytics integration",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GongClient:
    def __init__(self, access_key: str, access_token: str):
        self.access_key = access_key
        self.access_token = access_token
        self.base_url = "https://api.gong.io/v2"
        self.connected = bool(access_key and access_token)

    async def get_calls(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get calls from Gong"""
        if not self.connected:
            return []

        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            try:
                async with session.get(f"{self.base_url}/calls",
                                     headers=headers,
                                     params={"limit": limit}) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("calls", [])
                    else:
                        logger.error(f"Gong calls API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Gong calls request failed: {e}")
                return []

    async def get_transcripts(self, call_id: str) -> Dict[str, Any]:
        """Get transcript for a specific call"""
        if not self.connected:
            return {}

        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            try:
                async with session.get(f"{self.base_url}/calls/{call_id}/transcript",
                                     headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Gong transcript API error: {response.status}")
                        return {}
            except Exception as e:
                logger.error(f"Gong transcript request failed: {e}")
                return {}

gong_client = GongClient(GONG_ACCESS_KEY, GONG_ACCESS_TOKEN)

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    gong_status = "connected" if (GONG_ACCESS_KEY and GONG_ACCESS_TOKEN) else "no_credentials"

    if GONG_ACCESS_KEY and GONG_ACCESS_TOKEN:
        try:
            calls = await gong_client.get_calls(1)
            gong_status = f"connected ({len(calls)} calls accessible)"
        except Exception as e:
            gong_status = f"error: {str(e)[:50]}"

    return {
        "status": "healthy",
        "gong_connection": gong_status,
        "tenant": TENANT,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/")
async def root():
    return {
        "service": "Sophia AI Gong MCP",
        "version": "2.0.0",
        "status": "operational",
        "gong_configured": bool(GONG_ACCESS_KEY and GONG_ACCESS_TOKEN),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/calls")
async def get_calls(limit: int = 50):
    """Get Gong calls"""
    try:
        calls = await gong_client.get_calls(limit)
        return {
            "calls": calls,
            "count": len(calls),
            "tenant": TENANT,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calls/{call_id}/transcript")
async def get_call_transcript(call_id: str):
    """Get transcript for a specific call"""
    try:
        transcript = await gong_client.get_transcripts(call_id)
        return {
            "call_id": call_id,
            "transcript": transcript,
            "tenant": TENANT,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics")
async def get_analytics():
    """Get sales analytics from call data"""
    try:
        calls = await gong_client.get_calls(100)

        # Analyze call patterns
        analytics = {
            "total_calls": len(calls),
            "call_types": {},
            "sentiment_trends": {},
            "key_topics": []
        }

        for call in calls:
            call_type = call.get("type", "unknown")
            if call_type not in analytics["call_types"]:
                analytics["call_types"][call_type] = 0
            analytics["call_types"][call_type] += 1

        return {
            "analytics": analytics,
            "tenant": TENANT,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)