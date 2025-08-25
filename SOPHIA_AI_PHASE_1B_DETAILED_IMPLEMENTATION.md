# Sophia AI Phase 1B: MCP Service Wrappers - Detailed Implementation Plan

**Date**: August 25, 2025  
**Duration**: 2 Weeks (Weeks 3-4)  
**Priority**: HIGH - Following Phase 1A  
**Goal**: Create AGNO-compatible agent wrappers around existing MCP services to enable seamless integration

## Executive Summary

Phase 1B focuses on creating AGNO-compatible wrappers for all existing MCP services without disrupting their current functionality. This phase implements the "wrap, don't replace" strategy, allowing the AGNO Coordinator to interface with existing services through agent abstractions while preserving the stability of production services.

### Key Objectives
1. Create Python-based AGNO agent wrappers for each MCP service
2. Implement service-specific agent capabilities and tools
3. Establish communication protocols between AGNO and MCP services
4. Enable gradual migration path with feature flag control
5. Maintain zero downtime and full backwards compatibility

## Service Mapping Strategy

### Current MCP Services to Wrap

| MCP Service | AGNO Agent Role | Primary Capabilities | Integration Priority |
|-------------|-----------------|---------------------|---------------------|
| `mcp-agents` | TaskPlanner, ServiceRouter | Swarm management, task delegation | Critical |
| `mcp-context` | ContextManager, MemoryAgent | Document processing, embeddings | Critical |
| `mcp-research` | WebResearcher, DataAnalyst | Web search, data analysis | High |
| `mcp-business` | SalesCoach, ClientHealth | CRM integration, analytics | High |
| `mcp-github` | CodeAnalyzer, GitAgent | Code analysis, repo management | Medium |
| `mcp-hubspot` | CRMAgent, LeadManager | HubSpot integration | Medium |
| `mcp-lambda` | InfraAgent, ResourceManager | Infrastructure management | Low |
| `mcp-repo` | RepoManager, FileAgent | Repository operations | Low |

## Week 3: Core Wrapper Implementation

### Day 1-2: Base AGNO Wrapper Framework

#### 3.1 Base MCP Agent Wrapper Class
```python
# services/agno-wrappers/src/base/mcp_wrapper.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic
from dataclasses import dataclass
import asyncio
import aiohttp
import json
from enum import Enum

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
        
    async def connect(self):
        """Initialize connection to MCP service"""
        if not self.session:
            headers = {"Content-Type": "application/json"}
            if self.config.auth_token:
                headers["Authorization"] = f"Bearer {self.config.auth_token}"
                
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
            
    async def disconnect(self):
        """Close connection to MCP service"""
        if self.session:
            await self.session.close()
            self.session = None
            
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
                "service": self.service_config.name
            }
        except Exception as e:
            logger.error(f"Error executing {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "service": self.service_config.name
            }
            
    async def initialize(self):
        """Initialize the agent and discover MCP tools"""
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
            
        logger.info(f"Initialized {self.name} with {len(mcp_tools)} tools")
        
    async def cleanup(self):
        """Cleanup resources"""
        await self.mcp_client.disconnect()
        
    async def health_check(self) -> Dict[str, Any]:
        """Check health of the wrapped MCP service"""
        try:
            result = await self.mcp_client.call_method(MCPMethod.HEALTH_CHECK.value)
            return {
                "status": "healthy",
                "service": self.service_config.name,
                "details": result
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": self.service_config.name,
                "error": str(e)
            }

class MCPError(Exception):
    """MCP protocol error"""
    def __init__(self, message: str, code: int = -1):
        self.code = code
        super().__init__(message)
```

### Day 3: Critical Service Wrappers

#### 3.2 MCP-Context Agent Wrapper
```python
# services/agno-wrappers/src/agents/context_agent.py
from typing import Dict, Any, List, Optional
import hashlib
from datetime import datetime

from ..base.mcp_wrapper import AgnosticMCPAgent, MCPServiceConfig
from agno import Context, Memory
from agno.tools import tool

class ContextManagerAgent(AgnosticMCPAgent):
    """AGNO wrapper for mcp-context service"""
    
    def __init__(self, service_config: MCPServiceConfig, memory: Optional[Memory] = None):
        super().__init__(service_config, memory)
        self.context_cache = {}
        self.embedding_cache = {}
        
    def _get_agent_role(self) -> str:
        return """I am a Context Manager agent responsible for:
        - Processing and indexing documents
        - Managing conversation context
        - Generating and retrieving embeddings
        - Maintaining semantic search capabilities
        - Quality assessment of documents
        """
        
    @tool("process_document")
    async def process_document(
        self,
        content: str,
        doc_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a document and extract context"""
        doc_id = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        result = await self._execute_mcp_tool(
            "process_document",
            content=content,
            doc_type=doc_type,
            metadata=metadata or {},
            doc_id=doc_id
        )
        
        if result["success"]:
            # Cache the processed context
            self.context_cache[doc_id] = {
                "content": content,
                "processed": result["result"],
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata
            }
            
        return result
        
    @tool("search_context")
    async def search_context(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search for relevant context using embeddings"""
        # Check cache first
        cache_key = f"{query}:{limit}:{str(filters)}"
        if cache_key in self.embedding_cache:
            cached_result = self.embedding_cache[cache_key]
            if self._is_cache_valid(cached_result["timestamp"]):
                return {"success": True, "result": cached_result["results"]}
                
        # Call MCP service
        result = await self._execute_mcp_tool(
            "search_embeddings",
            query=query,
            limit=limit,
            filters=filters or {}
        )
        
        if result["success"]:
            # Cache the search results
            self.embedding_cache[cache_key] = {
                "results": result["result"],
                "timestamp": datetime.now().isoformat()
            }
            
        return result
        
    @tool("assess_quality")
    async def assess_document_quality(
        self,
        content: str,
        criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Assess the quality of a document"""
        default_criteria = [
            "relevance",
            "accuracy",
            "completeness",
            "clarity",
            "source_reliability"
        ]
        
        return await self._execute_mcp_tool(
            "assess_quality",
            content=content,
            criteria=criteria or default_criteria
        )
        
    @tool("update_context")
    async def update_conversation_context(
        self,
        conversation_id: str,
        new_messages: List[Dict[str, str]],
        max_context_length: int = 4000
    ) -> Dict[str, Any]:
        """Update conversation context with new messages"""
        return await self._execute_mcp_tool(
            "update_context",
            conversation_id=conversation_id,
            messages=new_messages,
            max_length=max_context_length
        )
        
    def _is_cache_valid(self, timestamp: str, max_age_seconds: int = 300) -> bool:
        """Check if cached data is still valid"""
        cached_time = datetime.fromisoformat(timestamp)
        age = (datetime.now() - cached_time).total_seconds()
        return age < max_age_seconds
```

#### 3.3 MCP-Agents Swarm Manager Wrapper
```python
# services/agno-wrappers/src/agents/swarm_agent.py
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import asyncio

from ..base.mcp_wrapper import AgnosticMCPAgent, MCPServiceConfig
from agno import Team, Agent, Context
from agno.tools import tool

class TaskType(Enum):
    RESEARCH = "research"
    ANALYSIS = "analysis"
    CODING = "coding"
    BUSINESS = "business"
    CREATIVE = "creative"

class SwarmManagerAgent(AgnosticMCPAgent):
    """AGNO wrapper for mcp-agents swarm management"""
    
    def __init__(self, service_config: MCPServiceConfig):
        super().__init__(service_config)
        self.active_swarms: Dict[str, Dict[str, Any]] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        
    def _get_agent_role(self) -> str:
        return """I am a Swarm Manager agent responsible for:
        - Creating and managing agent swarms
        - Delegating tasks to appropriate agents
        - Coordinating multi-agent workflows
        - Monitoring swarm performance
        - Optimizing resource allocation
        """
        
    @tool("create_swarm")
    async def create_swarm(
        self,
        task_type: TaskType,
        agents_needed: List[str],
        objective: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new agent swarm for a specific task"""
        swarm_id = f"swarm_{task_type.value}_{len(self.active_swarms)}"
        
        # Request swarm creation from MCP service
        result = await self._execute_mcp_tool(
            "create_swarm",
            swarm_type=task_type.value,
            agents=agents_needed,
            objective=objective,
            constraints=constraints or {}
        )
        
        if result["success"]:
            self.active_swarms[swarm_id] = {
                "id": swarm_id,
                "type": task_type,
                "agents": agents_needed,
                "objective": objective,
                "status": "active",
                "created_at": datetime.now().isoformat()
            }
            
            # Start monitoring the swarm
            asyncio.create_task(self._monitor_swarm(swarm_id))
            
        return result
        
    @tool("delegate_task")
    async def delegate_task(
        self,
        task: str,
        task_type: TaskType,
        priority: int = 5,
        deadline: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delegate a task to the appropriate agent or swarm"""
        # Analyze task requirements
        analysis = await self._analyze_task_requirements(task, task_type)
        
        # Find or create appropriate swarm
        swarm_id = await self._find_suitable_swarm(analysis)
        if not swarm_id:
            swarm_result = await self.create_swarm(
                task_type=task_type,
                agents_needed=analysis["required_agents"],
                objective=task
            )
            if not swarm_result["success"]:
                return swarm_result
            swarm_id = swarm_result["result"]["swarm_id"]
            
        # Delegate to swarm
        return await self._execute_mcp_tool(
            "delegate_to_swarm",
            swarm_id=swarm_id,
            task=task,
            priority=priority,
            deadline=deadline
        )
        
    @tool("get_swarm_status")
    async def get_swarm_status(self, swarm_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of a specific swarm or all active swarms"""
        if swarm_id:
            return await self._execute_mcp_tool(
                "get_swarm_status",
                swarm_id=swarm_id
            )
        else:
            # Get status of all swarms
            statuses = {}
            for sid in self.active_swarms:
                result = await self._execute_mcp_tool(
                    "get_swarm_status",
                    swarm_id=sid
                )
                if result["success"]:
                    statuses[sid] = result["result"]
            return {"success": True, "result": statuses}
            
    async def _analyze_task_requirements(
        self,
        task: str,
        task_type: TaskType
    ) -> Dict[str, Any]:
        """Analyze what agents are needed for a task"""
        # Use MCP service to analyze requirements
        result = await self._execute_mcp_tool(
            "analyze_task",
            task=task,
            task_type=task_type.value
        )
        
        if result["success"]:
            return result["result"]
        else:
            # Fallback to basic analysis
            return self._basic_task_analysis(task, task_type)
            
    def _basic_task_analysis(self, task: str, task_type: TaskType) -> Dict[str, Any]:
        """Basic fallback task analysis"""
        agent_mapping = {
            TaskType.RESEARCH: ["researcher", "analyst", "summarizer"],
            TaskType.ANALYSIS: ["analyst", "visualizer", "reporter"],
            TaskType.CODING: ["architect", "developer", "reviewer"],
            TaskType.BUSINESS: ["strategist", "analyst", "communicator"],
            TaskType.CREATIVE: ["ideator", "designer", "reviewer"]
        }
        
        return {
            "required_agents": agent_mapping.get(task_type, ["generalist"]),
            "complexity": "medium",
            "estimated_duration": "30m"
        }
        
    async def _find_suitable_swarm(self, requirements: Dict[str, Any]) -> Optional[str]:
        """Find an existing swarm that can handle the requirements"""
        required_agents = set(requirements["required_agents"])
        
        for swarm_id, swarm_info in self.active_swarms.items():
            if swarm_info["status"] != "active":
                continue
                
            swarm_agents = set(swarm_info["agents"])
            if required_agents.issubset(swarm_agents):
                # Check if swarm has capacity
                status = await self.get_swarm_status(swarm_id)
                if status["success"] and status["result"]["capacity"] > 0:
                    return swarm_id
                    
        return None
        
    async def _monitor_swarm(self, swarm_id: str):
        """Monitor swarm health and performance"""
        while swarm_id in self.active_swarms:
            try:
                status = await self.get_swarm_status(swarm_id)
                if status["success"]:
                    swarm_status = status["result"]["status"]
                    if swarm_status == "completed":
                        self.active_swarms[swarm_id]["status"] = "completed"
                        break
                    elif swarm_status == "failed":
                        self.active_swarms[swarm_id]["status"] = "failed"
                        await self._handle_swarm_failure(swarm_id)
                        break
                        
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring swarm {swarm_id}: {e}")
                await asyncio.sleep(30)  # Back off on error
```

### Day 4: Business Service Wrappers

#### 3.4 MCP-Research Agent Wrapper
```python
# services/agno-wrappers/src/agents/research_agent.py
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from ..base.mcp_wrapper import AgnosticMCPAgent, MCPServiceConfig
from agno.tools import tool

class ResearchAgent(AgnosticMCPAgent):
    """AGNO wrapper for mcp-research service"""
    
    def __init__(self, service_config: MCPServiceConfig):
        super().__init__(service_config)
        self.research_cache = {}
        self.source_credibility = {}
        
    def _get_agent_role(self) -> str:
        return """I am a Research Agent responsible for:
        - Conducting deep web research
        - Analyzing and synthesizing information
        - Fact-checking and verification
        - Tracking source credibility
        - Producing comprehensive research reports
        """
        
    @tool("research_topic")
    async def research_topic(
        self,
        topic: str,
        depth: str = "standard",  # quick, standard, deep
        sources: Optional[List[str]] = None,
        max_results: int = 20
    ) -> Dict[str, Any]:
        """Conduct research on a specific topic"""
        # Check cache first
        cache_key = f"{topic}:{depth}:{max_results}"
        if cache_key in self.research_cache:
            cached = self.research_cache[cache_key]
            if self._is_recent(cached["timestamp"]):
                return {"success": True, "result": cached["data"]}
                
        # Perform research via MCP
        result = await self._execute_mcp_tool(
            "research",
            query=topic,
            depth=depth,
            sources=sources or ["web", "academic", "news"],
            max_results=max_results
        )
        
        if result["success"]:
            # Process and enhance results
            enhanced_results = await self._enhance_research_results(
                result["result"],
                topic
            )
            
            # Cache results
            self.research_cache[cache_key] = {
                "data": enhanced_results,
                "timestamp": datetime.now().isoformat()
            }
            
            result["result"] = enhanced_results
            
        return result
        
    @tool("fact_check")
    async def fact_check(
        self,
        claim: str,
        context: Optional[str] = None,
        sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Fact-check a specific claim"""
        result = await self._execute_mcp_tool(
            "fact_check",
            claim=claim,
            context=context,
            sources=sources
        )
        
        if result["success"]:
            # Update source credibility based on fact-check results
            self._update_source_credibility(result["result"])
            
        return result
        
    @tool("analyze_sources")
    async def analyze_sources(
        self,
        sources: List[str],
        criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze the credibility and bias of sources"""
        default_criteria = [
            "credibility",
            "bias",
            "expertise",
            "transparency",
            "track_record"
        ]
        
        return await self._execute_mcp_tool(
            "analyze_sources",
            sources=sources,
            criteria=criteria or default_criteria
        )
        
    @tool("synthesize_findings")
    async def synthesize_findings(
        self,
        findings: List[Dict[str, Any]],
        format: str = "summary",  # summary, report, bullet_points
        max_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """Synthesize multiple research findings into a coherent output"""
        # Pre-process findings
        processed_findings = []
        for finding in findings:
            processed = {
                "content": finding.get("content", ""),
                "source": finding.get("source", "unknown"),
                "credibility": self._get_source_credibility(finding.get("source")),
                "relevance": finding.get("relevance", 0.5),
                "timestamp": finding.get("timestamp", datetime.now().isoformat())
            }
            processed_findings.append(processed)
            
        # Synthesize via MCP
        result = await self._execute_mcp_tool(
            "synthesize",
            findings=processed_findings,
            format=format,
            max_length=max_length
        )
        
        return result
        
    async def _enhance_research_results(
        self,
        results: List[Dict[str, Any]],
        topic: str
    ) -> List[Dict[str, Any]]:
        """Enhance research results with additional analysis"""
        enhanced = []
        
        for result in results:
            # Add credibility score
            source = result.get("source", "unknown")
            credibility = self._get_source_credibility(source)
            
            enhanced_result = {
                **result,
                "credibility_score": credibility,
                "relevance_score": await self._calculate_relevance(
                    result.get("content", ""),
                    topic
                ),
                "analysis": {
                    "key_points": self._extract_key_points(result.get("content", "")),
                    "entities": self._extract_entities(result.get("content", "")),
                    "sentiment": self._analyze_sentiment(result.get("content", ""))
                }
            }
            enhanced.append(enhanced_result)
            
        # Sort by relevance and credibility
        enhanced.sort(
            key=lambda x: (x["relevance_score"] * x["credibility_score"]),
            reverse=True
        )
        
        return enhanced
        
    def _get_source_credibility(self, source: str) -> float:
        """Get credibility score for a source"""
        return self.source_credibility.get(source, 0.7)  # Default to 0.7
        
    def _update_source_credibility(self, fact_check_result: Dict[str, Any]):
        """Update source credibility based on fact-checking results"""
        for source_eval in fact_check_result.get("source_evaluations", []):
            source = source_eval["source"]
            accuracy = source_eval["accuracy"]
            
            # Update credibility using exponential moving average
            current = self.source_credibility.get(source, 0.7)
            self.source_credibility[source] = 0.7 * current + 0.3 * accuracy
            
    def _is_recent(self, timestamp: str, max_age_hours: int = 24) -> bool:
        """Check if cached data is recent enough"""
        cached_time = datetime.fromisoformat(timestamp)
        age_hours = (datetime.now() - cached_time).total_seconds() / 3600
        return age_hours < max_age_hours
        
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content (simplified)"""
        # In production, this would use NLP
        sentences = content.split('.')
        return sentences[:3] if len(sentences) > 3 else sentences
        
    def _extract_entities(self, content: str) -> List[Dict[str, str]]:
        """Extract named entities (simplified)"""
        # In production, this would use NER
        return []
        
    def _analyze_sentiment(self, content: str) -> str:
        """Analyze sentiment (simplified)"""
        # In production, this would use sentiment analysis
        return "neutral"
        
    async def _calculate_relevance(self, content: str, topic: str) -> float:
        """Calculate relevance score (simplified)"""
        # In production, this would use semantic similarity
        topic_words = set(topic.lower().split())
        content_words = set(content.lower().split())
        
        if not topic_words:
            return 0.0
            
        overlap = len(topic_words.intersection(content_words))
        return min(overlap / len(topic_words), 1.0)
```

### Day 5: Infrastructure Service Wrappers

#### 3.5 MCP-Business Agent Wrapper
```python
# services/agno-wrappers/src/agents/business_agent.py
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import statistics

from ..base.mcp_wrapper import AgnosticMCPAgent, MCPServiceConfig
from agno.tools import tool

class BusinessIntelligenceAgent(AgnosticMCPAgent):
    """AGNO wrapper for mcp-business service"""
    
    def __init__(self, service_config: MCPServiceConfig):
        super().__init__(service_config)
        self.metrics_cache = {}
        self.alerts_active = []
        
    def _get_agent_role(self) -> str:
        return """I am a Business Intelligence Agent responsible for:
        - Analyzing sales performance and trends
        - Monitoring client health metrics
        - Generating business insights and recommendations
        - Tracking KPIs and OKRs
        - Providing predictive analytics
        """
        
    @tool("analyze_sales_performance")
    async def analyze_sales_performance(
        self,
