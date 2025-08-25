"""
Sophia AI Agent Base Framework

This module provides the foundational classes and interfaces for the Sophia AI
agent swarm system. All specialized agents inherit from the base SophiaAgent class.

Key Features:
- Agent lifecycle management
- Inter-agent communication protocols
- Memory and context management
- Task execution framework
- MCP service integration

Version: 1.0.0
Author: Sophia AI Intelligence Team
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

import logging

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Enumeration of available agent roles in the swarm"""
    REPOSITORY_ANALYST = "repository_analyst"
    TASK_PLANNER = "task_planner" 
    CODE_GENERATOR = "code_generator"
    QUALITY_ASSURANCE = "quality_assurance"
    ORCHESTRATOR = "orchestrator"


class TaskStatus(Enum):
    """Task execution status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentTask:
    """
    Represents a task that can be executed by an agent
    """
    id: str
    title: str
    description: str
    task_type: str
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    assigned_agent: Optional[str] = None
    parent_task_id: Optional[str] = None
    context: Dict[str, Any] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.id is None:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization"""
        return {
            **asdict(self),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'priority': self.priority.value if self.priority else None,
            'status': self.status.value if self.status else None
        }


@dataclass
class AgentMessage:
    """
    Inter-agent communication message
    """
    id: str
    sender_id: str
    recipient_id: Optional[str]  # None for broadcast messages
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime
    task_id: Optional[str] = None
    requires_response: bool = False

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }


class AgentContext:
    """
    Manages agent execution context and state
    """
    
    def __init__(self):
        self.current_task: Optional[AgentTask] = None
        self.session_data: Dict[str, Any] = {}
        self.capabilities: List[str] = []
        self.resource_limits: Dict[str, Any] = {
            'max_concurrent_tasks': 3,
            'memory_limit_mb': 512,
            'timeout_seconds': 300
        }

    def set_current_task(self, task: AgentTask):
        """Set the currently executing task"""
        self.current_task = task
        self.session_data['current_task_id'] = task.id
        self.session_data['task_start_time'] = datetime.now().isoformat()

    def clear_current_task(self):
        """Clear the current task when completed"""
        if self.current_task:
            self.session_data[f'completed_task_{self.current_task.id}'] = {
                'completed_at': datetime.now().isoformat(),
                'status': self.current_task.status.value
            }
        self.current_task = None
        self.session_data.pop('current_task_id', None)
        self.session_data.pop('task_start_time', None)

    def add_capability(self, capability: str):
        """Add a capability to this agent"""
        if capability not in self.capabilities:
            self.capabilities.append(capability)

    def has_capability(self, capability: str) -> bool:
        """Check if agent has a specific capability"""
        return capability in self.capabilities


class AgentMemory:
    """
    Agent memory and knowledge management system
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.short_term: Dict[str, Any] = {}
        self.working_memory: Dict[str, Any] = {}
        self.knowledge_base: Dict[str, Any] = {}
        self.conversation_history: List[AgentMessage] = []

    async def store_short_term(self, key: str, value: Any):
        """Store data in short-term memory (current session only)"""
        self.short_term[key] = {
            'value': value,
            'timestamp': datetime.now().isoformat()
        }

    async def store_working_memory(self, key: str, value: Any):
        """Store data in working memory (task-scoped)"""
        self.working_memory[key] = {
            'value': value,
            'timestamp': datetime.now().isoformat()
        }

    async def store_knowledge(self, key: str, value: Any, category: str = 'general'):
        """Store data in long-term knowledge base"""
        if category not in self.knowledge_base:
            self.knowledge_base[category] = {}
        
        self.knowledge_base[category][key] = {
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'access_count': 0
        }

    async def retrieve(self, key: str, memory_type: str = 'any') -> Optional[Any]:
        """Retrieve data from memory"""
        if memory_type in ['any', 'short_term'] and key in self.short_term:
            return self.short_term[key]['value']
        
        if memory_type in ['any', 'working'] and key in self.working_memory:
            return self.working_memory[key]['value']
        
        if memory_type in ['any', 'knowledge']:
            for category in self.knowledge_base.values():
                if key in category:
                    category[key]['access_count'] += 1
                    return category[key]['value']
        
        return None

    def add_conversation_message(self, message: AgentMessage):
        """Add message to conversation history"""
        self.conversation_history.append(message)
        # Keep only last 100 messages to prevent memory bloat
        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-100:]

    def get_recent_conversations(self, limit: int = 10) -> List[AgentMessage]:
        """Get recent conversation messages"""
        return self.conversation_history[-limit:] if self.conversation_history else []

    def clear_working_memory(self):
        """Clear working memory (typically after task completion)"""
        self.working_memory.clear()


class SophiaAgent(ABC):
    """
    Abstract base class for all Sophia AI agents
    
    This class provides the foundational framework that all specialized agents
    inherit from, including task execution, communication, and memory management.
    """
    
    def __init__(
        self, 
        agent_id: str,
        role: AgentRole,
        name: str,
        llm_config: Dict[str, Any],
        mcp_clients: Dict[str, Any]
    ):
        self.agent_id = agent_id
        self.role = role
        self.name = name
        self.llm_config = llm_config
        self.mcp_clients = mcp_clients
        
        self.context = AgentContext()
        self.memory = AgentMemory(agent_id)
        self.is_active = False
        self.current_tasks: List[AgentTask] = []
        self.collaboration_partners: List[str] = []
        
        # Initialize agent-specific capabilities
        self._initialize_capabilities()
        
        logger.info(f"Agent {self.name} ({self.agent_id}) initialized with role {self.role.value}")

    @abstractmethod
    def _initialize_capabilities(self):
        """Initialize agent-specific capabilities - must be implemented by subclasses"""
        pass

    @abstractmethod
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Execute a specific task - must be implemented by subclasses
        
        Args:
            task: The task to execute
            
        Returns:
            Dict containing task results and metadata
        """
        pass

    async def start(self):
        """Start the agent and begin listening for tasks"""
        self.is_active = True
        logger.info(f"Agent {self.name} started")

    async def stop(self):
        """Stop the agent gracefully"""
        self.is_active = False
        # Complete any ongoing tasks
        for task in self.current_tasks:
            if task.status == TaskStatus.IN_PROGRESS:
                task.status = TaskStatus.CANCELLED
                logger.warning(f"Task {task.id} cancelled due to agent shutdown")
        logger.info(f"Agent {self.name} stopped")

    async def accept_task(self, task: AgentTask) -> bool:
        """
        Evaluate whether this agent can accept a given task
        
        Args:
            task: The task to evaluate
            
        Returns:
            True if task can be accepted, False otherwise
        """
        # Check resource limits
        if len(self.current_tasks) >= self.context.resource_limits['max_concurrent_tasks']:
            logger.warning(f"Agent {self.name} cannot accept task - at capacity")
            return False
        
        # Check if agent has required capabilities for this task type
        required_capability = f"handle_{task.task_type}"
        if not self.context.has_capability(required_capability):
            logger.warning(f"Agent {self.name} lacks capability for task type {task.task_type}")
            return False
        
        return True

    async def process_task(self, task: AgentTask) -> AgentTask:
        """
        Process a task through the complete execution pipeline
        
        Args:
            task: The task to process
            
        Returns:
            The completed task with results
        """
        try:
            # Pre-execution setup
            task.assigned_agent = self.agent_id
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            
            self.current_tasks.append(task)
            self.context.set_current_task(task)
            
            logger.info(f"Agent {self.name} starting task {task.id}: {task.title}")
            
            # Execute the task
            result = await self.execute_task(task)
            
            # Post-execution cleanup
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            logger.info(f"Agent {self.name} completed task {task.id}")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            
            logger.error(f"Agent {self.name} failed task {task.id}: {e}")
        
        finally:
            # Clean up
            self.current_tasks.remove(task)
            self.context.clear_current_task()
            self.memory.clear_working_memory()
        
        return task

    async def send_message(self, recipient_id: Optional[str], message_type: str, content: Dict[str, Any]) -> AgentMessage:
        """
        Send a message to another agent or broadcast to all agents
        
        Args:
            recipient_id: Target agent ID (None for broadcast)
            message_type: Type of message being sent
            content: Message content
            
        Returns:
            The sent message
        """
        message = AgentMessage(
            id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            message_type=message_type,
            content=content,
            timestamp=datetime.now(),
            task_id=self.context.current_task.id if self.context.current_task else None
        )
        
        # Add to conversation history
        self.memory.add_conversation_message(message)
        
        logger.debug(f"Agent {self.name} sent {message_type} message to {recipient_id or 'all agents'}")
        
        return message

    async def receive_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Process an incoming message from another agent
        
        Args:
            message: The incoming message
            
        Returns:
            Optional response message
        """
        # Add to conversation history
        self.memory.add_conversation_message(message)
        
        logger.debug(f"Agent {self.name} received {message.message_type} message from {message.sender_id}")
        
        # Handle different message types
        if message.message_type == "collaboration_request":
            return await self._handle_collaboration_request(message)
        elif message.message_type == "task_delegation":
            return await self._handle_task_delegation(message)
        elif message.message_type == "status_inquiry":
            return await self._handle_status_inquiry(message)
        else:
            logger.warning(f"Agent {self.name} received unknown message type: {message.message_type}")
        
        return None

    async def _handle_collaboration_request(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle collaboration requests from other agents"""
        sender_id = message.sender_id
        if sender_id not in self.collaboration_partners:
            self.collaboration_partners.append(sender_id)
        
        return await self.send_message(
            sender_id,
            "collaboration_accepted",
            {"status": "accepted", "capabilities": self.context.capabilities}
        )

    async def _handle_task_delegation(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle task delegation from other agents"""
        task_data = message.content.get("task")
        if task_data:
            task = AgentTask(**task_data)
            can_accept = await self.accept_task(task)
            
            return await self.send_message(
                message.sender_id,
                "task_response",
                {"task_id": task.id, "accepted": can_accept}
            )
        
        return None

    async def _handle_status_inquiry(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Handle status inquiries from other agents"""
        status = {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "is_active": self.is_active,
            "current_tasks": len(self.current_tasks),
            "capabilities": self.context.capabilities
        }
        
        return await self.send_message(
            message.sender_id,
            "status_response",
            {"status": status}
        )

    async def get_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role.value,
            "is_active": self.is_active,
            "current_tasks": len(self.current_tasks),
            "capabilities": self.context.capabilities,
            "collaboration_partners": self.collaboration_partners,
            "memory_usage": {
                "short_term_items": len(self.memory.short_term),
                "working_memory_items": len(self.memory.working_memory),
                "knowledge_base_categories": len(self.memory.knowledge_base),
                "conversation_history": len(self.memory.conversation_history)
            }
        }

    def __repr__(self) -> str:
        return f"SophiaAgent(id={self.agent_id}, role={self.role.value}, name={self.name})"
