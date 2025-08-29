#!/usr/bin/env python3
"""
Fixed MCP Adapter for Sophia AI Services
=========================================
This adapter allows Cline to connect to your existing HTTP-based services
without requiring any modifications to those services.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import Tool, Resource
except ImportError:
    print("MCP library not installed. Install with: pip install mcp")
    exit(1)

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service endpoints mapping
SERVICES = {
    "context": {
        "base_url": "http://localhost:8081",
        "description": "Document storage and semantic search"
    },
    "research": {
        "base_url": "http://localhost:8085", 
        "description": "Research and web search capabilities"
    },
    "github": {
        "base_url": "http://localhost:8082",
        "description": "GitHub repository integration"
    },
    "hubspot": {
        "base_url": "http://localhost:8083",
        "description": "HubSpot CRM integration"
    },
    "salesforce": {
        "base_url": "http://localhost:8092",
        "description": "Salesforce CRM integration"
    },
    "gong": {
        "base_url": "http://localhost:8091",
        "description": "Gong call analytics"
    },
    "agents": {
        "base_url": "http://localhost:8000",
        "description": "AI agent orchestration"
    },
    "coordinator": {
        "base_url": "http://localhost:8080",
        "description": "AGNO coordinator service"
    },
    "orchestrator": {
        "base_url": "http://localhost:8088",
        "description": "Workflow orchestration"
    }
}

# HTTP client with timeout
client = httpx.AsyncClient(timeout=30.0)

# Initialize MCP server
server = Server("sophia-mcp-adapter", version="1.0.0")

# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

async def search_context_impl(query: str, limit: int = 10) -> Dict[str, Any]:
    """Search documents using semantic similarity"""
    try:
        response = await client.post(
            f"{SERVICES['context']['base_url']}/search",
            json={"query": query, "limit": limit}
        )
        response.raise_for_status()
        return {"success": True, "results": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def store_document_impl(content: str, source: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """Store a document with embeddings"""
    try:
        response = await client.post(
            f"{SERVICES['context']['base_url']}/store",
            json={
                "content": content,
                "source": source,
                "metadata": metadata or {}
            }
        )
        response.raise_for_status()
        return {"success": True, "result": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def web_search_impl(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Perform web search"""
    try:
        response = await client.post(
            f"{SERVICES['research']['base_url']}/search",
            json={"query": query, "limit": max_results}
        )
        response.raise_for_status()
        return {"success": True, "results": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def search_code_impl(repo: str, query: str, file_type: Optional[str] = None) -> Dict[str, Any]:
    """Search code in GitHub repositories"""
    try:
        params = {"repo": repo, "query": query}
        if file_type:
            params["file_type"] = file_type
            
        response = await client.post(
            f"{SERVICES['github']['base_url']}/search",
            json=params
        )
        response.raise_for_status()
        return {"success": True, "results": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def check_service_health_impl(service_name: Optional[str] = None) -> Dict[str, Any]:
    """Check health status of services"""
    results = {}
    
    services_to_check = [service_name] if service_name else SERVICES.keys()
    
    for service in services_to_check:
        if service not in SERVICES:
            results[service] = {"status": "unknown", "error": "Service not found"}
            continue
            
        try:
            response = await client.get(
                f"{SERVICES[service]['base_url']}/health",
                timeout=5.0
            )
            response.raise_for_status()
            results[service] = {
                "status": "healthy",
                "details": response.json()
            }
        except httpx.TimeoutException:
            results[service] = {"status": "timeout", "error": "Health check timed out"}
        except Exception as e:
            results[service] = {"status": "unhealthy", "error": str(e)}
    
    return {"services": results, "timestamp": datetime.now().isoformat()}

# ============================================================================
# REGISTER TOOLS WITH SERVER
# ============================================================================

# Define tools list
TOOLS = [
    Tool(
        name="search_context",
        description="Search documents using semantic similarity in the context service",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results", "default": 10}
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="store_document",
        description="Store a document with embeddings in the context service",
        inputSchema={
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Document content"},
                "source": {"type": "string", "description": "Source identifier"},
                "metadata": {"type": "object", "description": "Optional metadata"}
            },
            "required": ["content", "source"]
        }
    ),
    Tool(
        name="web_search",
        description="Perform web search using the research service",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results", "default": 5}
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="search_code",
        description="Search code in GitHub repositories",
        inputSchema={
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository (owner/repo)"},
                "query": {"type": "string", "description": "Search query"},
                "file_type": {"type": "string", "description": "File extension filter"}
            },
            "required": ["repo", "query"]
        }
    ),
    Tool(
        name="check_service_health",
        description="Check health status of services",
        inputSchema={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Service to check (optional)"}
            }
        }
    )
]

# Tool implementations mapping
TOOL_HANDLERS = {
    "search_context": search_context_impl,
    "store_document": store_document_impl,
    "web_search": web_search_impl,
    "search_code": search_code_impl,
    "check_service_health": check_service_health_impl
}

# Register list_tools handler
@server.list_tools()
async def list_tools() -> List[Tool]:
    """Return the list of available tools"""
    return TOOLS

# Register call_tool handler
@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> Any:
    """Execute a tool by name with the given arguments"""
    if name not in TOOL_HANDLERS:
        raise ValueError(f"Unknown tool: {name}")
    
    handler = TOOL_HANDLERS[name]
    result = await handler(**arguments)
    return result

# ============================================================================
# RESOURCE HANDLERS
# ============================================================================

# Define resources
RESOURCES = [
    Resource(
        uri=f"sophia://{service_name}",
        name=f"{service_name.capitalize()} Service",
        description=service_info["description"],
        mimeType="application/json"
    )
    for service_name, service_info in SERVICES.items()
]

@server.list_resources()
async def list_resources() -> List[Resource]:
    """List available resources from all services"""
    return RESOURCES

@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource information from a specific service"""
    if not uri.startswith("sophia://"):
        return json.dumps({"error": "Invalid URI format"})
    
    service_name = uri.replace("sophia://", "")
    
    if service_name not in SERVICES:
        return json.dumps({"error": f"Unknown service: {service_name}"})
    
    # Get service info and health
    service_info = SERVICES[service_name]
    health = await check_service_health_impl(service_name)
    
    return json.dumps({
        "service": service_name,
        "info": service_info,
        "health": health["services"][service_name],
        "timestamp": datetime.now().isoformat()
    }, indent=2)

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point for the MCP adapter"""
    logger.info("Starting Sophia MCP Adapter...")
    logger.info(f"Configured services: {', '.join(SERVICES.keys())}")
    
    # Run the MCP server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP server ready for connections")
        await server.run(read_stream, write_stream)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down MCP adapter...")
    except Exception as e:
        logger.error(f"Error running adapter: {e}")
        exit(1)
