from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

app = FastAPI(title="MCP Gong Integration")

# Simulated call recordings and insights
calls = {}
insights = {}

class CallRecording(BaseModel):
    participant_emails: List[str]
    duration_minutes: int
    title: str
    recording_url: Optional[str] = ""
    tags: Optional[List[str]] = []

class CallInsight(BaseModel):
    call_id: str
    key_topics: List[str]
    sentiment: str
    action_items: List[str]
    competitors_mentioned: List[str]

@app.get("/")
async def root():
    return {
        "service": "MCP Gong Integration",
        "status": "active",
        "capabilities": ["call_recording", "conversation_insights", "coaching", "analytics"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "calls": len(calls), "insights": len(insights)}

@app.post("/calls/record")
async def record_call(call: CallRecording):
    """Record a new call"""
    call_id = str(uuid.uuid4())
    calls[call_id] = {
        "id": call_id,
        "participant_emails": call.participant_emails,
        "duration_minutes": call.duration_minutes,
        "title": call.title,
        "recording_url": call.recording_url or f"https://gong.io/calls/{call_id}",
        "tags": call.tags,
        "recorded_at": datetime.now().isoformat()
    }
    return {"status": "recorded", "call_id": call_id, "message": f"Call '{call.title}' recorded"}

@app.post("/insights/analyze")
async def analyze_call(insight: CallInsight):
    """Analyze call for insights"""
    insight_id = str(uuid.uuid4())
    insights[insight_id] = {
        "id": insight_id,
        "call_id": insight.call_id,
        "key_topics": insight.key_topics,
        "sentiment": insight.sentiment,
        "action_items": insight.action_items,
        "competitors_mentioned": insight.competitors_mentioned,
        "analyzed_at": datetime.now().isoformat()
    }
    return {"status": "analyzed", "insight_id": insight_id, "summary": {
        "sentiment": insight.sentiment,
        "topics": len(insight.key_topics),
        "action_items": len(insight.action_items)
    }}

@app.get("/calls")
async def get_calls(tag: Optional[str] = None):
    """Get all calls"""
    call_list = list(calls.values())
    if tag:
        call_list = [c for c in call_list if tag in c.get("tags", [])]
    return {"calls": call_list, "total": len(call_list)}

@app.get("/analytics/summary")
async def get_analytics():
    """Get conversation analytics"""
    total_duration = sum(c["duration_minutes"] for c in calls.values())
    sentiments = {}
    all_topics = []
    
    for ins in insights.values():
        sentiment = ins["sentiment"]
        sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
        all_topics.extend(ins["key_topics"])
    
    return {
        "total_calls": len(calls),
        "total_duration_minutes": total_duration,
        "average_call_length": total_duration / len(calls) if calls else 0,
        "sentiments": sentiments,
        "top_topics": list(set(all_topics))[:10],
        "insights_generated": len(insights)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8091)
