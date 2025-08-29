#!/usr/bin/env python3
"""
Simple working MCP adapter for Sophia AI services
"""

import asyncio
import json
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
import httpx

# Create server
server = Server("sophia-mcp")

# HTTP client
client = httpx.AsyncClient(timeout=30.0)

# Service URLs
SERVICES = {
    "context": "http://localhost:8081",
    "research": "http://localhost:8085",
    "github": "http://localhost:8082",
    "hubspot": "http://localhost:8083",
    "salesforce": "http://localhost:8092",
    "gong": "http://localhost:8091",
    "agents": "http://localhost:8000",
    "coordinator": "http://localhost:8080",
    "orchestrator": "http://localhost:8088"
}

@server.list_tools()
async def list_tools():
    """List available tools"""
    return [
        {
            "name": "check_service_health",
            "description": "Check health of all services",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        }
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[dict]:
    """Handle tool calls"""
    if name == "check_service_health":
        results = {}
        
        for service_name, base_url in SERVICES.items():
            try:
                response = await client.get(f"{base_url}/health", timeout=2.0)
                if response.status_code == 200:
                    data = response.json()
                    results[service_name] = {
                        "status": "✅ healthy",
                        "details": data
                    }
                elif response.status_code == 404:
                    results[service_name] = {
                        "status": "⚠️ running (no health endpoint)"
                    }
                else:
                    results[service_name] = {
                        "status": f"❌ error (status {response.status_code})"
                    }
            except Exception as e:
                results[service_name] = {
                    "status": f"❌ error: {str(e)[:50]}"
                }
        
        return [
            {
                "type": "text",
                "text": json.dumps(results, indent=2)
            }
        ]
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdio
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

if __name__ == "__main__":
    asyncio.run(main())
