"""
Sophia Brain Context Integration Module
Enhances Sophia Brain with deep context and research awareness
This module should be imported by sophia-brain.py to add enhanced capabilities
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ContextAwareEnhancement:
    """
    Adds context awareness and deep research capabilities to Sophia Brain
    """
    
    def __init__(self, brain_instance):
        self.brain = brain_instance
        self.context_cache = {}
        self.repository_index = {}
        self.active_research_sessions = {}
        
    async def initialize_context_awareness(self):
        """Initialize full context awareness for Sophia Brain"""
        try:
            # Connect to MCP Context Server
            async with aiohttp.ClientSession() as session:
                # Initialize repository indexing
                async with session.post(
                    f"{self.brain.services['context']}/repository-indexer",
                    json={"action": "index", "path": "/workspace"}
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        self.repository_index = result
                        logger.info(f"📁 Repository indexed: {result.get('files_indexed', 0)} files")
                
                # Get initial dashboard context
                async with session.get(
                    f"{self.brain.services['context']}/dashboard-context"
                ) as resp:
                    if resp.status == 200:
                        self.context_cache['dashboard'] = await resp.json()
                        
        except Exception as e:
            logger.error(f"Failed to initialize context awareness: {e}")
    
    async def get_comprehensive_context(self, query: str) -> Dict[str, Any]:
        """Get comprehensive context for query processing"""
        context = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "repository": {},
            "research": {},
            "agents": {},
            "dashboard": {}
        }
        
        async with aiohttp.ClientSession() as session:
            # Get repository context
            try:
                async with session.post(
                    f"{self.brain.services['context']}/search",
                    json={"query": query, "limit": 10}
                ) as resp:
                    if resp.status == 200:
                        context["repository"] = await resp.json()
            except Exception as e:
                logger.warning(f"Could not get repository context: {e}")
            
            # Get research context
            try:
                async with session.post(
                    f"{self.brain.services['research']}/quick-search",
                    json={"query": query, "sources": ["web", "academic", "github"]}
                ) as resp:
                    if resp.status == 200:
                        context["research"] = await resp.json()
            except Exception as e:
                logger.warning(f"Could not get research context: {e}")
            
            # Get agent context
            try:
                async with session.get(
                    f"{self.brain.services['agents']}/available"
                ) as resp:
                    if resp.status == 200:
                        context["agents"] = await resp.json()
            except Exception as e:
                logger.warning(f"Could not get agent context: {e}")
        
        return context
    
    async def perform_deep_research(self, topic: str, depth: str = "comprehensive") -> Dict[str, Any]:
        """Perform deep research with context awareness"""
        research_session_id = f"research_{datetime.utcnow().timestamp()}"
        
        async with aiohttp.ClientSession() as session:
            # Start deep research
            research_request = {
                "topic": topic,
                "depth": depth,
                "include_code": True,
                "include_papers": True,
                "include_repos": True,
                "context": await self.get_comprehensive_context(topic)
            }
            
            async with session.post(
                f"{self.brain.services['research']}/deep-research",
                json=research_request
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    self.active_research_sessions[research_session_id] = result
                    return result
                    
        return {"error": "Research failed"}
    
    async def deploy_context_aware_swarm(self, task: str, swarm_type: str = "auto") -> Dict[str, Any]:
        """Deploy agent swarm with full context awareness"""
        # Get comprehensive context for the task
        context = await self.get_comprehensive_context(task)
        
        # Determine optimal swarm configuration based on context
        if swarm_type == "auto":
            swarm_type = self.determine_optimal_swarm_type(task, context)
        
        swarm_config = {
            "type": swarm_type,
            "task": task,
            "context": context,
            "agents": []
        }
        
        # Configure agents based on swarm type
        if swarm_type == "coding":
            swarm_config["agents"] = [
                {"type": "architect", "role": "Design system architecture"},
                {"type": "developer", "role": "Implement code", "count": 3},
                {"type": "reviewer", "role": "Review and optimize code"}
            ]
        elif swarm_type == "research":
            swarm_config["agents"] = [
                {"type": "coordinator", "role": "Coordinate research"},
                {"type": "researcher", "role": "Deep web research", "count": 2},
                {"type": "analyst", "role": "Analyze findings"}
            ]
        elif swarm_type == "analysis":
            swarm_config["agents"] = [
                {"type": "data_processor", "role": "Process data"},
                {"type": "pattern_detector", "role": "Detect patterns"},
                {"type": "insight_generator", "role": "Generate insights"}
            ]
        
        # Deploy swarm via coordinator
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.brain.services['coordinator']}/deploy-swarm",
                json=swarm_config
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
        
        return {"error": "Swarm deployment failed"}
    
    def determine_optimal_swarm_type(self, task: str, context: Dict) -> str:
        """Determine optimal swarm type based on task and context"""
        task_lower = task.lower()
        
        # Check for coding indicators
        if any(word in task_lower for word in ["code", "implement", "function", "class", "api", "frontend", "backend"]):
            return "coding"
        
        # Check for research indicators
        if any(word in task_lower for word in ["research", "find", "search", "investigate", "explore"]):
            return "research"
        
        # Check for analysis indicators
        if any(word in task_lower for word in ["analyze", "data", "pattern", "insight", "trend"]):
            return "analysis"
        
        # Default to coding if repository context suggests it
        if context.get("repository", {}).get("files_found", 0) > 0:
            return "coding"
        
        return "research"
    
    async def search_codebase_with_ai(self, query: str) -> Dict[str, Any]:
        """AI-powered codebase search with semantic understanding"""
        async with aiohttp.ClientSession() as session:
            # Use repository indexer for semantic search
            search_request = {
                "query": query,
                "semantic": True,
                "include_symbols": True,
                "include_dependencies": True
            }
            
            async with session.post(
                f"{self.brain.services['context']}/semantic-search",
                json=search_request
            ) as resp:
                if resp.status == 200:
                    results = await resp.json()
                    
                    # Enhance results with AI analysis
                    enhanced_results = {
                        "files": results.get("files", []),
                        "symbols": results.get("symbols", []),
                        "dependencies": results.get("dependencies", []),
                        "ai_summary": self.generate_search_summary(query, results)
                    }
                    
                    return enhanced_results
        
        return {"error": "Search failed"}
    
    def generate_search_summary(self, query: str, results: Dict) -> str:
        """Generate AI summary of search results"""
        num_files = len(results.get("files", []))
        num_symbols = len(results.get("symbols", []))
        
        if num_files == 0:
            return f"No results found for '{query}' in the codebase."
        
        summary = f"Found {num_files} files and {num_symbols} symbols related to '{query}'."
        
        # Add top files
        if results.get("files"):
            top_files = results["files"][:3]
            file_list = ", ".join([f["path"] for f in top_files])
            summary += f"\nMost relevant files: {file_list}"
        
        # Add top symbols
        if results.get("symbols"):
            top_symbols = results["symbols"][:3]
            symbol_list = ", ".join([f"{s['name']} ({s['type']})" for s in top_symbols])
            summary += f"\nKey symbols: {symbol_list}"
        
        return summary
    
    async def update_dashboard_context(self, component: str, state: Dict):
        """Update dashboard context in real-time"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.brain.services['context']}/dashboard-update",
                json={"component": component, "state": state}
            ) as resp:
                if resp.status == 200:
                    logger.info(f"📊 Dashboard context updated: {component}")


def enhance_sophia_brain(brain_instance):
    """
    Enhance existing Sophia Brain with context awareness
    Call this from sophia-brain.py to add enhanced capabilities
    """
    enhancement = ContextAwareEnhancement(brain_instance)
    
    # Add methods to brain instance
    brain_instance.get_comprehensive_context = enhancement.get_comprehensive_context
    brain_instance.perform_deep_research = enhancement.perform_deep_research
    brain_instance.deploy_context_aware_swarm = enhancement.deploy_context_aware_swarm
    brain_instance.search_codebase_with_ai = enhancement.search_codebase_with_ai
    brain_instance.update_dashboard_context = enhancement.update_dashboard_context
    
    # Initialize context awareness
    asyncio.create_task(enhancement.initialize_context_awareness())
    
    logger.info("✨ Sophia Brain enhanced with context awareness")
    
    return brain_instance


# Agent Swarm Templates for quick deployment
SWARM_TEMPLATES = {
    "full_stack_development": {
        "name": "Full Stack Development Swarm",
        "agents": [
            {"type": "frontend_architect", "capabilities": ["React", "Vue", "UI/UX"]},
            {"type": "backend_architect", "capabilities": ["FastAPI", "Django", "Node.js"]},
            {"type": "database_designer", "capabilities": ["PostgreSQL", "MongoDB", "Redis"]},
            {"type": "devops_engineer", "capabilities": ["Docker", "Kubernetes", "CI/CD"]},
            {"type": "security_analyst", "capabilities": ["Security", "Authentication", "Encryption"]},
            {"type": "code_reviewer", "capabilities": ["Best practices", "Performance", "Testing"]}
        ]
    },
    "research_and_analysis": {
        "name": "Research and Analysis Swarm",
        "agents": [
            {"type": "research_coordinator", "capabilities": ["Planning", "Synthesis"]},
            {"type": "web_researcher", "capabilities": ["Web search", "Data extraction"]},
            {"type": "academic_researcher", "capabilities": ["Papers", "Citations"]},
            {"type": "github_researcher", "capabilities": ["Code search", "Repository analysis"]},
            {"type": "data_analyst", "capabilities": ["Statistics", "Visualization"]},
            {"type": "report_generator", "capabilities": ["Documentation", "Presentation"]}
        ]
    },
    "ai_ml_development": {
        "name": "AI/ML Development Swarm",
        "agents": [
            {"type": "ml_architect", "capabilities": ["Model design", "Architecture"]},
            {"type": "data_engineer", "capabilities": ["Data pipeline", "Processing"]},
            {"type": "model_trainer", "capabilities": ["Training", "Optimization"]},
            {"type": "evaluation_specialist", "capabilities": ["Metrics", "Validation"]},
            {"type": "deployment_engineer", "capabilities": ["Model serving", "Scaling"]},
            {"type": "monitor", "capabilities": ["Performance", "Drift detection"]}
        ]
    },
    "bug_fixing": {
        "name": "Bug Fixing Swarm",
        "agents": [
            {"type": "bug_detector", "capabilities": ["Error analysis", "Log parsing"]},
            {"type": "root_cause_analyst", "capabilities": ["Debugging", "Tracing"]},
            {"type": "fix_implementer", "capabilities": ["Code fixes", "Patches"]},
            {"type": "test_generator", "capabilities": ["Test cases", "Regression tests"]},
            {"type": "verifier", "capabilities": ["Validation", "Confirmation"]}
        ]
    }
}


async def get_swarm_template(template_name: str) -> Dict[str, Any]:
    """Get a predefined swarm template"""
    return SWARM_TEMPLATES.get(template_name, {})