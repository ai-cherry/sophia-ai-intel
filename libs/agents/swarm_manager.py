"""
Sophia AI Agent Swarm Manager

Central management system for the Sophia AI agent swarm ecosystem.
Coordinates agents, manages workflows, and provides integration with the chat interface.

Key Features:
- Agent lifecycle management
- Task routing and coordination
- Integration with LangGraph workflows  
- Chat interface connectivity
- Monitoring and metrics
- Human approval workflows

Version: 1.0.0
Author: Sophia AI Intelligence Team
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

from .base_agent import SophiaAgent, AgentTask, TaskStatus, TaskPriority, AgentRole
from .communication import message_bus
from .code_kraken.orchestrator import CodeKrakenOrchestrator
from .code_kraken.planners import (
    create_cutting_edge_planner, 
    create_conservative_planner, 
    create_synthesis_planner
)
from .repository_agent import create_repository_analyst
from .embedding.embedding_engine import EmbeddingEngine
from .embedding.rag_pipeline import create_rag_pipeline

logger = logging.getLogger(__name__)


@dataclass
class SwarmConfiguration:
    """Configuration for the agent swarm"""
    max_concurrent_workflows: int = 5
    default_timeout_seconds: int = 1800
    enable_human_approval: bool = True
    embedding_model: str = "all-mpnet-base-v2"
    llm_models: Dict[str, str] = None
    cache_ttl_hours: int = 24
    
    def __post_init__(self):
        if self.llm_models is None:
            self.llm_models = {
                'cutting_edge': 'gpt-5',
                'conservative': 'claude-3.5-sonnet',
                'synthesis': 'gpt-5',
                'repository': 'gpt-4o',
                'default': 'gpt-5'
            }


@dataclass
class SwarmTaskRequest:
    """Request for swarm task execution"""
    task_description: str
    task_type: str
    priority: str = "medium"
    context: Dict[str, Any] = None
    user_id: Optional[str] = None
    chat_session_id: Optional[str] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


@dataclass
class SwarmTaskResult:
    """Result from swarm task execution"""
    task_id: str
    status: str
    result: Dict[str, Any]
    error: Optional[str]
    workflow_id: Optional[str]
    processing_time_ms: float
    agents_involved: List[str]
    created_at: datetime
    completed_at: Optional[datetime]


class SophiaAgentSwarmManager:
    """
    Main manager for the Sophia AI agent swarm system
    """
    
    def __init__(
        self,
        config: SwarmConfiguration,
        mcp_clients: Dict[str, Any]
    ):
        self.config = config
        self.mcp_clients = mcp_clients
        
        # Agent registry
        self.agents: Dict[str, SophiaAgent] = {}
        self.orchestrator: Optional[CodeKrakenOrchestrator] = None
        
        # Task management
        self.active_tasks: Dict[str, SwarmTaskResult] = {}
        self.task_history: List[SwarmTaskResult] = []
        
        # Components
        self.embedding_engine: Optional[EmbeddingEngine] = None
        self.rag_pipeline: Optional[Any] = None
        
        # State
        self.is_initialized = False
        self.initialization_error: Optional[str] = None

    async def initialize(self) -> bool:
        """Initialize the agent swarm system"""
        try:
            logger.info("Initializing Sophia Agent Swarm Manager")
            
            # Initialize embedding engine
            self.embedding_engine = EmbeddingEngine(
                embedding_model=self.config.embedding_model
            )
            logger.info("Embedding engine initialized")
            
            # Initialize RAG pipeline
            self.rag_pipeline = create_rag_pipeline(
                embedding_model=self.config.embedding_model,
                mcp_clients=self.mcp_clients
            )
            logger.info("RAG pipeline initialized")
            
            # Create and register agents
            await self._create_agents()
            logger.info(f"Created {len(self.agents)} agents")
            
            # Initialize orchestrator
            self.orchestrator = CodeKrakenOrchestrator(
                agents=self.agents,
                max_retries=3,
                timeout_seconds=self.config.default_timeout_seconds
            )
            logger.info("CodeKraken orchestrator initialized")
            
            # Register all agents with message bus
            for agent in self.agents.values():
                await message_bus.register_agent(agent)
            
            self.is_initialized = True
            logger.info("Sophia Agent Swarm Manager initialization completed")
            return True
            
        except Exception as e:
            self.initialization_error = str(e)
            logger.error(f"Failed to initialize agent swarm: {e}")
            return False

    async def _create_agents(self):
        """Create and configure all agents"""
        base_llm_config = {
            'temperature': 0.7,
            'max_tokens': 2000,
            'timeout_seconds': 30
        }
        
        # Repository Analyst Agent
        repo_analyst = create_repository_analyst(
            agent_id=f"repo_analyst_{uuid.uuid4().hex[:8]}",
            llm_config={**base_llm_config, 'model': self.config.llm_models['repository']},
            mcp_clients=self.mcp_clients,
            embedding_model=self.config.embedding_model
        )
        self.agents[repo_analyst.agent_id] = repo_analyst
        logger.info(f"Created Repository Analyst: {repo_analyst.agent_id}")
        
        # Cutting-Edge Planner
        cutting_edge_planner = create_cutting_edge_planner(
            agent_id=f"cutting_edge_{uuid.uuid4().hex[:8]}",
            llm_config={**base_llm_config, 'model': self.config.llm_models['cutting_edge']},
            mcp_clients=self.mcp_clients,
            rag_pipeline=self.rag_pipeline
        )
        self.agents[cutting_edge_planner.agent_id] = cutting_edge_planner
        logger.info(f"Created Cutting-Edge Planner: {cutting_edge_planner.agent_id}")
        
        # Conservative Planner
        conservative_planner = create_conservative_planner(
            agent_id=f"conservative_{uuid.uuid4().hex[:8]}",
            llm_config={**base_llm_config, 'model': self.config.llm_models['conservative']},
            mcp_clients=self.mcp_clients,
            rag_pipeline=self.rag_pipeline
        )
        self.agents[conservative_planner.agent_id] = conservative_planner
        logger.info(f"Created Conservative Planner: {conservative_planner.agent_id}")
        
        # Synthesis Planner
        synthesis_planner = create_synthesis_planner(
            agent_id=f"synthesis_{uuid.uuid4().hex[:8]}",
            llm_config={**base_llm_config, 'model': self.config.llm_models['synthesis']},
            mcp_clients=self.mcp_clients,
            rag_pipeline=self.rag_pipeline
        )
        self.agents[synthesis_planner.agent_id] = synthesis_planner
        logger.info(f"Created Synthesis Planner: {synthesis_planner.agent_id}")

    async def create_task_from_chat(self, chat_message: str, user_context: Dict[str, Any] = None) -> str:
        """Create a swarm task from chat message"""
        if not self.is_initialized:
            raise RuntimeError("Swarm manager not initialized")
        
        # Parse chat message to determine task type and requirements
        task_info = await self._parse_chat_message(chat_message, user_context or {})
        
        # Create swarm task
        task_request = SwarmTaskRequest(
            task_description=task_info['description'],
            task_type=task_info['type'],
            priority=task_info.get('priority', 'medium'),
            context=task_info.get('context', {}),
            user_id=user_context.get('user_id'),
            chat_session_id=user_context.get('session_id')
        )
        
        # Execute task
        task_id = await self.execute_task(task_request)
        
        return task_id

    async def execute_task(self, task_request: SwarmTaskRequest) -> str:
        """Execute a task using the agent swarm"""
        task_id = str(uuid.uuid4())
        
        # Create task result tracking
        task_result = SwarmTaskResult(
            task_id=task_id,
            status="running",
            result={},
            error=None,
            workflow_id=None,
            processing_time_ms=0,
            agents_involved=[],
            created_at=datetime.now(),
            completed_at=None
        )
        
        self.active_tasks[task_id] = task_result
        
        try:
            start_time = datetime.now()
            
            # Convert to agent task
            agent_task = AgentTask(
                id=task_id,
                title=f"Swarm Task: {task_request.task_description[:50]}...",
                description=task_request.task_description,
                task_type=task_request.task_type,
                priority=self._convert_priority(task_request.priority),
                status=TaskStatus.PENDING,
                created_at=datetime.now(),
                context=task_request.context
            )
            
            # Execute based on task type
            if task_request.task_type in ['repository_analysis', 'code_analysis']:
                result = await self._execute_repository_task(agent_task)
            elif task_request.task_type in ['code_generation', 'feature_implementation', 'bug_fix']:
                result = await self._execute_code_generation_workflow(agent_task)
            elif task_request.task_type in ['planning', 'architecture_design']:
                result = await self._execute_planning_task(agent_task)
            else:
                # Default to repository analysis
                result = await self._execute_repository_task(agent_task)
            
            # Update task result
            end_time = datetime.now()
            task_result.status = "completed"
            task_result.result = result
            task_result.processing_time_ms = (end_time - start_time).total_seconds() * 1000
            task_result.completed_at = end_time
            
            # Move to history
            self.task_history.append(task_result)
            if len(self.task_history) > 100:  # Keep last 100 tasks
                self.task_history = self.task_history[-100:]
            
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            task_result.status = "failed"
            task_result.error = str(e)
            task_result.completed_at = datetime.now()
            logger.error(f"Task {task_id} failed: {e}")
        
        return task_id

    async def _execute_repository_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute repository analysis task"""
        # Find repository analyst
        repo_analyst = self._find_agent_by_role(AgentRole.REPOSITORY_ANALYST)
        if not repo_analyst:
            raise RuntimeError("Repository analyst not available")
        
        # Execute task
        completed_task = await repo_analyst.process_task(task)
        
        if completed_task.status == TaskStatus.COMPLETED:
            return completed_task.result
        else:
            raise RuntimeError(f"Repository analysis failed: {completed_task.error}")

    async def _execute_code_generation_workflow(self, task: AgentTask) -> Dict[str, Any]:
        """Execute full code generation workflow using orchestrator"""
        if not self.orchestrator:
            raise RuntimeError("CodeKraken orchestrator not available")
        
        # Execute workflow
        workflow_result = await self.orchestrator.execute_workflow(task)
        
        if workflow_result.status.value == "completed":
            return {
                "workflow_result": asdict(workflow_result),
                "generated_code": workflow_result.final_output.get('generated_code') if workflow_result.final_output else None
            }
        else:
            raise RuntimeError(f"Workflow failed: {', '.join(workflow_result.errors)}")

    async def _execute_planning_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute planning task using multiple planners"""
        planners = [
            self._find_agent_by_role(AgentRole.TASK_PLANNER, name_contains="cutting"),
            self._find_agent_by_role(AgentRole.TASK_PLANNER, name_contains="conservative"),
            self._find_agent_by_role(AgentRole.TASK_PLANNER, name_contains="synthesis")
        ]
        
        planners = [p for p in planners if p is not None]
        
        if not planners:
            raise RuntimeError("No planning agents available")
        
        # Execute planning with all available planners
        planning_results = []
        for planner in planners:
            try:
                plan_task = AgentTask(
                    id=f"plan_{task.id}_{planner.name.replace(' ', '_').lower()}",
                    title=f"Planning: {task.title}",
                    description=task.description,
                    task_type="task_planning",
                    priority=task.priority,
                    status=TaskStatus.PENDING,
                    created_at=datetime.now(),
                    context=task.context
                )
                
                completed_plan = await planner.process_task(plan_task)
                if completed_plan.status == TaskStatus.COMPLETED:
                    planning_results.append({
                        'planner': planner.name,
                        'plan': completed_plan.result
                    })
                    
            except Exception as e:
                logger.warning(f"Planning failed for {planner.name}: {e}")
        
        return {
            "planning_results": planning_results,
            "total_plans": len(planning_results)
        }

    async def _parse_chat_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse chat message to determine task requirements"""
        message_lower = message.lower()
        
        # Determine task type
        if any(keyword in message_lower for keyword in ['analyze', 'analysis', 'review', 'examine']):
            task_type = "repository_analysis"
        elif any(keyword in message_lower for keyword in ['code', 'implement', 'build', 'create', 'generate']):
            task_type = "code_generation"
        elif any(keyword in message_lower for keyword in ['plan', 'design', 'architecture']):
            task_type = "planning"
        else:
            task_type = "repository_analysis"  # Default
        
        # Determine priority
        if any(keyword in message_lower for keyword in ['urgent', 'critical', 'asap']):
            priority = "high"
        elif any(keyword in message_lower for keyword in ['low', 'minor', 'small']):
            priority = "low"
        else:
            priority = "medium"
        
        return {
            'description': message,
            'type': task_type,
            'priority': priority,
            'context': {
                'original_message': message,
                'parsed_keywords': self._extract_keywords(message),
                'user_context': context
            }
        }

    def _extract_keywords(self, message: str) -> List[str]:
        """Extract technical keywords from message"""
        # Technical terms that might be relevant
        tech_keywords = [
            'api', 'database', 'service', 'function', 'class', 'method',
            'test', 'bug', 'error', 'performance', 'security', 'deploy',
            'refactor', 'optimize', 'documentation', 'pattern'
        ]
        
        message_lower = message.lower()
        found_keywords = []
        
        for keyword in tech_keywords:
            if keyword in message_lower:
                found_keywords.append(keyword)
        
        return found_keywords

    def _convert_priority(self, priority_str: str) -> TaskPriority:
        """Convert string priority to TaskPriority enum"""
        priority_map = {
            'low': TaskPriority.LOW,
            'medium': TaskPriority.MEDIUM,
            'high': TaskPriority.HIGH,
            'critical': TaskPriority.CRITICAL
        }
        
        return priority_map.get(priority_str.lower(), TaskPriority.MEDIUM)

    def _find_agent_by_role(self, role: AgentRole, name_contains: Optional[str] = None) -> Optional[SophiaAgent]:
        """Find agent by role and optional name filter"""
        for agent in self.agents.values():
            if hasattr(agent, 'role') and agent.role == role:
                if name_contains is None or name_contains.lower() in agent.name.lower():
                    return agent
        return None

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                'task_id': task.task_id,
                'status': task.status,
                'created_at': task.created_at.isoformat(),
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'processing_time_ms': task.processing_time_ms,
                'agents_involved': task.agents_involved,
                'has_result': bool(task.result),
                'error': task.error
            }
        
        # Check history
        for historical_task in self.task_history:
            if historical_task.task_id == task_id:
                return {
                    'task_id': historical_task.task_id,
                    'status': historical_task.status,
                    'created_at': historical_task.created_at.isoformat(),
                    'completed_at': historical_task.completed_at.isoformat() if historical_task.completed_at else None,
                    'processing_time_ms': historical_task.processing_time_ms,
                    'agents_involved': historical_task.agents_involved,
                    'result': historical_task.result,
                    'error': historical_task.error
                }
        
        return None

    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed result of a completed task"""
        # Check active tasks
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            if task.status == "completed":
                return task.result
            elif task.status == "failed":
                return {"error": task.error}
            else:
                return {"status": task.status, "message": "Task still in progress"}
        
        # Check history
        for historical_task in self.task_history:
            if historical_task.task_id == task_id:
                if historical_task.status == "completed":
                    return historical_task.result
                else:
                    return {"error": historical_task.error}
        
        return None

    async def get_swarm_status(self) -> Dict[str, Any]:
        """Get overall swarm status and metrics"""
        agent_statuses = {}
        for agent_id, agent in self.agents.items():
            agent_statuses[agent_id] = {
                'name': agent.name,
                'role': agent.role.value,
                'is_active': agent.is_active,
                'current_tasks': len(agent.current_tasks)
            }
        
        return {
            'is_initialized': self.is_initialized,
            'initialization_error': self.initialization_error,
            'total_agents': len(self.agents),
            'agent_statuses': agent_statuses,
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len([t for t in self.task_history if t.status == "completed"]),
            'failed_tasks': len([t for t in self.task_history if t.status == "failed"]),
            'orchestrator_available': self.orchestrator is not None,
            'embedding_engine_available': self.embedding_engine is not None,
            'rag_pipeline_available': self.rag_pipeline is not None
        }

    async def get_agent_metrics(self) -> Dict[str, Any]:
        """Get detailed agent metrics"""
        metrics = {}
        
        for agent_id, agent in self.agents.items():
            agent_status = await agent.get_status()
            metrics[agent_id] = agent_status
        
        return metrics

    async def shutdown(self):
        """Shutdown the agent swarm gracefully"""
        logger.info("Shutting down Sophia Agent Swarm Manager")
        
        # Stop all agents
        for agent in self.agents.values():
            try:
                await agent.stop()
            except Exception as e:
                logger.error(f"Error stopping agent {agent.name}: {e}")
        
        # Clear active tasks
        for task_result in self.active_tasks.values():
            if task_result.status == "running":
                task_result.status = "cancelled"
                task_result.error = "System shutdown"
                task_result.completed_at = datetime.now()
        
        self.is_initialized = False
        logger.info("Agent swarm shutdown completed")

    async def process_human_approval(self, workflow_id: str, approved: bool, comments: Optional[str] = None) -> bool:
        """Process human approval for a workflow"""
        if not self.orchestrator:
            return False
        
        try:
            # This would integrate with the orchestrator's human approval system
            # For now, just log the decision
            logger.info(f"Human approval for workflow {workflow_id}: {'approved' if approved else 'rejected'}")
            
            if comments:
                logger.info(f"Approval comments: {comments}")
            
            # In a full implementation, this would update the workflow state
            return True
            
        except Exception as e:
            logger.error(f"Error processing approval for workflow {workflow_id}: {e}")
            return False

    # Chat interface integration methods
    async def process_chat_message(
        self,
        message: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Main entry point for chat integration"""
        try:
            # Create task from chat message
            task_id = await self.create_task_from_chat(
                message,
                {
                    'session_id': session_id,
                    'user_id': user_id,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Wait for initial processing (up to 30 seconds for immediate response)
            await asyncio.sleep(2)  # Give it a moment to start
            
            task_status = await self.get_task_status(task_id)
            
            if task_status and task_status['status'] == 'completed':
                # Task completed quickly - return results
                result = await self.get_task_result(task_id)
                return {
                    'type': 'immediate_result',
                    'task_id': task_id,
                    'result': result,
                    'message': self._format_result_for_chat(result)
                }
            else:
                # Task still running - return status
                return {
                    'type': 'task_started',
                    'task_id': task_id,
                    'status': task_status['status'] if task_status else 'unknown',
                    'message': f"I'm analyzing this request using my agent swarm. Task ID: {task_id}. I'll provide results as they become available."
                }
                
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            return {
                'type': 'error',
                'error': str(e),
                'message': f"I encountered an error while processing your request: {str(e)}"
            }

    def _format_result_for_chat(self, result: Dict[str, Any]) -> str:
        """Format analysis result for chat display"""
        if not result:
            return "Analysis completed but no results available."
        
        if 'analysis' in result:
            analysis = result['analysis']
            
            message_parts = ["📊 **Repository Analysis Complete**\n"]
            
            # Structure info
            if 'structure' in analysis:
                struct = analysis['structure']
                message_parts.append("**Structure Overview:**")
                message_parts.append(f"• {struct.get('total_files', 0)} files analyzed")
                message_parts.append(f"• {struct.get('total_lines', 0):,} lines of code")
                message_parts.append(f"• Primary language: {struct.get('primary_language', 'unknown')}")
                message_parts.append("")
            
            # Patterns
            if 'patterns' in analysis:
                patterns = analysis['patterns']
                detected_patterns = [name for name, detected in patterns.items() if detected]
                if detected_patterns:
                    message_parts.append(f"**Patterns Detected:** {', '.join(detected_patterns)}")
                    message_parts.append("")
            
            # Quality insights
            if 'quality_insights' in analysis:
                insights = analysis['quality_insights']
                if insights:
                    message_parts.append(f"**Quality Insights:** {len(insights)} issues found")
                    for insight in insights[:3]:  # Show top 3
                        message_parts.append(f"• {insight['title']} ({insight['severity']})")
                    message_parts.append("")
            
            # Recommendations
            if 'recommendations' in analysis:
                recs = analysis['recommendations']
                if recs.get('prioritized'):
                    message_parts.append("**Top Recommendations:**")
                    for i, rec in enumerate(recs['prioritized'][:3], 1):
                        message_parts.append(f"{i}. {rec}")
            
            return '\n'.join(message_parts)
        
        return "Analysis completed. Results available for detailed review."

    def get_swarm_summary(self) -> str:
        """Get a summary of the swarm system for chat"""
        if not self.is_initialized:
            return "⚠️ Agent swarm is not initialized. Please check system configuration."
        
        status = f"""🤖 **Sophia AI Agent Swarm Status**

**Active Agents:** {len(self.agents)}
• Repository Analyst (code intelligence)
• Cutting-Edge Planner (experimental approaches)  
• Conservative Planner (stable solutions)
• Synthesis Planner (optimal combinations)

**Capabilities:**
• Repository analysis and pattern recognition
• Multi-approach planning and synthesis
• Code quality assessment
• Semantic code search and similarity analysis

**Current Activity:**
• Active tasks: {len(self.active_tasks)}
• Completed tasks: {len([t for t in self.task_history if t.status == "completed"])}

Ready to analyze code, plan implementations, and provide intelligent insights about your repository! 🚀"""

        return status


# Global swarm manager instance
_swarm_manager: Optional[SophiaAgentSwarmManager] = None


async def get_swarm_manager(
    mcp_clients: Dict[str, Any],
    config: Optional[SwarmConfiguration] = None
) -> SophiaAgentSwarmManager:
    """Get or create the global swarm manager instance"""
    global _swarm_manager
    
    if _swarm_manager is None:
        if config is None:
            config = SwarmConfiguration()
        
        _swarm_manager = SophiaAgentSwarmManager(config, mcp_clients)
        await _swarm_manager.initialize()
    
    return _swarm_manager


async def process_chat_request(
    message: str,
    session_id: str,
    user_id: Optional[str] = None,
    mcp_clients: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Main entry point for chat integration"""
    if mcp_clients is None:
        return {
            'type': 'error',
            'message': 'Agent swarm not available - MCP clients not configured'
        }
    
    try:
        swarm = await get_swarm_manager(mcp_clients)
        return await swarm.process_chat_message(message, session_id, user_id)
    except Exception as e:
        logger.error(f"Error in chat request processing: {e}")
        return {
            'type': 'error',
            'message': f'Agent swarm error: {str(e)}'
        }
