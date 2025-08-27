#!/usr/bin/env python3
"""
Sophia AI Gong MCP Service
==========================

Gong integration for revenue intelligence and sales conversation analytics.
Provides access to call recordings, transcripts, and sales insights.
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException, Header, Query
from pydantic import BaseModel

# Import shared platform libraries
from platform.common.service_base import create_app, ServiceConfig
from platform.auth.jwt import validate_token
from platform.common.errors import ServiceError, ValidationError, ok, err, raise_http_error
from platform.common.audit import log_tool_invocation, cleanup_connection_pool

# Configure logging
logger = logging.getLogger(__name__)

# Service configuration using ServiceConfig
SERVICE_CONFIG = ServiceConfig(
    name="gong-mcp",
    version="1.0.0",  # This should ideally come from a package version
    description="Gong integration for revenue intelligence and sales conversation analytics."
)

# Pydantic models for request/response validation
class SummarizeCallRequest(BaseModel):
    summary_type: str = "executive"  # executive, detailed, action_items
    include_transcript: bool = False
    focus_areas: Optional[List[str]] = None  # e.g., ["pricing", "objections", "next_steps"]

# Startup and shutdown handlers
# These will be passed to ServiceConfig
async def startup_event():
    """Initialize resources on startup"""
    logger.info(f"{SERVICE_CONFIG.name} starting...")

async def shutdown_event():
    """Clean up resources on shutdown"""
    await cleanup_connection_pool()
    logger.info(f"{SERVICE_CONFIG.name} shutting down")

# Create FastAPI app using the shared service base
app = create_app(
    config=ServiceConfig(
        name=SERVICE_CONFIG.name,
        version=SERVICE_CONFIG.version,
        description=SERVICE_CONFIG.description,
        startup_event=startup_event,
        shutdown_event=shutdown_event
    )
)

# Service-specific endpoints

def validate_provider_token(x_provider_token: Optional[str] = Header(None, alias="X-Provider-Token")):
    """Validate provider token from header"""
    if not x_provider_token:
        raise_http_error("Missing provider token", status_code=401, code="MISSING_TOKEN")
    # In production, validate the token with the provider
    # For now, just check it's not empty
    if len(x_provider_token.strip()) == 0:
        raise_http_error("Invalid provider token", status_code=401, code="INVALID_TOKEN")
    return x_provider_token

@app.get("/calls/recent")
async def get_recent_calls(
    account_id: str = Query(..., description="Account ID to get recent calls for"),
    window: int = Query(24, description="Time window in hours (default: 24)"),
    x_provider_token: str = Header(..., alias="X-Provider-Token")
):
    """Get recent Gong calls"""
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

        # Placeholder for Gong integration
        # In production, this would call the actual Gong API
        recent_calls = [
            {
                "id": "call_001",
                "title": "Q3 Planning Discussion with Enterprise Client",
                "duration": 2100,  # seconds
                "participants": ["john.doe", "jane.smith", "client.ceo"],
                "sentiment": "positive",
                "score": 85,
                "recording_url": "https://gong.io/recording/001",
                "transcript_available": True,
                "started_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                "account_id": account_id,
                "deal_amount": 150000,
                "stage": "proposal",
                "topics": ["pricing", "timeline", "implementation", "support"]
            },
            {
                "id": "call_002",
                "title": "Product Demo and Feature Review",
                "duration": 1800,
                "participants": ["sales.rep", "client.manager", "product.specialist"],
                "sentiment": "neutral",
                "score": 72,
                "recording_url": "https://gong.io/recording/002",
                "transcript_available": True,
                "started_at": (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat(),
                "account_id": account_id,
                "deal_amount": 75000,
                "stage": "demo",
                "topics": ["features", "integration", "pricing", "roi"]
            },
            {
                "id": "call_003",
                "title": "Contract Negotiation and Terms Discussion",
                "duration": 2700,
                "participants": ["senior.sales", "client.cfo", "legal.team"],
                "sentiment": "positive",
                "score": 88,
                "recording_url": "https://gong.io/recording/003",
                "transcript_available": True,
                "started_at": (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat(),
                "account_id": account_id,
                "deal_amount": 300000,
                "stage": "negotiation",
                "topics": ["contract", "terms", "payment", "timeline", "support"]
            }
        ]

        # Filter calls within the time window
        recent_calls_filtered = [
            call for call in recent_calls
            if datetime.fromisoformat(call["started_at"]) >= since_time
        ]

        logger.info(f"Retrieved {len(recent_calls_filtered)} recent calls for account {account_id} in last {window} hours")

        return ok({
            "calls": recent_calls_filtered,
            "count": len(recent_calls_filtered),
            "account_id": account_id,
            "window_hours": window,
            "since": since_time.isoformat(),
            "message": f"Retrieved {len(recent_calls_filtered)} recent calls"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recent calls: {e}")
        raise_http_error(f"Failed to get recent calls: {str(e)}", status_code=500, code="RETRIEVE_FAILED")

@app.post("/calls/{call_id}/summarize")
async def summarize_call(
    call_id: str,
    x_provider_token: str = Header(...),
    x_tenant_id: str = Header(...),
    x_actor_id: str = Header(...),
    x_purpose: str = Header(default="call_summary")
):
    """Summarize a Gong call transcript using Portkey LLM"""
    
    try:
        # First, get the call transcript from Gong
        headers = {"Authorization": f"Bearer {x_provider_token}"}
        
        async with httpx.AsyncClient() as client:
            # Get call details
            gong_response = await client.get(
                f"https://api.gong.io/v2/calls/{call_id}",
                headers=headers
            )
            
            if gong_response.status_code != 200:
                raise HTTPException(
                    status_code=gong_response.status_code,
                    detail="Failed to fetch call from Gong"
                )
            
            call_data = gong_response.json()
            
            # Get transcript
            transcript_response = await client.get(
                f"https://api.gong.io/v2/calls/{call_id}/transcript",
                headers=headers
            )
            
            if transcript_response.status_code != 200:
                raise HTTPException(
                    status_code=transcript_response.status_code,
                    detail="Failed to fetch transcript from Gong"
                )
            
            transcript_data = transcript_response.json()
            
            # Format transcript for summarization
            transcript_text = "\n".join([
                f"{segment['speaker']}: {segment['text']}"
                for segment in transcript_data.get("transcript", [])
            ])
            
            # Call Portkey LLM service for summarization
            portkey_url = os.getenv("PORTKEY_LLM_URL", "http://portkey-llm:8000")
            
            summary_response = await client.post(
                f"{portkey_url}/summarize",
                headers={
                    "x-tenant-id": x_tenant_id,
                    "x-actor-id": x_actor_id
                },
                json={
                    "content": transcript_text,
                    "max_tokens": 800,
                    "model": "gpt-4"
                }
            )
            
            if summary_response.status_code != 200:
                raise HTTPException(
                    status_code=summary_response.status_code,
                    detail="Failed to generate summary"
                )
            
            summary_data = summary_response.json()
            
            # Log to audit
            await log_tool_invocation(
                ctx={
                    "tenant": x_tenant_id,
                    "actor": x_actor_id,
                    "purpose": x_purpose
                },
                service="gong-mcp",
                tool="summarize_call",
                request={"call_id": call_id},
                response={"summary": summary_data["summary"][:200] + "..."},
                provider="gong",
                resource_ref=f"call:{call_id}"
            )
            
            return {
                "call_id": call_id,
                "call_title": call_data.get("title"),
                "duration": call_data.get("duration"),
                "summary": summary_data["summary"],
                "model_used": summary_data["model_used"],
                "token_count": summary_data["token_count"]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to summarize call: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to summarize call: {str(e)}"
        )
