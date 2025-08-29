"""
Unit tests for Memory Service (Mem0 integration)
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime, timedelta


class TestMemoryService:
    """Test suite for Memory Service functionality"""
    
    @pytest.fixture
    def mock_mem0_client(self):
        """Mock Mem0 client"""
        mock = MagicMock()
        mock.add.return_value = {"id": "mem-123", "status": "stored"}
        mock.search.return_value = [
            {"id": "mem-1", "content": "Previous interaction", "score": 0.9},
            {"id": "mem-2", "content": "Related context", "score": 0.8}
        ]
        return mock
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_memory_storage(self, mock_mem0_client):
        """Test storing memories in Mem0"""
        from services.memory_service import MemoryService
        
        service = MemoryService(client=mock_mem0_client)
        
        memory = {
            "user_id": "user-123",
            "session_id": "session-456",
            "content": "User prefers Python for backend development",
            "category": "preference",
            "metadata": {"confidence": 0.9}
        }
        
        result = await service.store_memory(memory)
        
        assert result["id"] == "mem-123"
        assert result["status"] == "stored"
        mock_mem0_client.add.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_memory_retrieval(self, mock_mem0_client):
        """Test retrieving relevant memories"""
        from services.memory_service import MemoryService
        
        service = MemoryService(client=mock_mem0_client)
        
        memories = await service.retrieve_memories(
            user_id="user-123",
            query="What programming languages does the user prefer?",
            limit=5
        )
        
        assert len(memories) == 2
        assert memories[0]["score"] > memories[1]["score"]
        mock_mem0_client.search.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_memory_aggregation(self, mock_mem0_client):
        """Test aggregating memories across sessions"""
        from services.memory_service import MemoryService
        
        service = MemoryService(client=mock_mem0_client)
        
        mock_mem0_client.get_all.return_value = [
            {"session_id": "s1", "content": "likes Python", "timestamp": "2024-01-01"},
            {"session_id": "s2", "content": "uses FastAPI", "timestamp": "2024-01-02"},
            {"session_id": "s3", "content": "prefers async", "timestamp": "2024-01-03"}
        ]
        
        aggregated = await service.aggregate_user_profile("user-123")
        
        assert "preferences" in aggregated
        assert "interaction_count" in aggregated
        assert aggregated["interaction_count"] == 3
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_memory_decay(self):
        """Test memory relevance decay over time"""
        from services.memory_service import calculate_memory_relevance
        
        # Recent memory should have high relevance
        recent_memory = {
            "timestamp": datetime.now() - timedelta(hours=1),
            "base_score": 0.8
        }
        recent_score = calculate_memory_relevance(recent_memory)
        assert recent_score >= 0.75
        
        # Old memory should have lower relevance
        old_memory = {
            "timestamp": datetime.now() - timedelta(days=30),
            "base_score": 0.8
        }
        old_score = calculate_memory_relevance(old_memory)
        assert old_score < recent_score
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_context_window_management(self, mock_mem0_client):
        """Test managing context window with memory prioritization"""
        from services.memory_service import MemoryService
        
        service = MemoryService(client=mock_mem0_client)
        
        # Simulate many memories
        mock_mem0_client.search.return_value = [
            {"id": f"mem-{i}", "content": f"Memory {i}", "score": 0.9 - (i * 0.05)}
            for i in range(20)
        ]
        
        context = await service.build_context_window(
            user_id="user-123",
            current_query="test query",
            max_tokens=1000
        )
        
        assert len(context["memories"]) < 20  # Should trim to fit token limit
        assert context["memories"][0]["score"] > context["memories"][-1]["score"]
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_memory_deduplication(self, mock_mem0_client):
        """Test deduplication of similar memories"""
        from services.memory_service import MemoryService
        
        service = MemoryService(client=mock_mem0_client)
        
        memories = [
            {"content": "User likes Python", "timestamp": "2024-01-01"},
            {"content": "User prefers Python", "timestamp": "2024-01-02"},
            {"content": "User uses JavaScript", "timestamp": "2024-01-03"}
        ]
        
        deduplicated = await service.deduplicate_memories(memories)
        
        assert len(deduplicated) == 2  # Python memories should be merged
        assert any("Python" in m["content"] for m in deduplicated)
        assert any("JavaScript" in m["content"] for m in deduplicated)
    
    @pytest.mark.unit
    def test_memory_categorization(self):
        """Test automatic categorization of memories"""
        from services.memory_service import categorize_memory
        
        # Preference memory
        pref = categorize_memory("I prefer dark mode in IDEs")
        assert pref == "preference"
        
        # Fact memory
        fact = categorize_memory("The user's email is john@example.com")
        assert fact == "fact"
        
        # Skill memory
        skill = categorize_memory("User is proficient in React and TypeScript")
        assert skill == "skill"
        
        # Context memory
        context = categorize_memory("We were discussing authentication yesterday")
        assert context == "context"