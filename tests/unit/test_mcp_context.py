"""
Unit tests for MCP Context Service
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import os
import json
from datetime import datetime


class TestMCPContextService:
    """Test suite for MCP Context Service"""
    
    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """Set required environment variables for testing"""
        monkeypatch.setenv("WEAVIATE_URL", "http://test-weaviate:8080")
        monkeypatch.setenv("WEAVIATE_API_KEY", "test-key")
        monkeypatch.setenv("NEON_DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    
    @pytest.mark.unit
    def test_env_validation_fails_without_required_vars(self, monkeypatch):
        """Test that service fails to start without required environment variables"""
        monkeypatch.delenv("WEAVIATE_URL", raising=False)
        monkeypatch.delenv("WEAVIATE_API_KEY", raising=False)
        
        with pytest.raises(ValueError, match="Missing required environment variables"):
            from services.mcp_context import app
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_document(self, mock_env_vars, mock_weaviate_client):
        """Test document creation in context service"""
        from services.mcp_context.app import create_document_handler
        
        document = {
            "title": "Test Document",
            "content": "This is test content",
            "metadata": {"category": "test"}
        }
        
        with patch('asyncpg.connect', new_callable=AsyncMock) as mock_db:
            mock_conn = AsyncMock()
            mock_conn.fetchrow.return_value = {
                "id": "doc-123",
                "title": document["title"],
                "created_at": datetime.now()
            }
            mock_db.return_value = mock_conn
            
            result = await create_document_handler(document)
            
            assert result["id"] == "doc-123"
            assert result["status"] == "created"
            mock_weaviate_client.data_object.create.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_semantic_search(self, mock_env_vars, mock_weaviate_client):
        """Test semantic search functionality"""
        from services.mcp_context.app import search_documents_handler
        
        query = "quantum computing applications"
        
        mock_weaviate_client.query.get.return_value.with_near_text.return_value.with_limit.return_value.do.return_value = {
            "data": {
                "Get": {
                    "Document": [
                        {
                            "title": "Quantum Computing Guide",
                            "content": "Introduction to quantum computing...",
                            "_additional": {"distance": 0.15}
                        }
                    ]
                }
            }
        }
        
        results = await search_documents_handler(query, limit=5)
        
        assert len(results) == 1
        assert results[0]["title"] == "Quantum Computing Guide"
        assert results[0]["relevance_score"] > 0.8
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_health_endpoint(self, mock_env_vars):
        """Test health check endpoint"""
        from fastapi.testclient import TestClient
        from services.mcp_context.app import app
        
        with TestClient(app) as client:
            response = client.get("/healthz")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "providers" in data
    
    @pytest.mark.unit
    def test_embedding_generation(self, mock_env_vars):
        """Test document embedding generation"""
        from services.mcp_context.real_embeddings import generate_embedding
        
        with patch('openai.Embedding.create') as mock_openai:
            mock_openai.return_value = {
                "data": [{
                    "embedding": [0.1] * 1536  # OpenAI embedding dimension
                }]
            }
            
            embedding = generate_embedding("Test text")
            
            assert len(embedding) == 1536
            assert all(isinstance(x, float) for x in embedding)
            mock_openai.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_context_provider_abstraction(self, mock_env_vars):
        """Test unified context provider abstraction"""
        from services.mcp_context.app import ContextProvider
        
        provider = ContextProvider()
        
        # Test PostgreSQL provider
        with patch.object(provider, '_postgres_store', new_callable=AsyncMock) as mock_pg:
            mock_pg.return_value = {"id": "pg-123"}
            result = await provider.store("postgres", {"data": "test"})
            assert result["provider"] == "postgres"
        
        # Test Weaviate provider
        with patch.object(provider, '_weaviate_store', new_callable=AsyncMock) as mock_wv:
            mock_wv.return_value = {"id": "wv-123"}
            result = await provider.store("weaviate", {"data": "test"})
            assert result["provider"] == "weaviate"
    
    @pytest.mark.unit
    def test_metadata_validation(self, mock_env_vars):
        """Test document metadata validation"""
        from services.mcp_context.validators import validate_document_metadata
        
        valid_metadata = {
            "category": "research",
            "tags": ["quantum", "computing"],
            "author": "test-user"
        }
        
        invalid_metadata = {
            "tags": "should-be-array",  # Invalid type
            "invalid_field": ["test"]
        }
        
        assert validate_document_metadata(valid_metadata) == True
        assert validate_document_metadata(invalid_metadata) == False