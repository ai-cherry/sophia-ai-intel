"""Context management module - consolidated from mcp-context"""
import asyncio
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ContextResult:
    source: str
    content: str
    score: float

class ContextManager:
    def __init__(self):
        self.vector_store = {}
        
    async def initialize(self):
        self.vector_store = {}  # Simple in-memory store for now
        
    async def health_check(self):
        return {"status": "healthy", "indexed_docs": len(self.vector_store)}
        
    async def search(self, query: str, limit: int = 10) -> List[ContextResult]:
        # Simple mock search - replace with actual vector search
        results = []
        for i, (key, content) in enumerate(list(self.vector_store.items())[:limit]):
            results.append(ContextResult(
                source=key,
                content=content[:200],
                score=0.8 - (i * 0.1)
            ))
        return results
        
    async def index(self, content: str, metadata: Dict[str, Any]):
        doc_id = metadata.get("id", f"doc_{len(self.vector_store)}")
        self.vector_store[doc_id] = content
        return {"id": doc_id, "indexed": True}
        
    async def cleanup(self):
        self.vector_store.clear()