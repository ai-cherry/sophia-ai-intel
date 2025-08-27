#!/usr/bin/env python3
"""
Sophia AI CRM MCP Service
=========================

Customer Relationship Management integration for Sophia AI platform.
Provides access to customer data, sales opportunities, and relationship management.
"""

import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Header
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
SERVICE_NAME = "Sophia AI CRM MCP"
SERVICE_DESCRIPTION = "Customer Relationship Management integration"
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
class UpdateStageRequest(BaseModel):
    stage: str
    probability: Optional[float] = None
    notes: Optional[str] = None

class CreateTaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = "medium"

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
            "opportunity_update_stage": "/opportunity/update_stage",
            "task_create": "/task/create",
            "opportunity_live": "/opportunity/{id}/live"
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

@app.post("/opportunity/update_stage")
async def update_opportunity_stage(
    opportunity_id: str,
    request: UpdateStageRequest,
    x_provider_token: str = Header(..., alias="X-Provider-Token"),
    x_tenant_id: str = Header(None, alias="X-Tenant-Id"),
    x_actor_id: str = Header(None, alias="X-Actor-Id"),
    x_client_ip: str = Header(None, alias="X-Forwarded-For"),
    user_agent: str = Header(None)
):
    """Update opportunity stage"""
    try:
        # Validate token
        validate_provider_token(x_provider_token)

        # Validate required fields
        if not opportunity_id:
            raise_http_error("Opportunity ID is required", status_code=400, code="MISSING_OPPORTUNITY_ID")

        if not request.stage:
            raise_http_error("Stage is required", status_code=400, code="MISSING_STAGE")

        # Placeholder for CRM integration
        # In production, this would call the actual CRM API
        updated_opportunity = {
            "id": opportunity_id,
            "stage": request.stage,
            "probability": request.probability,
            "notes": request.notes,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": "sophia-ai-mcp"
        }

        logger.info(f"Updated opportunity {opportunity_id} stage to {request.stage}")

        response_data = {
            "opportunity": updated_opportunity,
            "message": f"Opportunity {opportunity_id} stage updated successfully"
        }

        # Log audit record for successful operation
        audit_ctx = {
            'tenant': x_tenant_id or 'default',
            'actor': x_actor_id or 'system',
            'purpose': 'opportunity_stage_update'
        }
        
        await log_tool_invocation(
            ctx=audit_ctx,
            service='crm-mcp',
            tool='opportunity/update_stage',
            request={
                'opportunity_id': opportunity_id,
                'stage': request.stage,
                'probability': request.probability,
                'notes': request.notes
            },
            response=response_data,
            provider='salesforce',
            resource_ref=opportunity_id,
            ip=x_client_ip,
            user_agent=user_agent
        )

        return ok(response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update opportunity stage: {e}")
        
        # Log audit record for failed operation
        if 'audit_ctx' in locals():
            await log_tool_invocation(
                ctx=audit_ctx,
                service='crm-mcp',
                tool='opportunity/update_stage',
                request={
                    'opportunity_id': opportunity_id,
                    'stage': request.stage if 'request' in locals() else None
                },
                error={
                    'code': 'UPDATE_FAILED',
                    'message': str(e)
                },
                provider='salesforce',
                resource_ref=opportunity_id,
                ip=x_client_ip if 'x_client_ip' in locals() else None,
                user_agent=user_agent if 'user_agent' in locals() else None
            )
        
        raise_http_error(f"Failed to update opportunity stage: {str(e)}", status_code=500, code="UPDATE_FAILED")

@app.post("/task/create")
async def create_task(
    request: CreateTaskRequest,
    x_provider_token: str = Header(..., alias="X-Provider-Token"),
    x_tenant_id: str = Header(None, alias="X-Tenant-Id"),
    x_actor_id: str = Header(None, alias="X-Actor-Id"),
    x_client_ip: str = Header(None, alias="X-Forwarded-For"),
    user_agent: str = Header(None)
):
    """Create new task"""
    try:
        # Validate token
        validate_provider_token(x_provider_token)

        # Validate required fields
        if not request.title:
            raise_http_error("Task title is required", status_code=400, code="MISSING_TITLE")

        # Placeholder for CRM integration
        # In production, this would call the actual CRM API
        task_id = f"task_{datetime.now().timestamp()}"
        created_task = {
            "id": task_id,
            "title": request.title,
            "description": request.description,
            "assignee": request.assignee,
            "due_date": request.due_date,
            "priority": request.priority,
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": "sophia-ai-mcp"
        }

        logger.info(f"Created task {task_id}: {request.title}")

        response_data = {
            "task": created_task,
            "message": f"Task '{request.title}' created successfully"
        }

        # Log audit record for successful operation
        audit_ctx = {
            'tenant': x_tenant_id or 'default',
            'actor': x_actor_id or 'system',
            'purpose': 'task_creation'
        }
        
        await log_tool_invocation(
            ctx=audit_ctx,
            service='crm-mcp',
            tool='task/create',
            request={
                'title': request.title,
                'description': request.description,
                'assignee': request.assignee,
                'due_date': request.due_date,
                'priority': request.priority
            },
            response=response_data,
            provider='salesforce',
            resource_ref=task_id,
            ip=x_client_ip,
            user_agent=user_agent
        )

        return ok(response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        
        # Log audit record for failed operation
        if 'audit_ctx' in locals():
            await log_tool_invocation(
                ctx=audit_ctx,
                service='crm-mcp',
                tool='task/create',
                request={
                    'title': request.title if 'request' in locals() else None
                },
                error={
                    'code': 'CREATE_FAILED',
                    'message': str(e)
                },
                provider='salesforce',
                resource_ref=None,
                ip=x_client_ip if 'x_client_ip' in locals() else None,
                user_agent=user_agent if 'user_agent' in locals() else None
            )
        
        raise_http_error(f"Failed to create task: {str(e)}", status_code=500, code="CREATE_FAILED")

@app.get("/opportunity/{opportunity_id}/live")
async def get_opportunity_live(
    opportunity_id: str,
    x_provider_token: str = Header(..., alias="X-Provider-Token")
):
    """Get live opportunity data"""
    try:
        # Validate token
        validate_provider_token(x_provider_token)

        # Validate required fields
        if not opportunity_id:
            raise_http_error("Opportunity ID is required", status_code=400, code="MISSING_OPPORTUNITY_ID")

        # Placeholder for CRM integration
        # In production, this would call the actual CRM API for live data
        live_data = {
            "id": opportunity_id,
            "name": f"Enterprise Deal {opportunity_id}",
            "stage": "proposal",
            "amount": 75000,
            "probability": 0.75,
            "close_date": "2025-12-31",
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "next_steps": "Schedule product demo",
            "stakeholders": [
                {"name": "John Doe", "role": "Decision Maker", "last_contact": "2025-08-15"},
                {"name": "Jane Smith", "role": "Technical Lead", "last_contact": "2025-08-20"}
            ],
            "activities": [
                {
                    "type": "call",
                    "description": "Discussed requirements",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "duration": 1800
                },
                {
                    "type": "email",
                    "description": "Sent proposal document",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            ]
        }

        logger.info(f"Retrieved live data for opportunity {opportunity_id}")

        return ok({
            "opportunity": live_data,
            "message": f"Live data retrieved for opportunity {opportunity_id}"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get live opportunity data: {e}")
        raise_http_error(f"Failed to get live opportunity data: {str(e)}", status_code=500, code="RETRIEVE_FAILED")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)