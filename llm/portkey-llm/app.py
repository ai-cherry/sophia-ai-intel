import asyncio
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import json
import os

app = FastAPI(title="Portkey LLM Service")

class SummarizeRequest(BaseModel):
    content: str
    prompt_template: Optional[str] = None
    max_tokens: Optional[int] = 500
    model: Optional[str] = "gpt-4"

class SummarizeResponse(BaseModel):
    summary: str
    model_used: str
    token_count: int

# SSE keep-alive
async def sse_keepalive():
    while True:
        await asyncio.sleep(25)
        # In production, send SSE ping here

@app.on_event("startup")
async def startup():
    asyncio.create_task(sse_keepalive())

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    request: SummarizeRequest,
    x_tenant_id: str = Header(...),
    x_actor_id: str = Header(...)
):
    """Summarize content using Portkey AI Gateway"""
    
    portkey_api_key = os.getenv("PORTKEY_API_KEY")
    if not portkey_api_key:
        raise HTTPException(status_code=500, detail="PORTKEY_API_KEY not configured")
    
    # Default prompt template for call summarization
    if not request.prompt_template:
        request.prompt_template = """
        Summarize the following call transcript in a concise manner:
        - Key discussion points
        - Action items identified
        - Important decisions made
        - Next steps
        
        Transcript:
        {content}
        
        Summary:
        """
    
    prompt = request.prompt_template.format(content=request.content)
    
    # Call Portkey API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.portkey.ai/v1/chat/completions",
                headers={
                    "x-portkey-api-key": portkey_api_key,
                    "x-portkey-mode": "single",
                    "Content-Type": "application/json"
                },
                json={
                    "model": request.model,
                    "messages": [
                        {"role": "system", "content": "You are a professional summarizer."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": request.max_tokens,
                    "temperature": 0.3
                }
            )
            response.raise_for_status()
            data = response.json()
            
            summary = data["choices"][0]["message"]["content"]
            token_count = data.get("usage", {}).get("total_tokens", 0)
            
            return SummarizeResponse(
                summary=summary,
                model_used=request.model,
                token_count=token_count
            )
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "portkey-llm"}