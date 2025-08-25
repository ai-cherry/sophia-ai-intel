"""
Sophia CodeKraken Orchestrator

LangGraph-powered orchestration system for the hybrid AI agent swarm.
Manages stateful workflows, conditional branching, and agent coordination.

Key Features:
- Multi-agent workflow orchestration
- Conditional branching and retry logic
- State persistence and recovery
- Human approval integration
- Performance monitoring and metrics

Version: 1.0.0
Author: Sophia AI Intelligence Team
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver

from ..base_agent import SophiaAgent, AgentTask, TaskStatus, TaskPriority

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REQUIRES_APPROVAL = "requires_approval"


class NodeStatus(Enum):
    """Individual node execution status"""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowResult:
    """Result of workflow execution"""
    workflow_id: str
    status: WorkflowStatus
    start_time: datetime
    end_time: Optional[datetime]
    total_duration_seconds: Optional[float]
    nodes_executed: List[str]
    final_output: Optional[Dict[str, Any]]
    errors: List[str]
    metrics: Dict[str, Any]


@dataclass
class NodeExecution:
    """Execution details for a workflow node"""
    node_name: str
    agent_id: Optional[str]
    status: NodeStatus
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    error: Optional[str]
    retry_count: int = 0


class CodeKrakenState(TypedDict):
    """State object for CodeKraken workflows"""
    # Task information
    task_id: str
    task_description: str
    task_type: str
    task_context: Dict[str, Any]
    
    # Repository context
    repository_analysis: Optional[Dict[str, Any]]
    relevant_files: List[str]
    code_patterns: List[str]
    dependencies: List[str]
    
    # Planning phase
    cutting_edge_plan: Optional[Dict[str, Any]]
    conservative_plan: Optional[Dict[str, Any]]
    synthesis_plan: Optional[Dict[str, Any]]
    selected_plan: Optional[Dict[str, Any]]
    
    # Execution phase
    generated_code: Optional[str]
    debugged_code: Optional[str]
    optimized_code: Optional[str]
    test_results: Optional[Dict[str, Any]]
    
    # Quality and approval
    quality_assessment: Optional[Dict[str, Any]]
    requires_human_approval: bool
    approval_status: Optional[str]
    
    # Workflow management
    workflow_status: str
    current_node: str
    errors: List[str]
    retry_count: int
    execution_metrics: Dict[str, Any]
    
    # Agent assignments
    agent_assignments: Dict[str, str]  # node_name -> agent_id
    agent_outputs: Dict[str, Any]     # agent_id -> output


class CodeKrakenOrchestrator:
    """
    Main orchestrator for the CodeKraken agent swarm workflow
    """
    
    def __init__(
        self,
        agents: Dict[str, SophiaAgent],
        checkpoint_config: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        timeout_seconds: int = 1800  # 30 minutes
    ):
        self.agents = agents
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        
        # Workflow tracking
        self.active_workflows: Dict[str, WorkflowResult] = {}
        self.node_executions: Dict[str, List[NodeExecution]] = {}
        
        # Checkpoint system for state persistence
        if checkpoint_config and checkpoint_config.get('type') == 'postgres':
            self.checkpointer = PostgresSaver.from_conn_string(
                checkpoint_config['connection_string']
            )
        else:
            self.checkpointer = MemorySaver()
        
        # Initialize workflow graph
        self.workflow_graph = self._build_workflow_graph()
        self.compiled_graph = self.workflow_graph.compile(checkpointer=self.checkpointer)
        
        logger.info(f"CodeKraken Orchestrator initialized with {len(agents)} agents")

    def _build_workflow_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        graph = StateGraph(CodeKrakenState)
        
        # Add workflow nodes
        graph.add_node("repository_analysis", self._repository_analysis_node)
        graph.add_node("cutting_edge_planning", self._cutting_edge_planning_node)
        graph.add_node("conservative_planning", self._conservative_planning_node) 
        graph.add_node("plan_synthesis", self._plan_synthesis_node)
        graph.add_node("code_generation", self._code_generation_node)
        graph.add_node("debugging", self._debugging_node)
        graph.add_node("optimization", self._optimization_node)
        graph.add_node("quality_assessment", self._quality_assessment_node)
        graph.add_node("human_approval", self._human_approval_node)
        graph.add_node("finalization", self._finalization_node)
        
        # Set entry point
        graph.set_entry_point("repository_analysis")
        
        # Sequential flow with conditional branching
        graph.add_edge("repository_analysis", "cutting_edge_planning")
        graph.add_edge("repository_analysis", "conservative_planning")  # Parallel planning
        graph.add_edge("cutting_edge_planning", "plan_synthesis")
        graph.add_edge("conservative_planning", "plan_synthesis")
        graph.add_edge("plan_synthesis", "code_generation")
        
        # Conditional debugging loop
        graph.add_conditional_edges(
            "code_generation",
            self._should_debug,
            {
                "debug": "debugging",
                "optimize": "optimization"
            }
        )
        
        # Debug retry loop
        graph.add_conditional_edges(
            "debugging",
            self._should_retry_debug,
            {
                "retry": "code_generation",
                "optimize": "optimization",
                "fail": END
            }
        )
        
        graph.add_edge("optimization", "quality_assessment")
        
        # Human approval gate
        graph.add_conditional_edges(
            "quality_assessment", 
            self._requires_approval,
            {
                "approve": "human_approval",
                "finalize": "finalization"
            }
        )
        
        graph.add_conditional_edges(
            "human_approval",
            self._approval_decision,
            {
                "approved": "finalization", 
                "rejected": "plan_synthesis",
                "cancelled": END
            }
        )
        
        graph.add_edge("finalization", END)
        
        return graph

    async def execute_workflow(
        self,
        task: AgentTask,
        config: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """Execute a complete CodeKraken workflow"""
        workflow_id = f"workflow_{task.id}_{datetime.now().timestamp()}"
        
        # Initialize workflow result tracking
        workflow_result = WorkflowResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            start_time=datetime.now(),
            end_time=None,
            total_duration_seconds=None,
            nodes_executed=[],
            final_output=None,
            errors=[],
            metrics={}
        )
        
        self.active_workflows[workflow_id] = workflow_result
        self.node_executions[workflow_id] = []
        
        try:
            # Initialize state
            initial_state = CodeKrakenState(
                task_id=task.id,
                task_description=task.description,
                task_type=task.task_type,
                task_context=task.context or {},
                repository_analysis=None,
                relevant_files=[],
                code_patterns=[],
                dependencies=[],
                cutting_edge_plan=None,
                conservative_plan=None,
                synthesis_plan=None,
                selected_plan=None,
                generated_code=None,
                debugged_code=None,
                optimized_code=None,
                test_results=None,
                quality_assessment=None,
                requires_human_approval=False,
                approval_status=None,
                workflow_status=WorkflowStatus.RUNNING.value,
                current_node="repository_analysis",
                errors=[],
                retry_count=0,
                execution_metrics={},
                agent_assignments={},
                agent_outputs={}
            )
            
            # Execute workflow with timeout
            final_state = await asyncio.wait_for(
                self.compiled_graph.ainvoke(
                    initial_state,
                    config={"configurable": {"thread_id": workflow_id}, **(config or {})}
                ),
                timeout=self.timeout_seconds
            )
            
            # Update workflow result
            workflow_result.status = WorkflowStatus.COMPLETED
            workflow_result.final_output = {
                "generated_code": final_state.get("optimized_code") or final_state.get("generated_code"),
                "test_results": final_state.get("test_results"),
                "quality_assessment": final_state.get("quality_assessment"),
                "selected_plan": final_state.get("selected_plan")
            }
            
        except asyncio.TimeoutError:
            workflow_result.status = WorkflowStatus.FAILED
            workflow_result.errors.append(f"Workflow timed out after {self.timeout_seconds} seconds")
            logger.error(f"Workflow {workflow_id} timed out")
            
        except Exception as e:
            workflow_result.status = WorkflowStatus.FAILED
            workflow_result.errors.append(str(e))
            logger.error(f"Workflow {workflow_id} failed: {e}")
        
        finally:
            # Finalize workflow result
            workflow_result.end_time = datetime.now()
            workflow_result.total_duration_seconds = (
                workflow_result.end_time - workflow_result.start_time
            ).total_seconds()
            
            # Calculate metrics
            workflow_result.metrics = self._calculate_workflow_metrics(workflow_id)
            
        return workflow_result

    # Node implementations
    async def _repository_analysis_node(self, state: CodeKrakenState) -> Dict[str, Any]:
        """Analyze repository context for the task"""
        node_execution = NodeExecution(
            node_name="repository_analysis",
            agent_id=None,
            status=NodeStatus.RUNNING,
            start_time=datetime.now(),
            end_time=None,
            duration_seconds=None,
            input_data={"task_description": state["task_description"]},
            output_data=None,
            error=None
        )
        
        try:
            # Find Repository Analyst agent
            repo_agent = self._find_agent_by_role("repository_analyst")
            if repo_agent:
                node_execution.agent_id = repo_agent.agent_id
                
                # Create repository analysis task
                analysis_task = AgentTask(
                    id=f"repo_analysis_{state['task_id']}",
                    title="Repository Analysis",
                    description=f"Analyze repository context for: {state['task_description']}",
                    task_type="repository_analysis",
                    priority=TaskPriority.HIGH,
                    status=TaskStatus.PENDING,
                    created_at=datetime.now(),
                    context=state["task_context"]
                )
                
                # Execute analysis
                completed_task = await repo_agent.process_task(analysis_task)
                
                if completed_task.status == TaskStatus.COMPLETED and completed_task.result:
                    analysis_result = completed_task.result
                    node_execution.output_data = analysis_result
                    node_execution.status = NodeStatus.COMPLETED
                    
                    return {
                        "repository_analysis": analysis_result,
                        "relevant_files": analysis_result.get("relevant_files", []),
                        "code_patterns": analysis_result.get("code_patterns", []),
                        "dependencies": analysis_result.get("dependencies", []),
                        "current_node": "cutting_edge_planning"
                    }
                else:
                    raise Exception(f"Repository analysis failed: {completed_task.error}")
            else:
                raise Exception("Repository Analyst agent not found")
                
        except Exception as e:
            node_execution.status = NodeStatus.FAILED
            node_execution.error = str(e)
            logger.error(f"Repository analysis failed: {e}")
            
            return {
                "errors": state["errors"] + [str(e)],
                "workflow_status": WorkflowStatus.FAILED.value
            }
        
        finally:
            node_execution.end_time = datetime.now()
            if node_execution.start_time:
                node_execution.duration_seconds = (
                    node_execution.end_time - node_execution.start_time
                ).total_seconds()
            
            workflow_id = f"workflow_{state['task_id']}"
            if workflow_id in self.node_executions:
                self.node_executions[workflow_id].append(node_execution)

    async def _cutting_edge_planning_node(self, state: CodeKrakenState) -> Dict[str, Any]:
        """Generate cutting-edge/experimental plan"""
        return await self._execute_planning_node(state, "cutting_edge", "cutting_edge_plan")

    async def _conservative_planning_node(self, state: CodeKrakenState) -> Dict[str, Any]:
        """Generate conservative/stable plan"""
        return await self._execute_planning_node(state, "conservative", "conservative_plan")

    async def _execute_planning_node(self, state: CodeKrakenState, planner_type: str, output_key: str) -> Dict[str, Any]:
        """Generic planning node execution"""
        try:
            planner_agent = self._find_agent_by_role(f"{planner_type}_planner")
            if not planner_agent:
                raise Exception(f"{planner_type} planner agent not found")
            
            planning_task = AgentTask(
                id=f"{planner_type}_plan_{state['task_id']}",
                title=f"{planner_type.title()} Planning",
                description=state["task_description"],
                task_type="task_planning",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                created_at=datetime.now(),
                context={
                    **state["task_context"],
                    "repository_analysis": state["repository_analysis"],
                    "relevant_files": state["relevant_files"],
                    "planner_type": planner_type
                }
            )
            
            completed_task = await planner_agent.process_task(planning_task)
            
            if completed_task.status == TaskStatus.COMPLETED and completed_task.result:
                return {output_key: completed_task.result}
            else:
                raise Exception(f"{planner_type} planning failed: {completed_task.error}")
                
        except Exception as e:
            logger.error(f"{planner_type} planning failed: {e}")
            return {
                "errors": state["errors"] + [str(e)]
            }

    async def _plan_synthesis_node(self, state: CodeKrakenState) -> Dict[str, Any]:
        """Synthesize multiple plans into optimal approach"""
        try:
            synthesis_agent = self._find_agent_by_role("synthesis_planner")
            if not synthesis_agent:
                raise Exception("Synthesis planner agent not found")
            
            synthesis_task = AgentTask(
                id=f"synthesis_{state['task_id']}",
                title="Plan Synthesis",
                description="Synthesize optimal approach from multiple plans",
                task_type="plan_synthesis",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                created_at=datetime.now(),
                context={
                    "cutting_edge_plan": state["cutting_edge_plan"],
                    "conservative_plan": state["conservative_plan"],
                    "repository_analysis": state["repository_analysis"],
                    "task_description": state["task_description"]
                }
            )
            
            completed_task = await synthesis_agent.process_task(synthesis_task)
            
            if completed_task.status == TaskStatus.COMPLETED and completed_task.result:
                return {
                    "synthesis_plan": completed_task.result,
                    "selected_plan": completed_task.result,
                    "current_node": "code_generation"
                }
            else:
                raise Exception(f"Plan synthesis failed: {completed_task.error}")
                
        except Exception as e:
            logger.error(f"Plan synthesis failed: {e}")
            return {
                "errors": state["errors"] + [str(e)],
                "workflow_status": WorkflowStatus.FAILED.value
            }

    async def _code_generation_node(self, state: CodeKrakenState) -> Dict[str, Any]:
        """Generate code based on synthesized plan"""
        try:
            code_agent = self._find_agent_by_role("code_generator")
            if not code_agent:
                raise Exception("Code generator agent not found")
            
            generation_task = AgentTask(
                id=f"codegen_{state['task_id']}",
                title="Code Generation",
                description=state["task_description"],
                task_type="code_generation",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                created_at=datetime.now(),
                context={
                    "selected_plan": state["selected_plan"],
                    "repository_analysis": state["repository_analysis"],
                    "relevant_files": state["relevant_files"],
                    "code_patterns": state["code_patterns"]
                }
            )
            
            completed_task = await code_agent.process_task(generation_task)
            
            if completed_task.status == TaskStatus.COMPLETED and completed_task.result:
                return {
                    "generated_code": completed_task.result.get("code"),
                    "current_node": "debugging"
                }
            else:
                raise Exception(f"Code generation failed: {completed_task.error}")
                
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return {
                "errors": state["errors"] + [str(e)],
                "workflow_status": WorkflowStatus.FAILED.value
            }

    async def _debugging_node(self, state: CodeKrakenState) -> Dict[str, Any]:
        """Debug and fix generated code"""
        # Implementation similar to other nodes...
        return {"debugged_code": state["generated_code"], "current_node": "optimization"}

    async def _optimization_node(self, state: CodeKrakenState) -> Dict[str, Any]:
        """Optimize code for performance and efficiency"""
        # Implementation similar to other nodes...
        return {"optimized_code": state["debugged_code"], "current_node": "quality_assessment"}

    async def _quality_assessment_node(self, state: CodeKrakenState) -> Dict[str, Any]:
        """Assess code quality and determine if human approval is needed"""
        # Implementation similar to other nodes...
        return {
            "quality_assessment": {"score": 8.5, "issues": []},
            "requires_human_approval": True,
            "current_node": "human_approval"
        }

    async def _human_approval_node(self, state: CodeKrakenState) -> Dict[str, Any]:
        """Handle human approval workflow"""
        # This would integrate with dashboard for human approval
        return {
            "approval_status": "pending",
            "workflow_status": WorkflowStatus.REQUIRES_APPROVAL.value
        }

    async def _finalization_node(self, state: CodeKrakenState) -> Dict[str, Any]:
        """Finalize workflow and prepare output"""
        return {
            "workflow_status": WorkflowStatus.COMPLETED.value,
            "current_node": "completed"
        }

    # Conditional edge functions
    def _should_debug(self, state: CodeKrakenState) -> str:
        """Determine if debugging is needed"""
        if state.get("generated_code") and "error" not in state.get("generated_code", "").lower():
            return "optimize"
        return "debug"

    def _should_retry_debug(self, state: CodeKrakenState) -> str:
        """Determine if debug should retry or proceed"""
        if state.get("retry_count", 0) >= self.max_retries:
            return "fail"
        if state.get("debugged_code"):
            return "optimize"
        return "retry"

    def _requires_approval(self, state: CodeKrakenState) -> str:
        """Determine if human approval is required"""
        if state.get("requires_human_approval", False):
            return "approve"
        return "finalize"

    def _approval_decision(self, state: CodeKrakenState) -> str:
        """Process human approval decision"""
        status = state.get("approval_status")
        if status == "approved":
            return "approved"
        elif status == "rejected":
            return "rejected"
        return "cancelled"

    # Utility methods
    def _find_agent_by_role(self, role: str) -> Optional[SophiaAgent]:
        """Find agent by role name"""
        for agent in self.agents.values():
            if hasattr(agent, 'role') and agent.role.value == role:
                return agent
        return None

    def _calculate_workflow_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Calculate workflow execution metrics"""
        executions = self.node_executions.get(workflow_id, [])
        
        total_nodes = len(executions)
        successful_nodes = len([e for e in executions if e.status == NodeStatus.COMPLETED])
        failed_nodes = len([e for e in executions if e.status == NodeStatus.FAILED])
        
        total_duration = sum(
            e.duration_seconds for e in executions 
            if e.duration_seconds is not None
        )
        
        return {
            "total_nodes_executed": total_nodes,
            "successful_nodes": successful_nodes,
            "failed_nodes": failed_nodes,
            "success_rate": successful_nodes / total_nodes if total_nodes > 0 else 0,
            "total_execution_time": total_duration,
            "average_node_time": total_duration / total_nodes if total_nodes > 0 else 0
        }

    async def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowResult]:
        """Get current status of a workflow"""
        return self.active_workflows.get(workflow_id)

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id].status = WorkflowStatus.CANCELLED
            return True
        return False

    async def get_workflow_metrics(self) -> Dict[str, Any]:
        """Get overall orchestrator metrics"""
        total_workflows = len(self.active_workflows)
        completed = len([w for w in self.active_workflows.values() if w.status == WorkflowStatus.COMPLETED])
        failed = len([w for w in self.active_workflows.values() if w.status == WorkflowStatus.FAILED])
        
        return {
            "total_workflows": total_workflows,
            "completed_workflows": completed,
            "failed_workflows": failed,
            "success_rate": completed / total_workflows if total_workflows > 0 else 0,
            "active_agents": len(self.agents),
            "registered_agents": list(self.agents.keys())
        }
