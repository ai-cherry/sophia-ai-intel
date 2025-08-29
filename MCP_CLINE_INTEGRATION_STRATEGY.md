# MCP-Cline Integration Strategy: Non-Intrusive Universal Connection

## Executive Summary

You can connect Cline to your existing MCP servers **without modifying their core functionality** by adding a thin MCP protocol adapter layer. This approach keeps your Sophia integration completely intact while exposing the same services to Cline.

## Current Architecture vs MCP Integration

### Your Current Setup
```
[Sophia App] <--HTTP API--> [MCP Services (8081-8092)] <---> [Databases/Vector Stores]
```

### Non-Intrusive MCP Integration Options

## Option 1: MCP Protocol Wrapper (Recommended)
**Most Universal & Non-Intrusive**

Create a separate MCP adapter service that translates between MCP protocol and your existing HTTP APIs:

```python
# mcp-adapter.py - Universal MCP wrapper for your existing services
import json
from typing import Any, Dict, List
import httpx

class MCPAdapter:
    """Universal adapter that exposes existing HTTP services via MCP protocol"""
    
    def __init__(self):
        self.services = {
            "context": "http://localhost:8081",
            "research": "http://localhost:8085",
            "github": "http://localhost:8082",
            "hubspot": "http://localhost:8083",
            # ... other services
        }
    
    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Translates MCP requests to HTTP API calls"""
        method = request.get("method")
        params = request.get("params", {})
        
        # Route to appropriate service
        if method.startswith("context."):
            return await self._proxy_to_service("context", method, params)
        elif method.startswith("github."):
            return await self._proxy_to_service("github", method, params)
        # ... other routing logic
    
    async def _proxy_to_service(self, service: str, method: str, params: Dict):
        """Proxy MCP calls to existing HTTP endpoints"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.services[service]}/{method.split('.')[-1]}",
                json=params
            )
            return response.json()
```

### Architecture with MCP Adapter:
```
[Cline] <--MCP Protocol--> [MCP Adapter:3000]
                                    |
                                    v
        [Your Existing Services (unchanged)]
                                    |
[Sophia App] <--HTTP API--> [MCP Services (8081-8092)]
```

## Option 2: Dual-Protocol Support
**Add MCP alongside HTTP without breaking existing code**

Modify services to support both protocols simultaneously:

```python
# In your existing service files, add MCP support
class ServiceWithDualProtocol:
    def __init__(self):
        self.http_app = FastAPI()  # Your existing HTTP API
        self.mcp_server = MCPServer()  # New MCP endpoint
        
    # Your existing HTTP endpoints remain unchanged
    @self.http_app.post("/search")
    async def http_search(self, query: str):
        return await self.search_logic(query)
    
    # Add MCP handler that uses the SAME logic
    @self.mcp_server.tool("search")
    async def mcp_search(self, query: str):
        return await self.search_logic(query)
    
    # Shared business logic - no duplication
    async def search_logic(self, query: str):
        # Your existing implementation
        pass
```

## Option 3: Configuration-Based MCP Server
**Use MCP server configuration files pointing to your HTTP services**

Create MCP configuration that proxies to your existing services:

```json
{
  "mcpServers": {
    "sophia-context": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http-proxy"],
      "env": {
        "PROXY_URL": "http://localhost:8081",
        "MCP_TOOLS": JSON.stringify([
          {
            "name": "store_document",
            "description": "Store document with embeddings",
            "endpoint": "/store",
            "method": "POST"
          },
          {
            "name": "search_documents",
            "description": "Semantic search",
            "endpoint": "/search",
            "method": "POST"
          }
        ])
      }
    }
  }
}
```

## Implementation Recommendations

### 1. Start with the MCP Adapter (Option 1)
- **Zero changes** to existing services
- Can be deployed as a single new container
- Easy to test and rollback
- Maintains complete separation of concerns

### 2. Deployment Strategy
```bash
# Add to your deploy-all-mcp.sh
docker run -d --name mcp-adapter \
  --network sophia-network \
  -p 3000:3000 \
  -v $(pwd)/mcp-adapter:/app \
  python:3.11-slim sh -c "pip install mcp httpx && python adapter.py"
```

### 3. Benefits of This Approach

#### For Sophia Integration:
- ✅ **No changes required** - Sophia continues using HTTP APIs
- ✅ **No risk** - Existing functionality unchanged
- ✅ **No performance impact** - Adapter only active when Cline connects

#### For Cline Integration:
- ✅ **Full MCP compliance** - Cline sees standard MCP servers
- ✅ **All tools available** - Complete access to your services
- ✅ **Native integration** - Works with Cline's existing MCP support

## Quick Start Implementation

### Step 1: Create MCP Adapter
```python
# mcp-universal-adapter.py
import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
import httpx

server = Server("sophia-mcp-adapter")

# Map MCP tools to your HTTP endpoints
SERVICE_MAP = {
    "search_context": ("POST", "http://localhost:8081/search"),
    "store_document": ("POST", "http://localhost:8081/store"),
    "github_search": ("POST", "http://localhost:8082/search"),
    # Add all your endpoints here
}

@server.tool()
async def search_context(query: str, limit: int = 10):
    """Search documents using semantic similarity"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8081/search",
            json={"query": query, "limit": limit}
        )
        return response.json()

# Add more tool decorators for each service...

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 2: Configure Cline
Add to Cline's MCP settings:
```json
{
  "sophia": {
    "command": "python",
    "args": ["/path/to/mcp-universal-adapter.py"]
  }
}
```

### Step 3: Test Connection
Your services remain running as-is, and Cline can now access them through MCP!

## Conclusion

**You don't need to modify your existing services at all.** The MCP Adapter pattern provides a clean, non-intrusive way to expose your services to Cline while maintaining complete compatibility with Sophia. This approach:

1. **Preserves your existing architecture** - No changes to core services
2. **Adds no complexity** to Sophia integration
3. **Provides full MCP functionality** to Cline
4. **Can be added/removed** without any impact
5. **Maintains single source of truth** - Business logic stays in one place

The adapter acts as a universal translator between MCP protocol and your HTTP APIs, giving you the best of both worlds without any compromise.
