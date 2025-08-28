from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json

app = FastAPI(title="MCP HubSpot Integration")

# Simulated HubSpot data store
contacts = {}
companies = {}
deals = {}
tickets = {}

class Contact(BaseModel):
    email: str
    firstname: Optional[str] = ""
    lastname: Optional[str] = ""
    company: Optional[str] = ""
    properties: Optional[Dict[str, Any]] = {}

class Deal(BaseModel):
    name: str
    amount: float
    stage: str
    contact_id: Optional[str] = None
    close_date: Optional[str] = None

class Ticket(BaseModel):
    subject: str
    content: str
    priority: Optional[str] = "LOW"
    status: Optional[str] = "open"
    contact_id: Optional[str] = None

@app.get("/")
async def root():
    return {
        "service": "MCP HubSpot Integration",
        "status": "active",
        "capabilities": ["contacts", "companies", "deals", "tickets", "analytics"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "contacts": len(contacts), "deals": len(deals)}

# Contacts endpoints
@app.post("/contacts/create")
async def create_contact(contact: Contact):
    """Create a new contact in HubSpot"""
    contact_id = str(uuid.uuid4())
    
    contacts[contact_id] = {
        "id": contact_id,
        "email": contact.email,
        "firstname": contact.firstname,
        "lastname": contact.lastname,
        "company": contact.company,
        "properties": contact.properties,
        "created_at": datetime.now().isoformat(),
        "lifecycle_stage": "lead"
    }
    
    return {
        "status": "created",
        "contact_id": contact_id,
        "message": f"Contact {contact.email} created successfully"
    }

@app.get("/contacts")
async def list_contacts(limit: int = 10):
    """List all contacts"""
    contact_list = list(contacts.values())[:limit]
    return {
        "contacts": contact_list,
        "total": len(contacts),
        "limit": limit
    }

@app.get("/contacts/{contact_id}")
async def get_contact(contact_id: str):
    """Get contact by ID"""
    if contact_id not in contacts:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contacts[contact_id]

@app.post("/contacts/search")
async def search_contacts(query: Dict[str, Any]):
    """Search contacts"""
    search_term = query.get("query", "").lower()
    results = []
    
    for contact in contacts.values():
        if (search_term in contact.get("email", "").lower() or
            search_term in contact.get("firstname", "").lower() or
            search_term in contact.get("lastname", "").lower()):
            results.append(contact)
    
    return {"results": results, "total": len(results)}

# Deals endpoints
@app.post("/deals/create")
async def create_deal(deal: Deal):
    """Create a new deal"""
    deal_id = str(uuid.uuid4())
    
    deals[deal_id] = {
        "id": deal_id,
        "name": deal.name,
        "amount": deal.amount,
        "stage": deal.stage,
        "contact_id": deal.contact_id,
        "close_date": deal.close_date or datetime.now().isoformat(),
        "created_at": datetime.now().isoformat(),
        "pipeline": "default"
    }
    
    return {
        "status": "created",
        "deal_id": deal_id,
        "message": f"Deal '{deal.name}' created successfully"
    }

@app.get("/deals")
async def list_deals(stage: Optional[str] = None):
    """List deals, optionally filtered by stage"""
    deal_list = list(deals.values())
    
    if stage:
        deal_list = [d for d in deal_list if d["stage"] == stage]
    
    return {
        "deals": deal_list,
        "total": len(deal_list),
        "total_value": sum(d["amount"] for d in deal_list)
    }

# Analytics endpoints
@app.get("/analytics/summary")
async def get_analytics_summary():
    """Get analytics summary"""
    total_deal_value = sum(d["amount"] for d in deals.values())
    
    # Calculate conversion funnel
    stages = {}
    for deal in deals.values():
        stage = deal["stage"]
        if stage not in stages:
            stages[stage] = {"count": 0, "value": 0}
        stages[stage]["count"] += 1
        stages[stage]["value"] += deal["amount"]
    
    return {
        "contacts": {
            "total": len(contacts),
            "new_this_month": len([c for c in contacts.values() 
                                  if "2024-11" in c.get("created_at", "")])
        },
        "deals": {
            "total": len(deals),
            "total_value": total_deal_value,
            "average_value": total_deal_value / len(deals) if deals else 0,
            "by_stage": stages
        },
        "tickets": {
            "total": len(tickets),
            "open": len([t for t in tickets.values() if t.get("status") == "open"])
        }
    }

# Tickets endpoints
@app.post("/tickets/create")
async def create_ticket(ticket: Ticket):
    """Create support ticket"""
    ticket_id = str(uuid.uuid4())
    
    tickets[ticket_id] = {
        "id": ticket_id,
        "subject": ticket.subject,
        "content": ticket.content,
        "priority": ticket.priority,
        "status": ticket.status,
        "contact_id": ticket.contact_id,
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "status": "created",
        "ticket_id": ticket_id,
        "message": f"Ticket '{ticket.subject}' created"
    }

# Integration endpoints
@app.post("/sync/contacts")
async def sync_contacts_from_external(data: Dict[str, Any]):
    """Sync contacts from external system"""
    synced = 0
    for external_contact in data.get("contacts", []):
        contact = Contact(
            email=external_contact.get("email"),
            firstname=external_contact.get("first_name"),
            lastname=external_contact.get("last_name")
        )
        await create_contact(contact)
        synced += 1
    
    return {
        "status": "synced",
        "contacts_synced": synced,
        "message": f"Successfully synced {synced} contacts"
    }

@app.post("/automation/trigger")
async def trigger_automation(automation: Dict[str, Any]):
    """Trigger HubSpot automation workflow"""
    workflow_name = automation.get("workflow")
    contact_ids = automation.get("contact_ids", [])
    
    # Simulate workflow execution
    results = []
    for contact_id in contact_ids:
        if contact_id in contacts:
            results.append({
                "contact_id": contact_id,
                "workflow": workflow_name,
                "status": "triggered",
                "timestamp": datetime.now().isoformat()
            })
    
    return {
        "workflow": workflow_name,
        "contacts_processed": len(results),
        "results": results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)
