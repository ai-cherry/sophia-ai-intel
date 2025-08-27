import asyncio
from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
import httpx
import json
import os
from datetime import datetime
import uuid

app = FastAPI(title="Agents Swarm Service")

class AgentRole(str, Enum):
    PLANNER = "planner"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"

class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"

class SwarmTaskRequest(BaseModel):
    objective: str
    context: Optional[Dict[str, Any]] = {}
    max_iterations: Optional[int] = 3
    tools_allowed: Optional[List[str]] = None

class SwarmTaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    message: str

class TaskResult(BaseModel):
    task_id: str
    status: TaskStatus
    objective: str
    plan: Optional[Dict[str, Any]] = None
    execution_results: Optional[List[Dict[str, Any]]] = []
    review_feedback: Optional[Dict[str, Any]] = None
    final_output: Optional[str] = None
    errors: Optional[List[str]] = []

# In-memory task storage (use Redis in production)
tasks: Dict[str, TaskResult] = {}

# SSE keep-alive
async def sse_keepalive():
    while True:
        await asyncio.sleep(25)
        # In production, send SSE ping here

@app.on_event("startup")
async def startup():
    asyncio.create_task(sse_keepalive())

async def call_portkey_llm(prompt: str, role: AgentRole, max_tokens: int = 1000) -> str:
    """Call Portkey LLM service for agent reasoning"""
    portkey_url = os.getenv("PORTKEY_LLM_URL", "http://portkey-llm:8000")
    
    system_prompts = {
        AgentRole.PLANNER: "You are a strategic planner. Break down objectives into clear, actionable steps.",
        AgentRole.EXECUTOR: "You are an executor. Perform the given tasks and report results accurately.",
        AgentRole.REVIEWER: "You are a reviewer. Evaluate work quality and provide constructive feedback."
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{portkey_url}/summarize",
            headers={
                "x-tenant-id": "system",
                "x-actor-id": f"agent-{role.value}"
            },
            json={
                "content": prompt,
                "prompt_template": f"{system_prompts[role]}\n\nTask: {{content}}\n\nResponse:",
                "max_tokens": max_tokens,
                "model": "gpt-4"
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"LLM call failed for {role}")
        
        return response.json()["summary"]

async def planning_phase(task_id: str, objective: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Planning agent creates execution plan"""
    prompt = f"""
    Objective: {objective}
    Context: {json.dumps(context, indent=2)}
    
    Create a detailed execution plan with:
    1. Clear steps to achieve the objective
    2. Required tools/resources for each step
    3. Success criteria
    4. Potential risks and mitigations
    """
    
    plan_text = await call_portkey_llm(prompt, AgentRole.PLANNER)
    
    # Parse plan into structured format
    plan = {
        "created_at": datetime.utcnow().isoformat(),
        "objective": objective,
        "steps": plan_text,  # In production, parse this into structured steps
        "status": "approved"
    }
    
    tasks[task_id].plan = plan
    tasks[task_id].status = TaskStatus.EXECUTING
    
    return plan

async def execution_phase(task_id: str, plan: Dict[str, Any], tools_allowed: List[str]) -> List[Dict[str, Any]]:
    """Executor agents carry out the plan"""
    results = []
    
    # Execute each step in the plan
    execution_prompt = f"""
    Plan: {json.dumps(plan, indent=2)}
    Tools Available: {tools_allowed}
    
    Execute the plan and report results for each step.
    """
    
    execution_output = await call_portkey_llm(execution_prompt, AgentRole.EXECUTOR)
    
    # Store execution results
    result = {
        "executed_at": datetime.utcnow().isoformat(),
        "output": execution_output,
        "tools_used": tools_allowed or [],
        "status": "completed"
    }
    
    results.append(result)
    tasks[task_id].execution_results = results
    tasks[task_id].status = TaskStatus.REVIEWING
    
    return results

async def review_phase(task_id: str, plan: Dict[str, Any], execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Reviewer agent evaluates execution quality"""
    review_prompt = f"""
    Original Plan: {json.dumps(plan, indent=2)}
    Execution Results: {json.dumps(execution_results, indent=2)}
    
    Review the execution quality:
    1. Did it meet the objectives?
    2. Quality assessment (1-10)
    3. Improvements needed?
    4. Final recommendations
    """
    
    review_output = await call_portkey_llm(review_prompt, AgentRole.REVIEWER)
    
    feedback = {
        "reviewed_at": datetime.utcnow().isoformat(),
        "assessment": review_output,
        "approved": True,  # In production, parse approval from review
        "quality_score": 8  # In production, extract from review
    }
    
    tasks[task_id].review_feedback = feedback
    tasks[task_id].status = TaskStatus.COMPLETED
    tasks[task_id].final_output = review_output
    
    return feedback

async def run_swarm_workflow(task_id: str, request: SwarmTaskRequest):
    """Orchestrate the complete swarm workflow"""
    try:
        # Planning Phase
        tasks[task_id].status = TaskStatus.PLANNING
        plan = await planning_phase(task_id, request.objective, request.context)
        
        # Execution Phase
        execution_results = await execution_phase(task_id, plan, request.tools_allowed or [])
        
        # Review Phase
        review = await review_phase(task_id, plan, execution_results)
        
        # Iteration logic (if review requires changes)
        if not review.get("approved") and tasks[task_id].execution_results:
            if len(tasks[task_id].execution_results) < request.max_iterations:
                # Re-execute with feedback
                await execution_phase(task_id, plan, request.tools_allowed or [])
                await review_phase(task_id, plan, tasks[task_id].execution_results)
        
    except Exception as e:
        tasks[task_id].status = TaskStatus.FAILED
        tasks[task_id].errors = [str(e)]

@app.post("/tasks/create", response_model=SwarmTaskResponse)
async def create_task(
    request: SwarmTaskRequest,
    background_tasks: BackgroundTasks,
    x_tenant_id: str = Header(...),
    x_actor_id: str = Header(...)
):
    """Create and start a new swarm task"""
    task_id = str(uuid.uuid4())
    
    # Initialize task record
    task_result = TaskResult(
        task_id=task_id,
        status=TaskStatus.PENDING,
        objective=request.objective
    )
    tasks[task_id] = task_result
    
    # Start workflow in background
    background_tasks.add_task(run_swarm_workflow, task_id, request)
    
    # Log to audit
    try:
        from platform.common.audit import log_tool_invocation
        await log_tool_invocation(
            ctx={
                "tenant": x_tenant_id,
                "actor": x_actor_id,
                "purpose": "swarm_task_creation"
            },
            service="agents-swarm",
            tool="create_task",
            request={"objective": request.objective},
            response={"task_id": task_id},
            resource_ref=f"task:{task_id}"
        )
    except ImportError:
        # Platform libraries not available in development
        pass
    
    return SwarmTaskResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        message="Task created and workflow started"
    )

@app.get("/tasks/{task_id}", response_model=TaskResult)
async def get_task_status(
    task_id: str,
    x_tenant_id: str = Header(...),
    x_actor_id: str = Header(...)
):
    """Get current status and results of a swarm task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return tasks[task_id]

@app.get("/tasks", response_model=List[TaskResult])
async def list_tasks(
    x_tenant_id: str = Header(...),
    x_actor_id: str = Header(...)
):
    """List all swarm tasks"""
    return list(tasks.values())

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "agents-swarm", "active_tasks": len(tasks)}