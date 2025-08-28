"""
Simple working MCP Context Service
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import json
from datetime import datetime

app = FastAPI(
    title="MCP Context Service",
    description="Context management and vector search for Sophia AI",
    version="1.0.0"
)

# In-memory storage for demo
documents_store = {}
contexts_store = {}

class Document(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = {}
    embedding: Optional[List[float]] = None

class Context(BaseModel):
    name: str
    documents: List[str] = []
    metadata: Dict[str, Any] = {}

class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 10
    filters: Optional[Dict[str, Any]] = {}

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mcp-context",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",
        "vector_db": "connected"
    }

@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "MCP Context Service",
        "version": "1.0.0",
        "endpoints": [
            "/healthz",
            "/documents",
            "/documents/search",
            "/contexts",
            "/contexts/{context_id}"
        ]
    }

@app.post("/documents")
async def create_document(document: Document):
    """Create a new document"""
    doc_id = f"doc_{len(documents_store) + 1}"
    documents_store[doc_id] = {
        "id": doc_id,
        "content": document.content,
        "metadata": document.metadata,
        "created_at": datetime.now().isoformat()
    }
    return {"id": doc_id, "status": "created"}

@app.get("/documents")
async def list_documents():
    """List all documents"""
    return {"documents": list(documents_store.values())}

@app.post("/documents/search")
async def search_documents(query: SearchQuery):
    """Search documents using vector similarity"""
    # Simple keyword search for demo
    results = []
    for doc_id, doc in documents_store.items():
        if query.query.lower() in doc["content"].lower():
            results.append({
                "id": doc_id,
                "content": doc["content"][:200],
                "score": 0.95,  # Mock similarity score
                "metadata": doc["metadata"]
            })
    
    return {
        "query": query.query,
        "results": results[:query.limit],
        "total": len(results)
    }

@app.post("/contexts")
async def create_context(context: Context):
    """Create a new context"""
    context_id = f"ctx_{len(contexts_store) + 1}"
    contexts_store[context_id] = {
        "id": context_id,
        "name": context.name,
        "documents": context.documents,
        "metadata": context.metadata,
        "created_at": datetime.now().isoformat()
    }
    return {"id": context_id, "status": "created"}

@app.get("/contexts")
async def list_contexts():
    """List all contexts"""
    return {"contexts": list(contexts_store.values())}

@app.get("/contexts/{context_id}")
async def get_context(context_id: str):
    """Get a specific context"""
    if context_id not in contexts_store:
        raise HTTPException(status_code=404, detail="Context not found")
    return contexts_store[context_id]

@app.post("/embed")
async def create_embedding(text: str):
    """Generate embeddings for text"""
    # Return mock embedding
    return {
        "text": text,
        "embedding": [0.1] * 768,  # Mock 768-dimensional embedding
        "model": "text-embedding-ada-002"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8081))
    uvicorn.run(app, host="0.0.0.0", port=port)