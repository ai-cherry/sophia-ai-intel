#!/usr/bin/env python3
"""
Sophia AI Communications MCP Service
====================================

Communications and messaging integration for Sophia AI platform.
Provides access to email, chat, notifications, and communication channels.
"""

import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

# Import shared platform libraries
try:
    from platform.auth.jwt import validate_token
    from platform.common.errors import ServiceError, ValidationError, ok, err, raise_http_error
    from platform.common.audit import log_tool_invocation, cleanup_connection_pool
except ImportError:
    # Fallback for development
    validate_token = None
    ServiceError = Exception
    ValidationError = Exception
    def ok(data=None):
        return {"status": "ok", "data": data}
    def err(message, code="ERROR", status_code=400, details=None):
        return {"status": "error", "error": {"code": code, "message": message, "details": details or {}}}
    def raise_http_error(message, status_code=400, code="HTTP_ERROR"):
        from fastapi import HTTPException
        raise HTTPException(status_code=status_code, detail=err(message, code, status_code))
    # Mock audit functions for development
    async def log_tool_invocation(*args, **kwargs):
        return None
    async def cleanup_connection_pool():
        pass

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Environment configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
SERVICE_NAME = "Sophia AI Communications MCP"
SERVICE_DESCRIPTION = "Communications and messaging integration"
SERVICE_VERSION = "1.0.0"

# Global readiness flag
_ready = False

app = FastAPI(
    title=SERVICE_NAME,
    description=SERVICE_DESCRIPTION,
    version=SERVICE_VERSION
)

# CORS middleware with configurable origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class PostMessageRequest(BaseModel):
    channel: str
    text: str
    thread_ts: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None

@app.on_event("startup")
async def startup_event():
    """Set readiness flag on startup"""
    global _ready
    _ready = True
    logger.info(f"{SERVICE_NAME} v{SERVICE_VERSION} started and ready")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    await cleanup_connection_pool()
    logger.info(f"{SERVICE_NAME} shutting down")

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/readyz")
async def readiness_check():
    """Readiness check endpoint"""
    if not _ready:
        raise HTTPException(status_code=503, detail="Service not ready")

    return {
        "status": "ready",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/stream")
async def stream_endpoint(request: Request):
    """SSE keep-alive endpoint"""

    async def event_generator():
        """Generate SSE events with keep-alive pings"""
        while True:
            if await request.is_disconnected():
                break

            # Send keep-alive ping every 25 seconds
            yield ": ping\n\n"
            await asyncio.sleep(25)

    return EventSourceResponse(event_generator())

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": SERVICE_DESCRIPTION,
        "status": "operational",
        "endpoints": {
            "health": "/healthz",
            "ready": "/readyz",
            "stream": "/stream",
            "docs": "/docs",
            "slack_post_message": "/slack/post_message",
            "slack_recent_mentions": "/slack/recent_mentions"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def validate_provider_token(x_provider_token: Optional[str] = Header(None, alias="X-Provider-Token")):
    """Validate provider token from header"""
    if not x_provider_token:
        raise_http_error("Missing provider token", status_code=401, code="MISSING_TOKEN")
    # In production, validate the token with the provider
    # For now, just check it's not empty
    if len(x_provider_token.strip()) == 0:
        raise_http_error("Invalid provider token", status_code=401, code="INVALID_TOKEN")
    return x_provider_token

@app.post("/slack/post_message")
async def post_slack_message(
    request: PostMessageRequest,
    x_provider_token: str = Header(..., alias="X-Provider-Token"),
    x_tenant_id: str = Header(None, alias="X-Tenant-Id"),
    x_actor_id: str = Header(None, alias="X-Actor-Id"),
    x_client_ip: str = Header(None, alias="X-Forwarded-For"),
    user_agent: str = Header(None)
):
    """Post message to Slack"""
    try:
        # Validate token
        validate_provider_token(x_provider_token)

        # Validate required fields
        if not request.channel:
            raise_http_error("Channel is required", status_code=400, code="MISSING_CHANNEL")

        if not request.text:
            raise_http_error("Message text is required", status_code=400, code="MISSING_TEXT")

        # Placeholder for Slack integration
        # In production, this would call the actual Slack API
        message_id = f"msg_{datetime.now().timestamp()}"
        posted_message = {
            "id": message_id,
            "channel": request.channel,
            "text": request.text,
            "thread_ts": request.thread_ts,
            "attachments": request.attachments or [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "posted_by": "sophia-ai-mcp"
        }

        logger.info(f"Posted Slack message to {request.channel}: {request.text[:50]}...")

        response_data = {
            "message": posted_message,
            "status": f"Message posted to Slack channel {request.channel} successfully"
        }

        # Log audit record for successful operation
        audit_ctx = {
            'tenant': x_tenant_id or 'default',
            'actor': x_actor_id or 'system',
            'purpose': 'slack_message_post'
        }
        
        await log_tool_invocation(
            ctx=audit_ctx,
            service='comms-mcp',
            tool='slack/post_message',
            request={
                'channel': request.channel,
                'text': request.text,
                'thread_ts': request.thread_ts,
                'attachments': request.attachments
            },
            response=response_data,
            provider='slack',
            resource_ref=message_id,
            ip=x_client_ip,
            user_agent=user_agent
        )

        return ok(response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to post Slack message: {e}")
        
        # Log audit record for failed operation
        if 'audit_ctx' in locals():
            await log_tool_invocation(
                ctx=audit_ctx,
                service='comms-mcp',
                tool='slack/post_message',
                request={
                    'channel': request.channel if 'request' in locals() else None,
                    'text': request.text if 'request' in locals() else None
                },
                error={
                    'code': 'POST_FAILED',
                    'message': str(e)
                },
                provider='slack',
                resource_ref=None,
                ip=x_client_ip if 'x_client_ip' in locals() else None,
                user_agent=user_agent if 'user_agent' in locals() else None
            )
        
        raise_http_error(f"Failed to post Slack message: {str(e)}", status_code=500, code="POST_FAILED")

@app.get("/slack/recent_mentions")
async def get_recent_mentions(
    account_id: str = Query(..., description="Account ID to get mentions for"),
    window: int = Query(24, description="Time window in hours (default: 24)"),
    x_provider_token: str = Header(..., alias="X-Provider-Token")
):
    """Get recent Slack mentions"""
    try:
        # Validate token
        validate_provider_token(x_provider_token)

        # Validate required fields
        if not account_id:
            raise_http_error("Account ID is required", status_code=400, code="MISSING_ACCOUNT_ID")

        if window <= 0 or window > 168:  # Max 1 week
            raise_http_error("Window must be between 1 and 168 hours", status_code=400, code="INVALID_WINDOW")

        # Calculate time window
        since_time = datetime.now(timezone.utc) - timedelta(hours=window)

        # Placeholder for Slack integration
        # In production, this would call the actual Slack API
        mentions = [
            {
                "id": "mention_001",
                "channel": "#general",
                "text": f"<@{account_id}> please review the latest changes",
                "user": "john.doe",
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                "thread_ts": None,
                "reactions": [{"name": "thumbsup", "count": 2}]
            },
            {
                "id": "mention_002",
                "channel": "#product-updates",
                "text": f"Hey <@{account_id}>, the new feature is ready for testing",
                "user": "jane.smith",
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat(),
                "thread_ts": "thread_123",
                "reactions": []
            },
            {
                "id": "mention_003",
                "channel": "#support",
                "text": f"<@{account_id}> can you help with this customer issue?",
                "user": "support.team",
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat(),
                "thread_ts": None,
                "reactions": [{"name": "eyes", "count": 1}]
            }
        ]

        # Filter mentions within the time window
        recent_mentions = [
            mention for mention in mentions
            if datetime.fromisoformat(mention["timestamp"]) >= since_time
        ]

        logger.info(f"Retrieved {len(recent_mentions)} recent mentions for account {account_id} in last {window} hours")

        return ok({
            "mentions": recent_mentions,
            "count": len(recent_mentions),
            "account_id": account_id,
            "window_hours": window,
            "since": since_time.isoformat(),
            "message": f"Retrieved {len(recent_mentions)} recent mentions"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recent mentions: {e}")
        raise_http_error(f"Failed to get recent mentions: {str(e)}", status_code=500, code="RETRIEVE_FAILED")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)