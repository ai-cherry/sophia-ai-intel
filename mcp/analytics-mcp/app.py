
#!/usr/bin/env python3
"""
Sophia AI Analytics MCP Service
==============================

Analytics and business intelligence integration for Sophia AI platform.
Provides access to analytics data, reporting, and business metrics with
read-only curated SQL over Neon database.
"""

import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import asyncpg
from jinja2 import Template
from pydantic import BaseModel, validator

# Import shared platform libraries
try:
    from platform.auth.jwt import validate_token
    from platform.common.errors import ServiceError, ValidationError, ok, err, raise_http_error
except ImportError:
    # Fallback for development
    validate_token = None
    ServiceError = Exception
    ValidationError = Exception
    def ok(data: Any = None) -> Dict[str, Any]:
        return {"status": "ok", "data": data}
    def err(message: str, code: str = "ERROR", status_code: int = 400, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "status": "error",
            "error": {
                "code": code,
                "message": message,
                "details": details or {}
            }
        }
    def raise_http_error(message: str, status_code: int = 400, code: str = "HTTP_ERROR") -> None:
        raise HTTPException(status_code=status_code, detail=err(message, code, status_code))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Environment configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
SERVICE_NAME = "Sophia AI Analytics MCP"
SERVICE_DESCRIPTION = "Analytics and business intelligence integration with Neon SQL"
SERVICE_VERSION = "1.0.0"
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")

# Global variables
_ready = False
_db_pool: Optional[asyncpg.Pool] = None

# SQL Templates structure - whitelisted templates only
SQL_TEMPLATES = {
    "timeline": {
        "query": """
        SELECT
            id,
            account_id,
            interaction_type,
            content,
            metadata,
            created_at,
            updated_at
        FROM interactions
        WHERE account_id = '{{ account_id }}'
        {% if since %}
        AND created_at >= '{{ since }}'
        {% endif %}
        ORDER BY created_at DESC
        {% if limit %}
        LIMIT {{ limit }}
        {% endif %}
        """,
        "description": "Get timeline of interactions for an account",
        "parameters": ["account_id", "since", "limit"],
        "required": ["account_id"]
    },
    "user_analytics": {
        "query": """
        SELECT
            account_id,
            COUNT(*) as total_interactions,
            COUNT(DISTINCT DATE(created_at)) as active_days,
            MAX(created_at) as last_activity,
            MIN(created_at) as first_activity
        FROM interactions
        WHERE created_at >= '{{ start_date }}'
        AND created_at <= '{{ end_date }}'
        GROUP BY account_id
        ORDER BY total_interactions DESC
        {% if limit %}
        LIMIT {{ limit }}
        {% endif %}
        """,
        "description": "Get user analytics for date range",
        "parameters": ["start_date", "end_date", "limit"],
        "required": ["start_date", "end_date"]
    },
    "interaction_summary": {
        "query": """
        SELECT
            interaction_type,
            COUNT(*) as count,
            AVG(LENGTH(content)) as avg_content_length,
            MIN(created_at) as earliest,
            MAX(created_at) as latest
        FROM interactions
        WHERE created_at >= '{{ start_date }}'
        AND created_at <= '{{ end_date }}'
        {% if account_id %}
        AND account_id = '{{ account_id }}'
        {% endif %}
        GROUP BY interaction_type
        ORDER BY count DESC
        """,
        "description": "Get interaction summary statistics",
        "parameters": ["start_date", "end_date", "account_id"],
        "required": ["start_date", "end_date"]
    }
}

# Pydantic models
class SQLTemplateRequest(BaseModel):
    template_id: str
    parameters: Dict[str, Any] = {}

    @validator('template_id')
    def validate_template_id(cls, v):
        if v not in SQL_TEMPLATES:
            raise ValueError(f"Unknown template_id: {v}")
        return v

class TimelineRequest(BaseModel):
    account_id: str
    since: Optional[str] = None
    limit: Optional[int] = None

    @validator('limit')
    def validate_limit(cls, v):
        if v is not None and (v < 1 or v > 1000):
            raise ValueError("Limit must be between 1 and 1000")
        return v

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await startup_event()
    yield
    # Shutdown
    await shutdown_event()

async def startup_event():
    """Set readiness flag and initialize database connection pool"""
    global _ready, _db_pool

    if not NEON_DATABASE_URL:
        logger.warning("NEON_DATABASE_URL not configured - database features will be disabled")
    else:
        try:
            # Create connection pool
            _db_pool = await asyncpg.create_pool(
                NEON_DATABASE_URL,
                min_size=1,
                max_size=10,
                command_timeout=60,
                max_inactive_connection_lifetime=300
            )
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise

    _ready = True
    logger.info(f"{SERVICE_NAME} v{SERVICE_VERSION} started and ready")

async def shutdown_event():
    """Cleanup database connection pool"""
    global _db_pool
    if _db_pool:
        await _db_pool.close()
        logger.info("Database connection pool closed")

def render_sql(template_id: str, parameters: Dict[str, Any]) -> str:
    """
    Render SQL template with Jinja2 and parameter validation.

    Args:
        template_id: The template identifier
        parameters: Dictionary of parameters to substitute

    Returns:
        Rendered SQL query string

    Raises:
        ValidationError: If template_id is unknown or parameters are invalid
    """
    if template_id not in SQL_TEMPLATES:
        raise ValidationError(f"Unknown template_id: {template_id}")

    template_config = SQL_TEMPLATES[template_id]

    # Validate required parameters
    required_params = template_config.get("required", [])
    for param in required_params:
        if param not in parameters or parameters[param] is None:
            raise ValidationError(f"Missing required parameter: {param}")

    # Validate parameter types and sanitize
    sanitized_params = {}
    for key, value in parameters.items():
        if key not in template_config["parameters"]:
            raise ValidationError(f"Unknown parameter: {key}")

        # Basic sanitization - prevent SQL injection through template parameters
        if isinstance(value, str):
            # Remove any potential SQL injection characters
            sanitized_params[key] = value.replace("'", "''").replace("\\", "\\\\")
        else:
            sanitized_params[key] = value

    # Render template
    try:
        template = Template(template_config["query"])
        rendered_sql = template.render(**sanitized_params)
        logger.debug(f"Rendered SQL for template '{template_id}': {rendered_sql}")
        return rendered_sql
    except Exception as e:
        raise ValidationError(f"Failed to render SQL template: {e}")

async def execute_query(sql: str) -> List[Dict[str, Any]]:
    """
    Execute SQL query against Neon database.

    Args:
        sql: The SQL query to execute

    Returns:
        List of query results as dictionaries

    Raises:
        ServiceError: If database is not available or query fails
    """
    if not _db_pool:
        raise ServiceError("Database connection not available", code="DB_UNAVAILABLE")

    if not NEON_DATABASE_URL:
        raise ServiceError("Database not configured", code="DB_NOT_CONFIGURED")

    try:
        async with _db_pool.acquire() as connection:
            # Execute query with read-only transaction for security
            async with connection.transaction(readonly=True):
                rows = await connection.fetch(sql)
                # Convert rows to dictionaries
                results = [dict(row) for row in rows]
                return results
    except asyncpg.exceptions.PostgresError as e:
        logger.error(f"Database query failed: {e}")
        raise ServiceError(f"Database query failed: {str(e)}", code="DB_QUERY_ERROR")
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
        raise ServiceError(f"Unexpected database error: {str(e)}", code="DB_ERROR")

@app.on_event("startup")
async def startup():
    """FastAPI startup event"""
    pass  # Handled by lifespan context manager

@app.on_event("shutdown")
async def shutdown():
    """FastAPI shutdown event"""
    pass  # Handled by lifespan context manager

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "database": "connected" if _db_pool else "disconnected",
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
        "database": "connected" if _db_pool else "disconnected",
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
        "database": "connected" if _db_pool else "disconnected",
        "endpoints": {
            "health": "/healthz",
            "ready": "/readyz",
            "stream": "/stream",
            "docs": "/docs",
            "query_sql_template": "/query_sql_template",
            "timeline": "/timeline",
            "templates": "/templates"
        },
    }

@app.get("/templates")
async def list_templates():
    """List available SQL templates"""
    return ok({
        template_id: {
            "description": config["description"],
            "parameters": config["parameters"],
            "required": config.get("required", [])
        }
        for template_id, config in SQL_TEMPLATES.items()
    })

@app.post("/query_sql_template")
async def query_sql_template_endpoint(request: SQLTemplateRequest):
    """
    Execute a whitelisted SQL template with parameters.

    Args:
        request: SQLTemplateRequest containing template_id and parameters

    Returns:
        JSON response with query results or error
    """
    try:
        # Render SQL template
        sql = render_sql(request.template_id, request.parameters)

        # Execute query
        results = await execute_query(sql)

        return ok(results)

    except ValidationError as e:
        logger.warning(f"Template validation error: {e}")
        raise_http_error(str(e), status_code=400, code="VALIDATION_ERROR")

    except ServiceError as e:
        logger.error(f"Database service error: {e}")
        if "not configured" in str(e).lower():
            raise_http_error("Database not configured", status_code=503, code="DB_NOT_CONFIGURED")
        raise_http_error(str(e), status_code=500, code=e.code)

    except Exception as e:
        logger.error(f"Unexpected error in query_sql_template: {e}")
        raise_http_error("Internal server error", status_code=500, code="INTERNAL_ERROR")

@app.post("/timeline")
async def timeline_endpoint(request: TimelineRequest):
    """
    Get timeline of interactions for an account.

    Args:
        request: TimelineRequest containing account_id, since, limit

    Returns:
        JSON response with interaction records
    """
    try:
        # Prepare parameters for timeline template
        parameters = {
            "account_id": request.account_id,
            "since": request.since,
            "limit": request.limit
        }

        # Filter out None values
        parameters = {k: v for k, v in parameters.items() if v is not None}

        # Use the timeline template
        sql = render_sql("timeline", parameters)

        # Execute query
        results = await execute_query(sql)

        return ok(results)

    except ValidationError as e:
        logger.warning(f"Timeline validation error: {e}")
        raise_http_error(str(e), status_code=400, code="VALIDATION_ERROR")

    except ServiceError as e:
        logger.error(f"Database service error in timeline: {e}")
        if "not configured" in str(e).lower():
            raise_http_error("Database not configured", status_code=503, code="DB_NOT_CONFIGURED")
        raise_http_error(str(e), status_code=500, code=e.code)

    except Exception as e:
        logger.error(f"Unexpected error in timeline: {e}")
        raise_http_error("Internal server error", status_code=500, code="INTERNAL_ERROR")

# Set lifespan for FastAPI app
app.router.lifespan_context = lifespan

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=os.getenv("ENVIRONMENT", "production") == "development"
    )
        },
