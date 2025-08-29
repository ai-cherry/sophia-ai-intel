#!/usr/bin/env python3
"""
Universal MCP Adapter for Sophia AI Services
=============================================
This adapter allows Cline to connect to your existing HTTP-based services
without requiring any modifications to those services.

Your Sophia integration remains completely unchanged.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
except ImportError:
    print("MCP library not installed. Install with: pip install mcp")
    exit(1)

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("sophia-mcp-adapter")

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

# ============================================================================
# CONTEXT SERVICE TOOLS
# ============================================================================

@server.tool()
async def search_context(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search documents using semantic similarity in the context service.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return
    
    Returns:
        Search results with similarity scores
    """
    try:
        response = await client.post(
            f"{SERVICES['context']['base_url']}/search",
            json={"query": query, "limit": limit}
        )
        response.raise_for_status()
        return {"success": True, "results": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

@server.tool()
async def store_document(content: str, source: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Store a document with embeddings in the context service.
    
    Args:
        content: Document content
        source: Source identifier
        metadata: Optional metadata dictionary
    
    Returns:
        Storage confirmation with document ID
    """
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

# ============================================================================
# RESEARCH SERVICE TOOLS
# ============================================================================

@server.tool()
async def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Perform web search using the research service.
    
    Args:
        query: Search query
        max_results: Maximum number of results
    
    Returns:
        Web search results
    """
    try:
        response = await client.post(
            f"{SERVICES['research']['base_url']}/search",
            json={"query": query, "limit": max_results}
        )
        response.raise_for_status()
        return {"success": True, "results": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# GITHUB SERVICE TOOLS
# ============================================================================

@server.tool()
async def search_code(repo: str, query: str, file_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Search code in GitHub repositories.
    
    Args:
        repo: Repository name (owner/repo format)
        query: Search query
        file_type: Optional file extension filter (e.g., 'py', 'js')
    
    Returns:
        Code search results
    """
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

# ============================================================================
# CRM SERVICE TOOLS
# ============================================================================

@server.tool()
async def get_crm_contacts(service: str = "hubspot", limit: int = 10) -> Dict[str, Any]:
    """
    Get CRM contacts from HubSpot or Salesforce.
    
    Args:
        service: CRM service to use ('hubspot' or 'salesforce')
        limit: Maximum number of contacts to return
    
    Returns:
        CRM contact list
    """
    if service not in ["hubspot", "salesforce"]:
        return {"success": False, "error": "Service must be 'hubspot' or 'salesforce'"}
    
    try:
        response = await client.get(
            f"{SERVICES[service]['base_url']}/contacts",
            params={"limit": limit}
        )
        response.raise_for_status()
        return {"success": True, "contacts": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# ORCHESTRATION TOOLS
# ============================================================================

@server.tool()
async def execute_workflow(workflow_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a workflow through the orchestrator service.
    
    Args:
        workflow_name: Name of the workflow to execute
        parameters: Workflow parameters
    
    Returns:
        Workflow execution result
    """
    try:
        response = await client.post(
            f"{SERVICES['orchestrator']['base_url']}/execute",
            json={
                "workflow": workflow_name,
                "parameters": parameters
            }
        )
        response.raise_for_status()
        return {"success": True, "result": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

@server.tool()
async def create_agent_task(task_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new task for the agent coordinator.
    
    Args:
        task_type: Type of task to create
        parameters: Task parameters
    
    Returns:
        Task creation confirmation with task ID
    """
    try:
        response = await client.post(
            f"{SERVICES['coordinator']['base_url']}/tasks",
            json={
                "type": task_type,
                "parameters": parameters,
                "created_at": datetime.now().isoformat()
            }
        )
        response.raise_for_status()
        return {"success": True, "task": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# SERVICE HEALTH TOOLS
# ============================================================================

@server.tool()
async def check_service_health(service_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Check health status of services.
    
    Args:
        service_name: Specific service to check, or None for all services
    
    Returns:
        Health status of requested service(s)
    """
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
# RESOURCE HANDLERS
# ============================================================================

@server.list_resources()
async def list_resources() -> List[Dict[str, Any]]:
    """List available resources from all services."""
    resources = []
    
    for service_name, service_info in SERVICES.items():
        resources.append({
            "uri": f"sophia://{service_name}",
            "name": f"{service_name.capitalize()} Service",
            "description": service_info["description"],
            "mimeType": "application/json"
        })
    
    return resources

@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource information from a specific service."""
    if not uri.startswith("sophia://"):
        return json.dumps({"error": "Invalid URI format"})
    
    service_name = uri.replace("sophia://", "")
    
    if service_name not in SERVICES:
        return json.dumps({"error": f"Unknown service: {service_name}"})
    
    # Get service info and health
    service_info = SERVICES[service_name]
    health = await check_service_health(service_name)
    
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
    """Main entry point for the MCP adapter."""
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
