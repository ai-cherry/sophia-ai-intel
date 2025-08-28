from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

app = FastAPI(title="MCP Salesforce Integration")

# Simulated Salesforce data
leads = {}
opportunities = {}
accounts = {}
contacts = {}

class Lead(BaseModel):
    company: str
    email: str
    first_name: str
    last_name: str
    status: Optional[str] = "Open"
    source: Optional[str] = "Web"

class Opportunity(BaseModel):
    name: str
    account_id: str
    amount: float
    stage: str
    close_date: str
    probability: Optional[int] = 50

@app.get("/")
async def root():
    return {
        "service": "MCP Salesforce Integration",
        "status": "active",
        "capabilities": ["leads", "opportunities", "accounts", "contacts", "analytics"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "leads": len(leads), "opportunities": len(opportunities)}

@app.post("/leads/create")
async def create_lead(lead: Lead):
    """Create a new lead"""
    lead_id = str(uuid.uuid4())
    leads[lead_id] = {
        "id": lead_id,
        "company": lead.company,
        "email": lead.email,
        "first_name": lead.first_name,
        "last_name": lead.last_name,
        "status": lead.status,
        "source": lead.source,
        "created_date": datetime.now().isoformat()
    }
    return {"status": "created", "lead_id": lead_id, "message": f"Lead for {lead.company} created"}

@app.get("/leads")
async def get_leads(status: Optional[str] = None):
    """Get all leads"""
    lead_list = list(leads.values())
    if status:
        lead_list = [l for l in lead_list if l["status"] == status]
    return {"leads": lead_list, "total": len(lead_list)}

@app.post("/opportunities/create")
async def create_opportunity(opp: Opportunity):
    """Create opportunity"""
    opp_id = str(uuid.uuid4())
    opportunities[opp_id] = {
        "id": opp_id,
        "name": opp.name,
        "account_id": opp.account_id,
        "amount": opp.amount,
        "stage": opp.stage,
        "close_date": opp.close_date,
        "probability": opp.probability,
        "created_date": datetime.now().isoformat()
    }
    return {"status": "created", "opportunity_id": opp_id, "message": f"Opportunity {opp.name} created"}

@app.get("/analytics/pipeline")
async def get_pipeline_analytics():
    """Get sales pipeline analytics"""
    stages = {}
    total_value = 0
    
    for opp in opportunities.values():
        stage = opp["stage"]
        if stage not in stages:
            stages[stage] = {"count": 0, "value": 0}
        stages[stage]["count"] += 1
        stages[stage]["value"] += opp["amount"]
        total_value += opp["amount"]
    
    return {
        "total_opportunities": len(opportunities),
        "total_pipeline_value": total_value,
        "by_stage": stages,
        "average_deal_size": total_value / len(opportunities) if opportunities else 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8092)
