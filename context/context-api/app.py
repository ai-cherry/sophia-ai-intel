#!/usr/bin/env python3
"""
Sophia AI Context API Service
============================

Context and memory management for Sophia AI platform.
Provides access to vector storage, conversation history, and contextual information retrieval.
"""

import os
import logging
import uuid
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import HTTPException
from pydantic import BaseModel
import weaviate
from weaviate.classes.init import Auth

# Import shared platform libraries
try:
    from platform.common.service_base import create_app, ok, err, raise_http_error
    from platform.auth.jwt import validate_token
    from platform.common.errors import ServiceError, ValidationError
except ImportError:
    # Fallback for development
    from platform.common.service_base import create_app, ok, err, raise_http_error
    validate_token = None
    ServiceError = Exception
    ValidationError = Exception

# Configure logging
logger = logging.getLogger(__name__)

# Environment configuration
SERVICE_NAME = "Sophia AI Context API"
SERVICE_DESCRIPTION = "Context and memory management service"
SERVICE_VERSION = "2.0.0"
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL", "")
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf")

# In-memory document store (for staging before vector processing)
_document_store = {}

# Pydantic models
class DocumentUpsert(BaseModel):
    """Document upsert request model"""
    id: Optional[str] = None
    account_id: str
    content: str
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    """Document response model"""
    doc_id: str
    status: str
    timestamp: str

# Create FastAPI app using the shared service base
app = create_app(
    name=SERVICE_NAME,
    desc=SERVICE_DESCRIPTION,
    version=SERVICE_VERSION
)

# Initialize Weaviate client using official cloud connection pattern
weaviate_client = weaviate.connect_to_weaviate_cloud(
    cluster_url=WEAVIATE_URL,
    auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
) if WEAVIATE_URL and WEAVIATE_API_KEY else None

# Service-specific endpoints

@app.get("/conversations")
async def get_conversations(user_id: Optional[str] = None, limit: int = 50):
    """Get conversation history"""
    try:
        # Placeholder for conversations data
        conversations = [
            {
                "id": "conv_001",
                "user_id": user_id or "user_123",
                "title": "Product Strategy Discussion",
                "last_message": "What are our Q4 priorities?",
                "message_count": 15,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "conv_002",
                "user_id": user_id or "user_123",
                "title": "Market Analysis",
                "last_message": "Competitor analysis shows...",
                "message_count": 8,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        ]

        return {
            "conversations": conversations[:limit],
            "count": len(conversations[:limit]),
            "service": SERVICE_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str, limit: int = 100):
    """Get messages from a specific conversation"""
    try:
        # Placeholder for messages data
        messages = [
            {
                "id": "msg_001",
                "conversation_id": conversation_id,
                "role": "user",
                "content": "What are our Q4 priorities?",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {"tokens": 8, "model": "gpt-4"}
            },
            {
                "id": "msg_002",
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": "Based on our strategic planning, Q4 priorities include...",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {"tokens": 150, "model": "gpt-4", "sources": ["strategy_doc.pdf"]}
            }
        ]

        return {
            "messages": messages[:limit],
            "count": len(messages[:limit]),
            "conversation_id": conversation_id,
            "service": SERVICE_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get messages for conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search_context(query: str, user_id: Optional[str] = None, limit: int = 10):
    """Search through context and conversation history using Weaviate"""
    try:
        if not weaviate_client:
            return {
                "query": query,
                "results": [],
                "count": 0,
                "service": SERVICE_NAME,
                "error": "Weaviate not configured",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        # Perform semantic search across different classes
        search_results = []
        
        # Search in Documents class if it exists
        try:
            documents_result = (
                weaviate_client.query
                .get("Documents", ["content", "source", "metadata"])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .with_additional(["certainty", "id"])
                .do()
            )
            
            if "data" in documents_result and "Get" in documents_result["data"] and "Documents" in documents_result["data"]["Get"]:
                for doc in documents_result["data"]["Get"]["Documents"]:
                    search_results.append({
                        "id": doc["_additional"]["id"],
                        "type": "document",
                        "title": doc.get("source", "Unknown Document"),
                        "content": doc["content"][:500] + "..." if len(doc["content"]) > 500 else doc["content"],
                        "relevance_score": doc["_additional"]["certainty"],
                        "source": doc.get("source", "weaviate"),
                        "metadata": doc.get("metadata", {}),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
        except Exception as doc_e:
            logger.warning(f"Documents search failed: {doc_e}")

        # Search in Conversations class if it exists
        try:
            conversations_result = (
                weaviate_client.query
                .get("Conversations", ["content", "title", "metadata"])
                .with_near_text({"concepts": [query]})
                .with_limit(limit // 2 if search_results else limit)
                .with_additional(["certainty", "id"])
                .do()
            )
            
            if "data" in conversations_result and "Get" in conversations_result["data"] and "Conversations" in conversations_result["data"]["Get"]:
                for conv in conversations_result["data"]["Get"]["Conversations"]:
                    search_results.append({
                        "id": conv["_additional"]["id"],
                        "type": "conversation",
                        "title": conv.get("title", "Conversation"),
                        "content": conv["content"][:500] + "..." if len(conv["content"]) > 500 else conv["content"],
                        "relevance_score": conv["_additional"]["certainty"],
                        "source": "conversation",
                        "metadata": conv.get("metadata", {}),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
        except Exception as conv_e:
            logger.warning(f"Conversations search failed: {conv_e}")

        # Sort by relevance score
        search_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return {
            "query": query,
            "results": search_results[:limit],
            "count": len(search_results[:limit]),
            "service": SERVICE_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to search context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vectors/stats")
async def get_vector_stats():
    """Get vector database statistics"""
    try:
        if not weaviate_client:
            return {
                "stats": {
                    "total_vectors": 0,
                    "collections": {},
                    "dimensions": 0,
                    "index_type": "Weaviate HNSW",
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "status": "not_configured"
                },
                "service": SERVICE_NAME,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        # Get real Weaviate stats
        cluster_stats = weaviate_client.cluster.get_nodes_status()
        
        # Get schema information
        schema = weaviate_client.schema.get()
        collections = {}
        total_vectors = 0
        
        for cls in schema.get("classes", []):
            class_name = cls["class"]
            try:
                # Get object count for each class
                result = weaviate_client.query.aggregate(class_name).with_meta_count().do()
                count = result.get("data", {}).get("Aggregate", {}).get(class_name, [{}])[0].get("meta", {}).get("count", 0)
                collections[class_name] = count
                total_vectors += count
            except Exception as class_e:
                logger.warning(f"Could not get count for class {class_name}: {class_e}")
                collections[class_name] = 0

        stats = {
            "total_vectors": total_vectors,
            "collections": collections,
            "dimensions": 1536,  # OpenAI embedding dimensions
            "index_type": "Weaviate HNSW",
            "cluster_status": cluster_stats,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "status": "connected"
        }

        return {
            "stats": stats,
            "service": SERVICE_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get vector stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory")
async def get_memory_context(user_id: str, context_type: str = "recent"):
    """Get contextual memory for a user"""
    try:
        # Placeholder for memory data
        memory = {
            "user_id": user_id,
            "context_type": context_type,
            "items": [
                {
                    "id": "mem_001",
                    "type": "conversation_summary",
                    "content": "User is focused on Q4 strategy and market expansion",
                    "importance": 0.9,
                    "last_accessed": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": "mem_002",
                    "type": "preference",
                    "content": "Prefers detailed analysis with data visualizations",
                    "importance": 0.7,
                    "last_accessed": datetime.now(timezone.utc).isoformat()
                }
            ],
            "total_items": 2,
            "memory_strength": 0.85
        }

        return {
            "memory": memory,
            "service": SERVICE_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get memory context for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def get_documents(user_id: Optional[str] = None, limit: int = 20):
    """Get indexed documents"""
    try:
        # Placeholder for documents data
        documents = [
            {
                "id": "doc_001",
                "title": "Q4 Strategy Document",
                "type": "pdf",
                "size": 2048576,
                "chunks": 45,
                "indexed_at": datetime.now(timezone.utc).isoformat(),
                "last_accessed": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "doc_002",
                "title": "Market Analysis Report",
                "type": "docx",
                "size": 1536000,
                "chunks": 32,
                "indexed_at": datetime.now(timezone.utc).isoformat(),
                "last_accessed": datetime.now(timezone.utc).isoformat()
            }
        ]

        return {
            "documents": documents[:limit],
            "count": len(documents[:limit]),
            "service": SERVICE_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/doc/upsert", response_model=DocumentResponse)
async def upsert_document(document: DocumentUpsert):
    """
    Document upsert endpoint for storing documents in Weaviate.
    Stores documents with vector embeddings in Weaviate Cloud.
    """
    try:
        # Generate document ID if not provided
        doc_id = document.id or str(uuid.uuid4())
        
        # Store document in staging area (in-memory for now)
        doc_data = {
            "doc_id": doc_id,
            "account_id": document.account_id,
            "content": document.content,
            "url": document.url,
            "metadata": document.metadata or {},
            "status": "processing",
            "staged_at": datetime.now(timezone.utc).isoformat(),
            "vector_indexed": False
        }
        
        _document_store[doc_id] = doc_data
        
        # Store in Weaviate if configured
        if weaviate_client:
            try:
                # Prepare data object
                data_object = {
                    "content": document.content,
                    "source": document.url or f"account_{document.account_id}",
                    "account_id": document.account_id,
                    "doc_id": doc_id,
                    "metadata": document.metadata or {},
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                # Store in Documents class
                weaviate_client.data_object.create(
                    data_object=data_object,
                    class_name="Documents",
                    uuid=doc_id
                )
                
                # Update status
                _document_store[doc_id]["status"] = "indexed"
                _document_store[doc_id]["vector_indexed"] = True
                
                logger.info(f"Document {doc_id} indexed in Weaviate for account {document.account_id}")
                
                return DocumentResponse(
                    doc_id=doc_id,
                    status="indexed",
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
                
            except Exception as weaviate_e:
                logger.error(f"Failed to store in Weaviate: {weaviate_e}")
                _document_store[doc_id]["status"] = "staged"
                
                return DocumentResponse(
                    doc_id=doc_id,
                    status="staged",
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
        else:
            logger.warning("Weaviate not configured, document staged only")
            return DocumentResponse(
                doc_id=doc_id,
                status="staged",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
    except Exception as e:
        logger.error(f"Failed to upsert document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/doc/{doc_id}")
async def get_document(doc_id: str):
    """Retrieve document by ID"""
    try:
        # Check if document exists in store
        if doc_id not in _document_store:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
        
        doc_data = _document_store[doc_id]
        
        return {
            "document": doc_data,
            "service": SERVICE_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard")
async def get_context_dashboard():
    """Get context service dashboard overview"""
    try:
        # Placeholder for dashboard data
        dashboard = {
            "total_conversations": 1250,
            "total_messages": 25000,
            "total_documents": len(_document_store),
            "staged_documents": sum(1 for d in _document_store.values() if d.get("status") == "staged"),
            "indexed_documents": sum(1 for d in _document_store.values() if d.get("vector_indexed")),
            "total_vectors": 125000,
            "storage_used": "2.4GB",
            "avg_response_time": 45,  # ms
            "cache_hit_rate": 0.87,
            "recent_activity": [
                {
                    "type": "conversation_created",
                    "description": "New conversation started",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                {
                    "type": "document_indexed",
                    "description": "Market report indexed successfully",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            ]
        }

        return {
            "dashboard": dashboard,
            "service": SERVICE_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get context dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)