#!/usr/bin/env python3
"""
Sophia AI Projects MCP Service
==============================

Project management and collaboration integration for Sophia AI platform.
Provides access to project boards, tasks, timelines, and team collaboration tools.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import Header, Query
from pydantic import BaseModel

# Import shared platform libraries
try:
    from platform.common.service_base import create_app, ok, err, raise_http_error
    from platform.auth.jwt import validate_token
    from platform.common.errors import ServiceError, ValidationError
    from platform.common.audit import log_tool_invocation, cleanup_connection_pool
except ImportError:
    # Fallback for development
    from platform.common.service_base import create_app, ok, err, raise_http_error
    validate_token = None
    ServiceError = Exception
    ValidationError = Exception
    # Mock audit functions for development
    async def log_tool_invocation(*args, **kwargs):
        return None
    async def cleanup_connection_pool():
        pass

# Configure logging
logger = logging.getLogger(__name__)

# Environment configuration
SERVICE_NAME = "Sophia AI Projects MCP"
SERVICE_DESCRIPTION = "Project management and collaboration integration"
SERVICE_VERSION = "1.0.0"

# Pydantic models for request/response validation
class CreateIssueRequest(BaseModel):
    title: str
    description: Optional[str] = None
    assignee: Optional[str] = None
    labels: Optional[List[str]] = None
    priority: str = "medium"
    due_date: Optional[str] = None

# Startup and shutdown handlers
async def startup_handler():
    """Initialize resources on startup"""
    logger.info(f"{SERVICE_NAME} starting...")

async def shutdown_handler():
    """Clean up resources on shutdown"""
    await cleanup_connection_pool()
    logger.info(f"{SERVICE_NAME} shutting down")

# Create FastAPI app using the shared service base
app = create_app(
    name=SERVICE_NAME,
    desc=SERVICE_DESCRIPTION,
    version=SERVICE_VERSION,
    startup_handler=startup_handler,
    shutdown_handler=shutdown_handler
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

@app.post("/issue/create")
async def create_issue(
    request: CreateIssueRequest,
    x_provider_token: str = Header(..., alias="X-Provider-Token"),
    x_tenant_id: str = Header(None, alias="X-Tenant-Id"),
    x_actor_id: str = Header(None, alias="X-Actor-Id"),
    x_client_ip: str = Header(None, alias="X-Forwarded-For"),
    user_agent: str = Header(None)
):
    """Create new issue"""
    try:
        # Validate token
        validate_provider_token(x_provider_token)

        # Validate required fields
        if not request.title:
            raise_http_error("Issue title is required", status_code=400, code="MISSING_TITLE")

        # Placeholder for project management integration
        # In production, this would call the actual project management API (e.g., Jira, GitHub Issues)
        issue_id = f"issue_{datetime.now().timestamp()}"
        created_issue = {
            "id": issue_id,
            "title": request.title,
            "description": request.description,
            "assignee": request.assignee,
            "labels": request.labels or [],
            "priority": request.priority,
            "status": "open",
            "due_date": request.due_date,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": "sophia-ai-mcp",
            "url": f"https://project-management.example.com/issues/{issue_id}"
        }

        logger.info(f"Created issue {issue_id}: {request.title}")

        response_data = {
            "issue": created_issue,
            "message": f"Issue '{request.title}' created successfully"
        }

        # Log audit record for successful operation
        audit_ctx = {
            'tenant': x_tenant_id or 'default',
            'actor': x_actor_id or 'system',
            'purpose': 'issue_creation'
        }
        
        await log_tool_invocation(
            ctx=audit_ctx,
            service='projects-mcp',
            tool='issue/create',
            request={
                'title': request.title,
                'description': request.description,
                'assignee': request.assignee,
                'labels': request.labels,
                'priority': request.priority,
                'due_date': request.due_date
            },
            response=response_data,
            provider='github',
            resource_ref=issue_id,
            ip=x_client_ip,
            user_agent=user_agent
        )

        return ok(response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create issue: {e}")
        
        # Log audit record for failed operation
        if 'audit_ctx' in locals():
            await log_tool_invocation(
                ctx=audit_ctx,
                service='projects-mcp',
                tool='issue/create',
                request={
                    'title': request.title if 'request' in locals() else None
                },
                error={
                    'code': 'CREATE_FAILED',
                    'message': str(e)
                },
                provider='github',
                resource_ref=None,
                ip=x_client_ip if 'x_client_ip' in locals() else None,
                user_agent=user_agent if 'user_agent' in locals() else None
            )
        
        raise_http_error(f"Failed to create issue: {str(e)}", status_code=500, code="CREATE_FAILED")

@app.get("/work/open")
async def get_open_work(
    account_id: str = Query(..., description="Account ID to get open work for"),
    x_provider_token: str = Header(..., alias="X-Provider-Token")
):
    """Get open work items"""
    try:
        # Validate token
        validate_provider_token(x_provider_token)

        # Validate required fields
        if not account_id:
            raise_http_error("Account ID is required", status_code=400, code="MISSING_ACCOUNT_ID")

        # Placeholder for project management integration
        # In production, this would call the actual project management API
        open_work = [
            {
                "id": "task_001",
                "type": "task",
                "title": "Implement user authentication system",
                "description": "Set up JWT authentication with role-based access control",
                "assignee": "john.doe",
                "priority": "high",
                "status": "in_progress",
                "due_date": "2025-09-15",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "project": "Platform Development",
                "url": "https://project-management.example.com/tasks/task_001"
            },
            {
                "id": "issue_002",
                "type": "issue",
                "title": "Fix mobile responsiveness on dashboard",
                "description": "Dashboard not displaying correctly on mobile devices",
                "assignee": "jane.smith",
                "priority": "medium",
                "status": "open",
                "due_date": "2025-09-20",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "project": "UI/UX Improvements",
                "url": "https://project-management.example.com/issues/issue_002"
            },
            {
                "id": "task_003",
                "type": "task",
                "title": "Set up CI/CD pipeline",
                "description": "Configure automated testing and deployment pipeline",
                "assignee": "devops.team",
                "priority": "high",
                "status": "open",
                "due_date": "2025-09-10",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "project": "DevOps",
                "url": "https://project-management.example.com/tasks/task_003"
            },
            {
                "id": "issue_004",
                "type": "issue",
                "title": "API rate limiting not working",
                "description": "Rate limiting middleware is not being applied correctly",
                "assignee": "backend.team",
                "priority": "high",
                "status": "open",
                "due_date": "2025-09-12",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "project": "Backend Services",
                "url": "https://project-management.example.com/issues/issue_004"
            }
        ]

        logger.info(f"Retrieved {len(open_work)} open work items for account {account_id}")

        return ok({
            "work_items": open_work,
            "count": len(open_work),
            "account_id": account_id,
            "message": f"Retrieved {len(open_work)} open work items"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get open work: {e}")
        raise_http_error(f"Failed to get open work: {str(e)}", status_code=500, code="RETRIEVE_FAILED")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)