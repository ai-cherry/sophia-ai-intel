#!/usr/bin/env python3
"""
Slack MCP Service - Communication Integration
============================================

Slack integration for Sophia AI platform.
Provides access to channels, messages, and team communication data.
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
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")
TENANT = os.getenv("TENANT", "pay-ready")

app = FastAPI(
    title="Sophia AI Slack MCP Service",
    description="Team communication and collaboration integration",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SlackClient:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = "https://slack.com/api"
        self.connected = bool(bot_token)

    async def get_channels(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get Slack channels"""
        if not self.connected:
            return []

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.bot_token}"}

            try:
                async with session.get(f"{self.base_url}/conversations.list",
                                     headers=headers,
                                     params={"limit": limit}) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("channels", [])
                    else:
                        logger.error(f"Slack channels API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Slack channels request failed: {e}")
                return []

    async def get_messages(self, channel_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get messages from a specific channel"""
        if not self.connected:
            return []

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.bot_token}"}

            try:
                async with session.get(f"{self.base_url}/conversations.history",
                                     headers=headers,
                                     params={"channel": channel_id, "limit": limit}) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("messages", [])
                    else:
                        logger.error(f"Slack messages API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Slack messages request failed: {e}")
                return []

slack_client = SlackClient(SLACK_BOT_TOKEN)

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    slack_status = "connected" if SLACK_BOT_TOKEN else "no_token"

    if SLACK_BOT_TOKEN:
        try:
            channels = await slack_client.get_channels(1)
            slack_status = f"connected ({len(channels)} channels accessible)"
        except Exception as e:
            slack_status = f"error: {str(e)[:50]}"

    return {
        "status": "healthy",
        "slack_connection": slack_status,
        "tenant": TENANT,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/")
async def root():
    return {
        "service": "Sophia AI Slack MCP",
        "version": "2.0.0",
        "status": "operational",
        "slack_configured": bool(SLACK_BOT_TOKEN),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/channels")
async def get_channels(limit: int = 50):
    """Get Slack channels"""
    try:
        channels = await slack_client.get_channels(limit)
        return {
            "channels": channels,
            "count": len(channels),
            "tenant": TENANT,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get channels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/channels/{channel_id}/messages")
async def get_channel_messages(channel_id: str, limit: int = 50):
    """Get messages from a specific channel"""
    try:
        messages = await slack_client.get_messages(channel_id, limit)
        return {
            "channel_id": channel_id,
            "messages": messages,
            "count": len(messages),
            "tenant": TENANT,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics")
async def get_analytics():
    """Get communication analytics from Slack data"""
    try:
        channels = await slack_client.get_channels(100)

        # Analyze communication patterns
        analytics = {
            "total_channels": len(channels),
            "channel_types": {},
            "active_channels": 0,
            "public_channels": 0,
            "private_channels": 0
        }

        for channel in channels:
            channel_type = "public" if channel.get("is_channel", True) else "private"
            analytics["channel_types"][channel_type] = analytics["channel_types"].get(channel_type, 0) + 1

            if channel_type == "public":
                analytics["public_channels"] += 1
            else:
                analytics["private_channels"] += 1

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