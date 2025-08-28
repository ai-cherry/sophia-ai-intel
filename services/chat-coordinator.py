from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
import asyncio
from datetime import datetime

app = FastAPI(title="Sophia Chat Coordinator")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    context: Optional[Dict[str, Any]] = {}

class ChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}

async def search_web(query: str) -> str:
    """Search web using MCP Research service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8085/research",
                json={"query": query, "sources": ["web", "news"], "limit": 3}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    result = data["results"][0]
                    return f"Based on recent information: {result['summary']}"
    except:
        pass
    return None

async def search_context(query: str) -> str:
    """Search context documents"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8081/documents/search",
                json={"query": query, "limit": 3}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    return f"From knowledge base: {data['results'][0]['content'][:200]}..."
    except:
        pass
    return None

async def check_agent_capability(query: str) -> str:
    """Check if query needs agent assistance"""
    keywords = ["code", "swarm", "agent", "deploy", "github", "commit"]
    if any(keyword in query.lower() for keyword in keywords):
        return "I can help with coding and agent orchestration. Use the Agent Swarm interface for direct agent control, or I can assist with code generation and GitHub integration here."
    return None

def process_query(query: str) -> Dict[str, Any]:
    """Analyze query and determine response strategy"""
    query_lower = query.lower()
    
    # Common queries with direct answers
    if "president" in query_lower and ("us" in query_lower or "united states" in query_lower):
        return {
            "type": "direct",
            "answer": "As of 2024, Joe Biden is the President of the United States. He has been serving since January 20, 2021."
        }
    
    if "who are you" in query_lower or "what are you" in query_lower:
        return {
            "type": "direct",
            "answer": "I'm Sophia AI, an intelligent multi-agent platform. I can help with research, coding, data analysis, and coordinate various AI agents to assist with complex tasks."
        }
    
    # Determine if web search needed
    if any(word in query_lower for word in ["search", "find", "latest", "current", "news"]):
        return {"type": "search", "query": query}
    
    # Check for agent/coding queries
    if any(word in query_lower for word in ["code", "agent", "swarm", "github"]):
        return {"type": "agent", "query": query}
    
    # Default to context search
    return {"type": "context", "query": query}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process chat messages through appropriate services"""
    
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    # Get the latest user message
    user_message = request.messages[-1].content
    
    # Analyze query
    analysis = process_query(user_message)
    
    response_text = ""
    sources = []
    
    if analysis["type"] == "direct":
        response_text = analysis["answer"]
        
    elif analysis["type"] == "search":
        # Try web search first
        web_result = await search_web(user_message)
        if web_result:
            response_text = web_result
            sources.append({"type": "web", "service": "mcp-research"})
        else:
            # Fallback to context
            context_result = await search_context(user_message)
            if context_result:
                response_text = context_result
                sources.append({"type": "context", "service": "mcp-context"})
                
    elif analysis["type"] == "agent":
        agent_response = await check_agent_capability(user_message)
        if agent_response:
            response_text = agent_response
            sources.append({"type": "agent", "service": "agno-coordinator"})
            
    else:
        # Try context search
        context_result = await search_context(user_message)
        if context_result:
            response_text = context_result
            sources.append({"type": "context", "service": "mcp-context"})
    
    # Fallback response
    if not response_text:
        response_text = f"I understand you're asking about '{user_message}'. Let me help you with that. The system has multiple services available including web search, document context, and agent orchestration. Could you provide more details about what you need?"
    
    return ChatResponse(
        response=response_text,
        sources=sources,
        metadata={
            "query_type": analysis["type"],
            "timestamp": datetime.now().isoformat(),
            "services_used": [s["service"] for s in sources]
        }
    )

@app.get("/")
async def root():
    return {
        "service": "Sophia Chat Coordinator",
        "status": "active",
        "capabilities": ["chat", "web_search", "context_search", "agent_coordination"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8095)
