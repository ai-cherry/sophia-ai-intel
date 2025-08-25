"""
Sophia AI Agent Communication System

This module provides the message bus and communication infrastructure for
inter-agent collaboration within the Sophia AI agent swarm.

Key Features:
- Message routing and delivery
- Broadcast messaging
- Conflict resolution
- Task coordination
- Event-driven agent interactions

Version: 1.0.0
Author: Sophia AI Intelligence Team
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime
from collections import defaultdict, deque
from dataclasses import dataclass

from .base_agent import SophiaAgent, AgentMessage, AgentTask, TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class MessageRoute:
    """Represents a message routing rule"""
    sender_pattern: str
    recipient_pattern: str
    message_type: str
    priority: int = 1
    filters: Dict[str, Any] = None

    def __post_init__(self):
        if self.filters is None:
            self.filters = {}


@dataclass
class ConflictResolution:
    """Represents a conflict between agent responses"""
    task_id: str
    conflicting_responses: List[Dict[str, Any]]
    resolution_strategy: str
    resolved_response: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0


class AgentMessageBus:
    """
    Central message bus for inter-agent communication
    
    Handles message routing, delivery, and coordination between agents
    in the Sophia AI swarm system.
    """
    
    def __init__(self):
        self.agents: Dict[str, SophiaAgent] = {}
        self.message_queue: deque = deque()
        self.routing_rules: List[MessageRoute] = []
        self.message_history: List[AgentMessage] = []
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.active_tasks: Dict[str, AgentTask] = {}
        self.task_assignments: Dict[str, List[str]] = defaultdict(list)  # task_id -> agent_ids
        self.collaboration_groups: Dict[str, Set[str]] = {}  # group_name -> agent_ids
        
        # Metrics and monitoring
        self.metrics = {
            'messages_sent': 0,
            'messages_delivered': 0,
            'messages_failed': 0,
            'conflicts_resolved': 0,
            'tasks_coordinated': 0
        }
        
        # Start background processing
        self._processing_active = False

    async def register_agent(self, agent: SophiaAgent):
        """Register an agent with the message bus"""
        self.agents[agent.agent_id] = agent
        logger.info(f"Agent {agent.name} registered with message bus")
        
        # Start processing if this is the first agent
        if not self._processing_active:
            asyncio.create_task(self._process_messages())
            self._processing_active = True

    async def unregister_agent(self, agent_id: str):
        """Unregister an agent from the message bus"""
        if agent_id in self.agents:
            agent = self.agents.pop(agent_id)
            logger.info(f"Agent {agent.name} unregistered from message bus")

    async def send_message(self, message: AgentMessage) -> bool:
        """
        Send a message through the bus
        
        Args:
            message: The message to send
            
        Returns:
            True if message was queued successfully
        """
        self.message_queue.append(message)
        self.metrics['messages_sent'] += 1
        logger.debug(f"Message {message.id} queued for delivery")
        return True

    async def broadcast_message(self, sender_id: str, message_type: str, content: Dict[str, Any]) -> List[str]:
        """
        Broadcast a message to all agents except the sender
        
        Args:
            sender_id: ID of the sending agent
            message_type: Type of message
            content: Message content
            
        Returns:
            List of recipient agent IDs
        """
        recipients = []
        for agent_id in self.agents:
            if agent_id != sender_id:
                message = AgentMessage(
                    id=f"broadcast_{datetime.now().timestamp()}_{agent_id}",
                    sender_id=sender_id,
                    recipient_id=agent_id,
                    message_type=message_type,
                    content=content,
                    timestamp=datetime.now()
                )
                await self.send_message(message)
                recipients.append(agent_id)
        
        logger.info(f"Broadcast message from {sender_id} sent to {len(recipients)} agents")
        return recipients

    async def send_to_group(self, group_name: str, sender_id: str, message_type: str, content: Dict[str, Any]) -> List[str]:
        """
        Send a message to all agents in a collaboration group
        
        Args:
            group_name: Name of the collaboration group
            sender_id: ID of the sending agent
            message_type: Type of message
            content: Message content
            
        Returns:
            List of recipient agent IDs
        """
        if group_name not in self.collaboration_groups:
            logger.warning(f"Collaboration group {group_name} not found")
            return []
        
        recipients = []
        for agent_id in self.collaboration_groups[group_name]:
            if agent_id != sender_id and agent_id in self.agents:
                message = AgentMessage(
                    id=f"group_{group_name}_{datetime.now().timestamp()}_{agent_id}",
                    sender_id=sender_id,
                    recipient_id=agent_id,
                    message_type=message_type,
                    content=content,
                    timestamp=datetime.now()
                )
                await self.send_message(message)
                recipients.append(agent_id)
        
        logger.info(f"Group message to {group_name} from {sender_id} sent to {len(recipients)} agents")
        return recipients

    async def create_collaboration_group(self, group_name: str, agent_ids: List[str]) -> bool:
        """
        Create a collaboration group with specified agents
        
        Args:
            group_name: Name for the new group
            agent_ids: List of agent IDs to include
            
        Returns:
            True if group was created successfully
        """
        # Verify all agents exist
        valid_agents = [agent_id for agent_id in agent_ids if agent_id in self.agents]
        if len(valid_agents) != len(agent_ids):
            logger.warning(f"Some agents not found when creating group {group_name}")
        
        if len(valid_agents) < 2:
            logger.error(f"Cannot create collaboration group {group_name} with less than 2 agents")
            return False
        
        self.collaboration_groups[group_name] = set(valid_agents)
        logger.info(f"Created collaboration group {group_name} with {len(valid_agents)} agents")
        
        # Notify group members
        for agent_id in valid_agents:
            message = AgentMessage(
                id=f"group_created_{group_name}_{agent_id}",
                sender_id="system",
                recipient_id=agent_id,
                message_type="group_created",
                content={
                    "group_name": group_name,
                    "members": list(valid_agents)
                },
                timestamp=datetime.now()
            )
            await self.send_message(message)
        
        return True

    async def coordinate_task(self, task: AgentTask, preferred_agents: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Coordinate task execution among agents
        
        Args:
            task: The task to coordinate
            preferred_agents: Optional list of preferred agent IDs
            
        Returns:
            Coordination result with assigned agents
        """
        self.active_tasks[task.id] = task
        self.metrics['tasks_coordinated'] += 1
        
        # Determine candidate agents
        candidates = preferred_agents or list(self.agents.keys())
        suitable_agents = []
        
        # Check agent availability and capability
        for agent_id in candidates:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                can_accept = await agent.accept_task(task)
                if can_accept:
                    suitable_agents.append(agent_id)
        
        if not suitable_agents:
            logger.warning(f"No suitable agents found for task {task.id}")
            return {
                "success": False,
                "error": "No suitable agents available",
                "task_id": task.id
            }
        
        # For now, assign to the first suitable agent
        # TODO: Implement more sophisticated assignment algorithms
        assigned_agent_id = suitable_agents[0]
        self.task_assignments[task.id] = [assigned_agent_id]
        
        # Send task assignment message
        message = AgentMessage(
            id=f"task_assignment_{task.id}",
            sender_id="system",
            recipient_id=assigned_agent_id,
            message_type="task_assignment",
            content={
                "task": task.to_dict(),
                "coordination_id": f"coord_{task.id}"
            },
            timestamp=datetime.now(),
            task_id=task.id
        )
        
        await self.send_message(message)
        
        logger.info(f"Task {task.id} coordinated and assigned to agent {assigned_agent_id}")
        
        return {
            "success": True,
            "task_id": task.id,
            "assigned_agents": [assigned_agent_id],
            "available_agents": suitable_agents
        }

    async def collect_responses(self, task_id: str, timeout_seconds: int = 30) -> Dict[str, Any]:
        """
        Collect responses from agents working on a task
        
        Args:
            task_id: The task ID to collect responses for
            timeout_seconds: How long to wait for responses
            
        Returns:
            Collected responses and metadata
        """
        if task_id not in self.active_tasks:
            return {"error": "Task not found", "task_id": task_id}
        
        assigned_agents = self.task_assignments.get(task_id, [])
        if not assigned_agents:
            return {"error": "No agents assigned to task", "task_id": task_id}
        
        responses = {}
        start_time = datetime.now()
        
        # Wait for responses with timeout
        while (datetime.now() - start_time).seconds < timeout_seconds:
            # Check for completed tasks
            for agent_id in assigned_agents:
                if agent_id in self.agents:
                    agent = self.agents[agent_id]
                    # Check if agent has completed the task
                    for completed_task in agent.current_tasks:
                        if completed_task.id == task_id and completed_task.status == TaskStatus.COMPLETED:
                            responses[agent_id] = {
                                "status": "completed",
                                "result": completed_task.result,
                                "completion_time": completed_task.completed_at
                            }
            
            # If we have responses from all assigned agents, break
            if len(responses) >= len(assigned_agents):
                break
            
            await asyncio.sleep(0.5)  # Check every 500ms
        
        # Handle timeout
        for agent_id in assigned_agents:
            if agent_id not in responses:
                responses[agent_id] = {
                    "status": "timeout",
                    "error": "Agent did not respond within timeout period"
                }
        
        return {
            "task_id": task_id,
            "responses": responses,
            "collection_time": datetime.now(),
            "timeout_reached": len(responses) < len(assigned_agents)
        }

    async def resolve_conflicts(self, conflicting_responses: List[Dict[str, Any]], strategy: str = "consensus") -> ConflictResolution:
        """
        Resolve conflicts between agent responses
        
        Args:
            conflicting_responses: List of conflicting responses
            strategy: Resolution strategy ('consensus', 'majority', 'expert', 'hybrid')
            
        Returns:
            Conflict resolution result
        """
        self.metrics['conflicts_resolved'] += 1
        
        conflict = ConflictResolution(
            task_id="unknown",  # Will be set by caller
            conflicting_responses=conflicting_responses,
            resolution_strategy=strategy
        )
        
        if strategy == "consensus":
            # Find common elements across responses
            resolved = await self._resolve_by_consensus(conflicting_responses)
        elif strategy == "majority":
            # Use majority vote
            resolved = await self._resolve_by_majority(conflicting_responses)
        elif strategy == "expert":
            # Defer to most experienced agent
            resolved = await self._resolve_by_expert(conflicting_responses)
        else:
            # Default to first response
            resolved = conflicting_responses[0] if conflicting_responses else None
        
        conflict.resolved_response = resolved
        conflict.confidence_score = await self._calculate_confidence(resolved, conflicting_responses)
        
        logger.info(f"Conflict resolved using {strategy} strategy with confidence {conflict.confidence_score:.2f}")
        
        return conflict

    async def _resolve_by_consensus(self, responses: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Resolve conflicts by finding consensus among responses"""
        # Simple implementation: find common keys and values
        if not responses:
            return None
        
        common_keys = set(responses[0].keys())
        for response in responses[1:]:
            common_keys &= set(response.keys())
        
        consensus = {}
        for key in common_keys:
            values = [r[key] for r in responses]
            # If all values are the same, use it
            if len(set(str(v) for v in values)) == 1:
                consensus[key] = values[0]
        
        return consensus if consensus else responses[0]

    async def _resolve_by_majority(self, responses: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Resolve conflicts by majority vote"""
        if not responses:
            return None
        
        # Simple majority: return the most common response
        response_strings = [json.dumps(r, sort_keys=True) for r in responses]
        from collections import Counter
        most_common = Counter(response_strings).most_common(1)[0][0]
        
        return json.loads(most_common)

    async def _resolve_by_expert(self, responses: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Resolve conflicts by deferring to expert agent"""
        # For now, return first response (would need agent expertise scoring)
        return responses[0] if responses else None

    async def _calculate_confidence(self, resolved: Optional[Dict[str, Any]], original_responses: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for resolved response"""
        if not resolved or not original_responses:
            return 0.0
        
        # Simple confidence based on response similarity
        matches = 0
        for response in original_responses:
            # Count matching keys
            common_keys = set(resolved.keys()) & set(response.keys())
            matching_values = sum(1 for key in common_keys if resolved.get(key) == response.get(key))
            if common_keys:
                matches += matching_values / len(common_keys)
        
        return min(matches / len(original_responses), 1.0)

    async def _process_messages(self):
        """Background task to process queued messages"""
        while True:
            try:
                if self.message_queue:
                    message = self.message_queue.popleft()
                    await self._deliver_message(message)
                else:
                    await asyncio.sleep(0.1)  # Small delay when queue is empty
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    async def _deliver_message(self, message: AgentMessage) -> bool:
        """
        Deliver a message to its recipient
        
        Args:
            message: The message to deliver
            
        Returns:
            True if delivered successfully
        """
        try:
            # Add to message history
            self.message_history.append(message)
            
            # Keep only last 1000 messages
            if len(self.message_history) > 1000:
                self.message_history = self.message_history[-1000:]
            
            # Deliver to specific recipient
            if message.recipient_id and message.recipient_id in self.agents:
                recipient = self.agents[message.recipient_id]
                response = await recipient.receive_message(message)
                
                # Handle response if provided
                if response:
                    await self.send_message(response)
                
                self.metrics['messages_delivered'] += 1
                logger.debug(f"Message {message.id} delivered to {message.recipient_id}")
                
                # Notify subscribers
                await self._notify_subscribers(message)
                
                return True
            else:
                logger.warning(f"Recipient {message.recipient_id} not found for message {message.id}")
                self.metrics['messages_failed'] += 1
                return False
                
        except Exception as e:
            logger.error(f"Failed to deliver message {message.id}: {e}")
            self.metrics['messages_failed'] += 1
            return False

    async def _notify_subscribers(self, message: AgentMessage):
        """Notify event subscribers of message delivery"""
        event_type = f"message_{message.message_type}"
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"Subscriber callback failed: {e}")

    async def subscribe_to_events(self, event_type: str, callback: Callable):
        """Subscribe to message bus events"""
        self.subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to event type: {event_type}")

    async def get_metrics(self) -> Dict[str, Any]:
        """Get message bus metrics and statistics"""
        return {
            **self.metrics,
            "registered_agents": len(self.agents),
            "active_tasks": len(self.active_tasks),
            "message_queue_size": len(self.message_queue),
            "message_history_size": len(self.message_history),
            "collaboration_groups": len(self.collaboration_groups),
            "routing_rules": len(self.routing_rules)
        }

    async def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered agents"""
        status = {}
        for agent_id, agent in self.agents.items():
            status[agent_id] = await agent.get_status()
        return status


# Global message bus instance
message_bus = AgentMessageBus()
