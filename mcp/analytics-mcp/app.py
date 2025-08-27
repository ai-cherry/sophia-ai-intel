

Analytics and business intelligence integration for Sophia AI platform.
Provides access to analytics data, reporting, and business metrics with
read-only curated SQL over Neon database.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import asyncpg
from jinja2 import Template
from pydantic import BaseModel, validator

# Import shared platform libraries
from platform.common.service_base import create_app, ServiceConfig
from platform.auth.jwt import validate_token
from platform.common.errors import ServiceError, ValidationError, ok, err, raise_http_error # Ensure these are imported directly by the app

# Configure logging
logger = logging.getLogger(__name__)
#!/usr/bin/env python3
"""
Sophia AI Analytics MCP Service

Analytics and business intelligence integration for Sophia AI platform.
Provides access to analytics data, reporting, and business metrics with
read-only curated SQL over Neon database.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import asyncpg
from jinja2 import Template
from pydantic import BaseModel, validator

# Import shared platform libraries
from platform.common.service_base import create_app, ServiceConfig
from platform.auth.jwt import validate_token
from platform.common.errors import ServiceError, ValidationError, ok, err, raise_http_error

# Configure logging
logger = logging.getLogger(__name__)

# Environment configuration
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")

# Global variables
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

# Startup and shutdown handlers
async def startup_handler():
    """Initialize database connection pool"""
    global _db_pool

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

async def shutdown_handler():
    """Cleanup database connection pool"""
    global _db_pool
    if _db_pool:
        await _db_pool.close()
        logger.info("Database connection pool closed")

# Create FastAPI app using the shared service base
app = create_app(
    config=ServiceConfig(
        name="analytics-mcp",
        version="1.0.0", # This should ideally come from a package version
        description="Analytics and business intelligence integration with Neon SQL",
        startup_event=startup_handler,
        shutdown_event=shutdown_handler
    )
)

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

# Service-specific endpoints

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
        parameters = {k: v for k: v in parameters.items() if v is not None}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=os.getenv("ENVIRONMENT", "production") == "development"
    )
==============================

Analytics and business intelligence integration for Sophia AI platform.
Provides access to analytics data, reporting, and business metrics with
read-only curated SQL over Neon database.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import HTTPException
import asyncpg
from jinja2 import Template
from pydantic import BaseModel, validator

# Import shared platform libraries
try:
    from platform.common.service_base import create_app, ok, err, raise_http_error
    from platform.auth.jwt import validate_token
    from platform.common.errors import ServiceError, ValidationError
except ImportError:
    # Fallback for development
    from platform.common.service_base import create_app, ok, err, raise_http_error
    validate_token = None
    ServiceError = Exception
    ValidationError = Exception

# Configure logging
logger = logging.getLogger(__name__)

# Environment configuration
SERVICE_NAME = "Sophia AI Analytics MCP"
SERVICE_DESCRIPTION = "Analytics and business intelligence integration with Neon SQL"
SERVICE_VERSION = "1.0.0"
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")

# Global variables
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

# Startup and shutdown handlers
async def startup_handler():
    """Initialize database connection pool"""
    global _db_pool

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

async def shutdown_handler():
    """Cleanup database connection pool"""
    global _db_pool
    if _db_pool:
        await _db_pool.close()
        logger.info("Database connection pool closed")

# Create FastAPI app using the shared service base
app = create_app(
    name=SERVICE_NAME,
    desc=SERVICE_DESCRIPTION,
    version=SERVICE_VERSION,
    startup_handler=startup_handler,
    shutdown_handler=shutdown_handler
)

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

# Service-specific endpoints

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

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=os.getenv("ENVIRONMENT", "production") == "development"
    )
