"""
Unit tests for Swarm Coordinator Service
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime


class TestSwarmCoordinator:
    """Test suite for Swarm Coordinator functionality"""
    
    @pytest.fixture
    def mock_swarm_config(self):
        """Mock swarm configuration"""
        return {
            "swarms": {
                "research": {
                    "agents": ["scout1", "scout2", "scout3"],
                    "strategy": "parallel",
                    "temperature": 0.7
                },
                "development": {
                    "agents": ["coder1", "coder2"],
                    "strategy": "sequential",
                    "temperature": 0.3
                },
                "validation": {
                    "agents": ["judge1", "judge2"],
                    "strategy": "consensus",
                    "temperature": 0.1
                }
            }
        }
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_swarm_initialization(self, mock_swarm_config):
        """Test swarm initialization with configuration"""
        from services.swarm_coordinator import SwarmCoordinator
        
        coordinator = SwarmCoordinator(mock_swarm_config)
        
        assert len(coordinator.swarms) == 3
        assert "research" in coordinator.swarms
        assert coordinator.swarms["research"]["strategy"] == "parallel"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_parallel_swarm_execution(self):
        """Test parallel execution of swarm agents"""
        from services.swarm_coordinator import SwarmCoordinator
        
        coordinator = SwarmCoordinator()
        
        with patch.object(coordinator, '_execute_agent', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {"result": "success", "data": "test"}
            
            results = await coordinator.execute_parallel_swarm(
                agents=["agent1", "agent2", "agent3"],
                task="Test task"
            )
            
            assert len(results) == 3
            assert mock_exec.call_count == 3
            assert all(r["result"] == "success" for r in results)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sequential_swarm_execution(self):
        """Test sequential execution with context passing"""
        from services.swarm_coordinator import SwarmCoordinator
        
        coordinator = SwarmCoordinator()
        
        with patch.object(coordinator, '_execute_agent', new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = [
                {"result": "step1", "context": {"key1": "value1"}},
                {"result": "step2", "context": {"key1": "value1", "key2": "value2"}},
                {"result": "final", "context": {"key1": "value1", "key2": "value2", "key3": "value3"}}
            ]
            
            result = await coordinator.execute_sequential_swarm(
                agents=["agent1", "agent2", "agent3"],
                task="Test task"
            )
            
            assert result["result"] == "final"
            assert len(result["context"]) == 3
            assert mock_exec.call_count == 3
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_consensus_swarm_with_disagreement(self):
        """Test consensus mechanism with disagreeing agents"""
        from services.swarm_coordinator import SwarmCoordinator
        
        coordinator = SwarmCoordinator()
        
        agent_responses = [
            {"verdict": "approve", "confidence": 0.9},
            {"verdict": "reject", "confidence": 0.8},
            {"verdict": "approve", "confidence": 0.7}
        ]
        
        with patch.object(coordinator, '_execute_agent', new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = agent_responses
            
            result = await coordinator.execute_consensus_swarm(
                agents=["judge1", "judge2", "judge3"],
                task="Evaluate proposal"
            )
            
            assert result["consensus"] == "approve"  # 2 out of 3 approved
            assert result["agreement_score"] < 1.0  # Not perfect agreement
            assert "dissenting_opinions" in result
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_error_handling_in_swarm(self):
        """Test error handling when agents fail"""
        from services.swarm_coordinator import SwarmCoordinator
        
        coordinator = SwarmCoordinator()
        
        with patch.object(coordinator, '_execute_agent', new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = [
                {"result": "success"},
                Exception("Agent failure"),
                {"result": "success"}
            ]
            
            results = await coordinator.execute_parallel_swarm(
                agents=["agent1", "agent2", "agent3"],
                task="Test task",
                allow_failures=True
            )
            
            assert len(results) == 3
            assert results[0]["result"] == "success"
            assert results[1]["error"] == "Agent failure"
            assert results[2]["result"] == "success"
    
    @pytest.mark.unit
    def test_swarm_strategy_selection(self):
        """Test automatic strategy selection based on task type"""
        from services.swarm_coordinator import select_swarm_strategy
        
        # Research tasks should use parallel
        strategy = select_swarm_strategy("research quantum computing applications")
        assert strategy == "parallel"
        
        # Implementation tasks should use sequential
        strategy = select_swarm_strategy("implement authentication system")
        assert strategy == "sequential"
        
        # Validation tasks should use consensus
        strategy = select_swarm_strategy("validate security compliance")
        assert strategy == "consensus"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_adaptive_swarm_resizing(self):
        """Test dynamic swarm resizing based on task complexity"""
        from services.swarm_coordinator import SwarmCoordinator
        
        coordinator = SwarmCoordinator()
        
        # Simple task should use fewer agents
        agents = await coordinator.determine_optimal_swarm_size(
            task="What is 2+2?",
            complexity_score=0.1
        )
        assert len(agents) <= 2
        
        # Complex task should use more agents
        agents = await coordinator.determine_optimal_swarm_size(
            task="Design a distributed microservices architecture with fault tolerance",
            complexity_score=0.9
        )
        assert len(agents) >= 5