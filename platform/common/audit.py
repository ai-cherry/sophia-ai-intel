#!/usr/bin/env python3
"""
Sophia AI Audit Helper
======================

Provides async audit logging for MCP tool invocations to Neon database.
Logs all write operations across MCP services for compliance and debugging.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import uuid4

import asyncpg
from asyncpg import Connection, Pool

# Configure logging
logger = logging.getLogger(__name__)

# Database connection pool (module-level for reuse)
_connection_pool: Optional[Pool] = None


async def get_connection_pool() -> Optional[Pool]:
    """Get or create database connection pool."""
    global _connection_pool
    
    if _connection_pool is not None:
        return _connection_pool
    
    database_url = os.getenv("NEON_DATABASE_URL")
    if not database_url:
        logger.warning("NEON_DATABASE_URL not set, audit logging disabled")
        return None
    
    try:
        _connection_pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=10,
            command_timeout=10,
            server_settings={
                'application_name': 'sophia-audit'
            }
        )
        logger.info("Audit database connection pool created")
        return _connection_pool
    except Exception as e:
        logger.error(f"Failed to create audit database pool: {e}")
        return None


async def log_tool_invocation(
    ctx: Dict[str, Any],
    service: str,
    tool: str,
    request: Dict[str, Any],
    response: Optional[Dict[str, Any]] = None,
    error: Optional[Dict[str, Any]] = None,
    provider: Optional[str] = None,
    resource_ref: Optional[str] = None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Optional[str]:
    """
    Log a tool invocation to the audit database.
    
    Args:
        ctx: Context dict containing tenant, actor, and purpose
        service: MCP service name (e.g., 'crm-mcp', 'comms-mcp')
        tool: Tool/endpoint name (e.g., 'update_stage', 'post_message')
        request: Request payload dict
        response: Response payload dict (if successful)
        error: Error details dict (if failed)
        provider: External provider name (e.g., 'salesforce', 'slack')
        resource_ref: Reference to external resource (e.g., opportunity_id)
        ip: Client IP address
        user_agent: Client user agent string
    
    Returns:
        Audit record ID if successful, None if logging failed
    
    Example:
        await log_tool_invocation(
            ctx={'tenant': 'org_123', 'actor': 'user_456', 'purpose': 'sales_update'},
            service='crm-mcp',
            tool='update_stage',
            request={'opportunity_id': 'opp_789', 'stage': 'proposal'},
            response={'status': 'ok', 'data': {...}},
            provider='salesforce',
            resource_ref='opp_789',
            ip='192.168.1.1',
            user_agent='Sophia-AI/1.0'
        )
    """
    pool = await get_connection_pool()
    if pool is None:
        logger.debug("Audit logging skipped - no database connection")
        return None
    
    # Extract context fields
    tenant = ctx.get('tenant', 'unknown')
    actor = ctx.get('actor', 'unknown')
    purpose = ctx.get('purpose')
    
    # Generate audit record ID
    audit_id = str(uuid4())
    
    # Prepare the SQL query
    query = """
        INSERT INTO audit.tool_invocations (
            id, at, tenant, actor, service, tool,
            request, response, error,
            provider, resource_ref, purpose,
            ip, user_agent
        )
        VALUES (
            $1, $2, $3, $4, $5, $6,
            $7, $8, $9,
            $10, $11, $12,
            $13, $14
        )
    """
    
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                query,
                audit_id,
                datetime.now(timezone.utc),
                tenant,
                actor,
                service,
                tool,
                json.dumps(request),
                json.dumps(response) if response else None,
                json.dumps(error) if error else None,
                provider,
                resource_ref,
                purpose,
                ip,
                user_agent
            )
        
        logger.info(f"Audit logged: {service}/{tool} by {actor} [{audit_id}]")
        return audit_id
        
    except Exception as e:
        # Log error but don't fail the main operation
        logger.error(f"Failed to log audit record: {e}", exc_info=True)
        return None


async def cleanup_connection_pool():
    """Clean up database connection pool on shutdown."""
    global _connection_pool
    
    if _connection_pool is not None:
        try:
            await _connection_pool.close()
            logger.info("Audit database connection pool closed")
        except Exception as e:
            logger.error(f"Error closing audit database pool: {e}")
        finally:
            _connection_pool = None


# Helper functions for common audit scenarios

async def log_write_operation(
    service: str,
    tool: str,
    request: Dict[str, Any],
    response: Optional[Dict[str, Any]] = None,
    error: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Optional[str]:
    """
    Simplified helper for logging write operations.
    Extracts context from environment or defaults.
    """
    # Try to extract context from environment or use defaults
    ctx = {
        'tenant': os.getenv('TENANT_ID', 'default'),
        'actor': os.getenv('ACTOR_ID', 'system'),
        'purpose': kwargs.get('purpose', 'write_operation')
    }
    
    return await log_tool_invocation(
        ctx=ctx,
        service=service,
        tool=tool,
        request=request,
        response=response,
        error=error,
        provider=kwargs.get('provider'),
        resource_ref=kwargs.get('resource_ref'),
        ip=kwargs.get('ip'),
        user_agent=kwargs.get('user_agent')
    )


async def log_error_operation(
    service: str,
    tool: str,
    request: Dict[str, Any],
    error_message: str,
    error_code: str = 'ERROR',
    **kwargs
) -> Optional[str]:
    """
    Helper for logging failed operations.
    """
    error_dict = {
        'code': error_code,
        'message': error_message,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    return await log_write_operation(
        service=service,
        tool=tool,
        request=request,
        error=error_dict,
        **kwargs
    )