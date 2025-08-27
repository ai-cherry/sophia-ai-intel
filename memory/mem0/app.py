import asyncio
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import os
from datetime import datetime, timedelta
import uuid
import redis.asyncio as redis
from collections import deque

app = FastAPI(title="Mem0 Memory Service")

# Redis connection for memory storage
redis_client = None

class Memory(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = {}
    ttl: Optional[int] = 3600  # Default 1 hour TTL

class MemoryQuery(BaseModel):
    query: str
    limit: Optional[int] = 10
    actor_id: Optional[str] = None

class MemoryResponse(BaseModel):
    memory_id: str
    content: str
    metadata: Dict[str, Any]
    created_at: str
    expires_at: Optional[str]

class ConversationContext(BaseModel):
    messages: List[Dict[str, str]]
    max_tokens: Optional[int] = 1000

# In-memory buffer for recent interactions (backup to Redis)
memory_buffer = {}

async def get_redis() -> redis.Redis:
    """Get Redis connection"""
    global redis_client
    if redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = await redis.from_url(redis_url, decode_responses=True)
    return redis_client

# SSE keep-alive
async def sse_keepalive():
    while True:
        await asyncio.sleep(25)
        # In production, send SSE ping here

@app.on_event("startup")
async def startup():
    asyncio.create_task(sse_keepalive())
    await get_redis()

@app.on_event("shutdown")
async def shutdown():
    global redis_client
    if redis_client:
        await redis_client.close()

@app.post("/memory/store", response_model=MemoryResponse)
async def store_memory(
    memory: Memory,
    x_tenant_id: str = Header(...),
    x_actor_id: str = Header(...)
):
    """Store a new memory with optional TTL"""
    memory_id = str(uuid.uuid4())
    
    # Create memory record
    memory_data = {
        "memory_id": memory_id,
        "tenant_id": x_tenant_id,
        "actor_id": x_actor_id,
        "content": memory.content,
        "metadata": json.dumps(memory.metadata),
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(seconds=memory.ttl)).isoformat() if memory.ttl else None
    }
    
    # Store in Redis with TTL
    client = await get_redis()
    key = f"memory:{x_tenant_id}:{x_actor_id}:{memory_id}"
    
    await client.hset(key, mapping=memory_data)
    if memory.ttl:
        await client.expire(key, memory.ttl)
    
    # Also store in actor's memory list
    list_key = f"memories:{x_tenant_id}:{x_actor_id}"
    await client.lpush(list_key, memory_id)
    await client.ltrim(list_key, 0, 99)  # Keep last 100 memories
    
    # Update local buffer
    if x_actor_id not in memory_buffer:
        memory_buffer[x_actor_id] = deque(maxlen=20)
    memory_buffer[x_actor_id].append({
        "memory_id": memory_id,
        "content": memory.content,
        "timestamp": datetime.utcnow()
    })
    
    return MemoryResponse(
        memory_id=memory_id,
        content=memory.content,
        metadata=memory.metadata,
        created_at=memory_data["created_at"],
        expires_at=memory_data.get("expires_at")
    )

@app.get("/memory/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    x_tenant_id: str = Header(...),
    x_actor_id: str = Header(...)
):
    """Retrieve a specific memory by ID"""
    client = await get_redis()
    key = f"memory:{x_tenant_id}:{x_actor_id}:{memory_id}"
    
    memory_data = await client.hgetall(key)
    if not memory_data:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return MemoryResponse(
        memory_id=memory_id,
        content=memory_data["content"],
        metadata=json.loads(memory_data.get("metadata", "{}")),
        created_at=memory_data["created_at"],
        expires_at=memory_data.get("expires_at")
    )

@app.post("/memory/search", response_model=List[MemoryResponse])
async def search_memories(
    query: MemoryQuery,
    x_tenant_id: str = Header(...),
    x_actor_id: str = Header(...)
):
    """Search memories for an actor"""
    actor_id = query.actor_id or x_actor_id
    client = await get_redis()
    
    # Get memory IDs for actor
    list_key = f"memories:{x_tenant_id}:{actor_id}"
    memory_ids = await client.lrange(list_key, 0, query.limit - 1)
    
    memories = []
    for memory_id in memory_ids:
        key = f"memory:{x_tenant_id}:{actor_id}:{memory_id}"
        memory_data = await client.hgetall(key)
        
        if memory_data:
            # Simple text matching (in production, use vector search)
            if query.query.lower() in memory_data["content"].lower():
                memories.append(MemoryResponse(
                    memory_id=memory_id,
                    content=memory_data["content"],
                    metadata=json.loads(memory_data.get("metadata", "{}")),
                    created_at=memory_data["created_at"],
                    expires_at=memory_data.get("expires_at")
                ))
    
    return memories[:query.limit]

@app.post("/memory/summarize")
async def summarize_conversation(
    context: ConversationContext,
    x_tenant_id: str = Header(...),
    x_actor_id: str = Header(...)
):
    """Summarize a conversation and store as memory"""
    # Extract key points from conversation
    key_points = []
    for msg in context.messages[-5:]:  # Last 5 messages
        if msg.get("role") == "assistant":
            key_points.append(msg.get("content", "")[:200])
    
    # Create summary (in production, use LLM)
    summary = f"Conversation summary: {'; '.join(key_points)}"
    
    # Store as memory
    memory = Memory(
        content=summary,
        metadata={
            "type": "conversation_summary",
            "message_count": len(context.messages)
        },
        ttl=7200  # 2 hours for conversation summaries
    )
    
    return await store_memory(memory, x_tenant_id=x_tenant_id, x_actor_id=x_actor_id)

@app.delete("/memory/{memory_id}")
async def delete_memory(
    memory_id: str,
    x_tenant_id: str = Header(...),
    x_actor_id: str = Header(...)
):
    """Delete a specific memory"""
    client = await get_redis()
    key = f"memory:{x_tenant_id}:{x_actor_id}:{memory_id}"
    
    deleted = await client.delete(key)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    # Remove from list
    list_key = f"memories:{x_tenant_id}:{x_actor_id}"
    await client.lrem(list_key, 1, memory_id)
    
    return {"status": "deleted", "memory_id": memory_id}

@app.delete("/memory/clear")
async def clear_memories(
    x_tenant_id: str = Header(...),
    x_actor_id: str = Header(...)
):
    """Clear all memories for an actor"""
    client = await get_redis()
    
    # Get all memory IDs
    list_key = f"memories:{x_tenant_id}:{x_actor_id}"
    memory_ids = await client.lrange(list_key, 0, -1)
    
    # Delete each memory
    for memory_id in memory_ids:
        key = f"memory:{x_tenant_id}:{x_actor_id}:{memory_id}"
        await client.delete(key)
    
    # Clear the list
    await client.delete(list_key)
    
    # Clear local buffer
    if x_actor_id in memory_buffer:
        del memory_buffer[x_actor_id]
    
    return {"status": "cleared", "memories_deleted": len(memory_ids)}

@app.get("/memory/recent")
async def get_recent_memories(
    limit: int = 10,
    x_tenant_id: str = Header(...),
    x_actor_id: str = Header(...)
):
    """Get recent memories from buffer (fast access)"""
    if x_actor_id in memory_buffer:
        recent = list(memory_buffer[x_actor_id])[-limit:]
        return {"memories": recent}
    return {"memories": []}

@app.get("/health")
async def health():
    try:
        client = await get_redis()
        await client.ping()
        redis_status = "healthy"
    except:
        redis_status = "unhealthy"
    
    return {
        "status": "healthy",
        "service": "mem0",
        "redis": redis_status,
        "buffer_size": sum(len(v) for v in memory_buffer.values())
    }