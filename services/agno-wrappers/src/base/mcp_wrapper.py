"""
Base AGNO Wrapper Framework for MCP Services
=============================================

This module provides the foundation for creating AGNO-compatible agent wrappers
around existing MCP (Model Context Protocol) services. The framework enables
seamless integration between the AGNO orchestration layer and existing MCP
services without disrupting current functionality.

Key Features:
- MCP protocol client implementation
- Base agent wrapper class
- Tool discovery and registration
- Health monitoring and error handling
- Caching and performance optimization
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp
import json
from datetime import datetime

from agno import Agent, Tool, Context
from agno.memory import Memory
from agno.utils import logger

T = TypeVar('T')

class MCPMethod(Enum):
    """Standard MCP protocol methods"""
    LIST_TOOLS = "tools/list"
    EXECUTE_TOOL = "tools/execute"
    LIST_RESOURCES = "resources/list"
    GET_RESOURCE = "resources/get"
    HEALTH_CHECK = "health/check"

@dataclass
class MCPServiceConfig:
    """Configuration for MCP service connection"""
    name: str
    url: str
    timeout: int = 30
    max_retries: int = 3
    auth_token: Optional[str] = None
    feature_flags: Dict[str, bool] = None

class MCPClient:
    """Low-level MCP protocol client"""

    def __init__(self, config: MCPServiceConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._tools_cache: Dict[str, Dict] = {}
        self._connection_pool: List[aiohttp.ClientSession] = []

    async def connect(self):
        """Initialize connection to MCP service"""
        if not self.session:
            headers = {"Content-Type": "application/json"}
            if self.config.auth_token:
                headers["Authorization"] = f"Bearer {self.config.auth_token}"

            # Configure connection pooling for better performance
            connector = aiohttp.TCPConnector(
                limit=10,  # Connection pool size
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                keepalive_timeout=60
            )

            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                connector=connector
            )

    async def disconnect(self):
        """Close connection to MCP service"""
        if self.session:
            await self.session.close()
            self.session = None

        # Close any pooled connections
        for session in self._connection_pool:
            await session.close()
        self._connection_pool.clear()

    async def call_method(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute MCP protocol method"""
        if not self.session:
            await self.connect()

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": f"{self.config.name}_{asyncio.get_event_loop().time()}"
        }

        for attempt in range(self.config.max_retries):
            try:
                async with self.session.post(
                    f"{self.config.url}/rpc",
                    json=payload
                ) as response:
                    result = await response.json()

                    if "error" in result:
                        raise MCPError(
                            f"MCP error: {result['error'].get('message', 'Unknown error')}",
                            code=result['error'].get('code', -1)
                        )

                    return result.get("result", {})

            except asyncio.TimeoutError:
                logger.warning(f"Timeout calling {method} on {self.config.name}, attempt {attempt + 1}")
                if attempt == self.config.max_retries - 1:
                    raise
            except Exception as e:
                logger.error(f"Error calling {method} on {self.config.name}: {e}")
                if attempt == self.config.max_retries - 1:
                    raise

        raise MCPError(f"Failed to call {method} after {self.config.max_retries} attempts")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from MCP service"""
        if not self._tools_cache:
            result = await self.call_method(MCPMethod.LIST_TOOLS.value)
            self._tools_cache = {tool['name']: tool for tool in result.get('tools', [])}
        return list(self._tools_cache.values())

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a specific tool on the MCP service"""
        return await self.call_method(
            MCPMethod.EXECUTE_TOOL.value,
            {"name": tool_name, "arguments": arguments}
        )

    async def get_resource(self, resource_uri: str) -> Dict[str, Any]:
        """Get a specific resource from the MCP service"""
        return await self.call_method(
            MCPMethod.GET_RESOURCE.value,
            {"uri": resource_uri}
        )

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources from the MCP service"""
        result = await self.call_method(MCPMethod.LIST_RESOURCES.value)
        return result.get('resources', [])

class AgnosticMCPAgent(Agent, ABC):
    """Base class for AGNO agents that wrap MCP services"""

    def __init__(
        self,
        service_config: MCPServiceConfig,
        memory: Optional[Memory] = None,
        **kwargs
    ):
        self.service_config = service_config
        self.mcp_client = MCPClient(service_config)
        self._initialized = False
        self._last_health_check = 0
        self._health_cache: Optional[Dict[str, Any]] = None

        # Initialize parent Agent class
        super().__init__(
            name=f"{service_config.name}_agent",
            role=self._get_agent_role(),
            tools=self._create_tools(),
            memory=memory,
            **kwargs
        )

    @abstractmethod
    def _get_agent_role(self) -> str:
        """Define the agent's role description"""
        pass

    def _create_tools(self) -> List[Tool]:
        """Create AGNO tools from MCP service capabilities"""
        # This will be populated dynamically from MCP service
        return [
            Tool(
                name=f"{self.service_config.name}_execute",
                description=f"Execute operations on {self.service_config.name} MCP service",
                func=self._execute_mcp_tool
            )
        ]

    async def _execute_mcp_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Generic MCP tool execution wrapper"""
        try:
            result = await self.mcp_client.execute_tool(tool_name, kwargs)
            return {
                "success": True,
                "result": result,
                "service": self.service_config.name,
                "execution_time": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error executing {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "service": self.service_config.name,
                "execution_time": datetime.now().isoformat()
            }

    async def initialize(self):
        """Initialize the agent and discover MCP tools"""
        if self._initialized:
            return

        try:
            await self.mcp_client.connect()

            # Discover and register MCP tools as AGNO tools
            mcp_tools = await self.mcp_client.list_tools()
            for mcp_tool in mcp_tools:
                agno_tool = Tool(
                    name=mcp_tool['name'],
                    description=mcp_tool.get('description', ''),
                    func=lambda **kwargs, tool_name=mcp_tool['name']:
                        self._execute_mcp_tool(tool_name, **kwargs)
                )
                self.register_tool(agno_tool)

            self._initialized = True
            logger.info(f"Initialized {self.name} with {len(mcp_tools)} tools")

        except Exception as e:
            logger.error(f"Failed to initialize {self.name}: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources"""
        await self.mcp_client.disconnect()
        self._initialized = False

    async def health_check(self) -> Dict[str, Any]:
        """Check health of the wrapped MCP service"""
        now = datetime.now().timestamp()
        cache_duration = 60  # Cache health checks for 60 seconds

        if self._health_cache and (now - self._last_health_check) < cache_duration:
            return self._health_cache

        try:
            result = await self.mcp_client.call_method(MCPMethod.HEALTH_CHECK.value)
            health_status = {
                "status": "healthy",
                "service": self.service_config.name,
                "details": result,
                "timestamp": datetime.now().isoformat(),
                "response_time": result.get('response_time', 0)
            }
        except Exception as e:
            health_status = {
                "status": "unhealthy",
                "service": self.service_config.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

        self._health_cache = health_status
        self._last_health_check = now
        return health_status

    async def get_service_info(self) -> Dict[str, Any]:
        """Get information about the MCP service"""
        try:
            tools = await self.mcp_client.list_tools()
            resources = await self.mcp_client.list_resources()

            return {
                "service_name": self.service_config.name,
                "url": self.service_config.url,
                "tools_count": len(tools),
                "resources_count": len(resources),
                "tools": [t['name'] for t in tools],
                "resources": [r['uri'] for r in resources],
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "service_name": self.service_config.name,
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }

    def is_initialized(self) -> bool:
        """Check if the agent is properly initialized"""
        return self._initialized

class MCPError(Exception):
    """MCP protocol error"""
    def __init__(self, message: str, code: int = -1):
        self.code = code
        super().__init__(message)

# Factory function for creating MCP service configurations
def create_mcp_config(
    name: str,
    url: str,
    auth_token: Optional[str] = None,
    timeout: int = 30,
    max_retries: int = 3
) -> MCPServiceConfig:
    """Create a standardized MCP service configuration"""
    return MCPServiceConfig(
        name=name,
        url=url,
        timeout=timeout,
        max_retries=max_retries,
        auth_token=auth_token,
        feature_flags={}
    )

# Utility function for batch operations
async def execute_batch_tools(
    agent: AgnosticMCPAgent,
    tool_calls: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Execute multiple tools in batch for better performance"""
    tasks = []
    for call in tool_calls:
        tool_name = call.get('tool_name')
        arguments = call.get('arguments', {})
        tasks.append(agent._execute_mcp_tool(tool_name, **arguments))

    return await asyncio.gather(*tasks, return_exceptions=True)