#!/usr/bin/env python3
"""
HubSpot MCP Service - CRM Integration
====================================

HubSpot integration for Sophia AI platform.
Provides access to contacts, deals, companies, and sales pipeline data.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

import aiohttp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Environment configuration
HUBSPOT_ACCESS_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN", "")
HUBSPOT_CLIENT_SECRET = os.getenv("HUBSPOT_CLIENT_SECRET", "")
TENANT = os.getenv("TENANT", "pay-ready")

app = FastAPI(
    title="Sophia AI HubSpot MCP Service",
    description="CRM integration and sales pipeline management",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HubSpotClient:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.hubapi.com"
        self.connected = bool(access_token)
    
    async def get_contacts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get contacts from HubSpot"""
        if not self.connected:
            return []
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {"limit": limit, "properties": "email,firstname,lastname,company"}
            
            try:
                async with session.get(f"{self.base_url}/crm/v3/objects/contacts", 
                                     headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("results", [])
                    else:
                        logger.error(f"HubSpot contacts API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"HubSpot contacts request failed: {e}")
                return []
    
    async def get_deals(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get deals from HubSpot"""
        if not self.connected:
            return []
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {"limit": limit, "properties": "dealname,amount,dealstage,closedate"}
            
            try:
                async with session.get(f"{self.base_url}/crm/v3/objects/deals",
                                     headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("results", [])
                    else:
                        logger.error(f"HubSpot deals API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"HubSpot deals request failed: {e}")
                return []

hubspot_client = HubSpotClient(HUBSPOT_ACCESS_TOKEN)

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    hubspot_status = "connected" if HUBSPOT_ACCESS_TOKEN else "no_access_token"
    
    if HUBSPOT_ACCESS_TOKEN:
        try:
            contacts = await hubspot_client.get_contacts(1)
            hubspot_status = f"connected ({len(contacts)} contacts accessible)"
        except Exception as e:
            hubspot_status = f"error: {str(e)[:50]}"
    
    return {
        "status": "healthy",
        "hubspot_connection": hubspot_status,
        "tenant": TENANT,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/")
async def root():
    return {
        "service": "Sophia AI HubSpot MCP",
        "version": "2.0.0", 
        "status": "operational",
        "hubspot_configured": bool(HUBSPOT_ACCESS_TOKEN),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/contacts")
async def get_contacts(limit: int = 50):
    """Get HubSpot contacts"""
    try:
        contacts = await hubspot_client.get_contacts(limit)
        return {
            "contacts": contacts,
            "count": len(contacts),
            "tenant": TENANT,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/deals")  
async def get_deals(limit: int = 50):
    """Get HubSpot deals"""
    try:
        deals = await hubspot_client.get_deals(limit)
        return {
            "deals": deals,
            "count": len(deals), 
            "tenant": TENANT,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipeline")
async def get_pipeline():
    """Get sales pipeline summary"""
    try:
        deals = await hubspot_client.get_deals(100)
        contacts = await hubspot_client.get_contacts(100)
        
        # Analyze pipeline
        pipeline_summary = {
            "total_deals": len(deals),
            "total_contacts": len(contacts),
            "deal_stages": {},
            "total_value": 0
        }
        
        for deal in deals:
            stage = deal.get("properties", {}).get("dealstage", "unknown")
            amount = deal.get("properties", {}).get("amount")
            
            if stage not in pipeline_summary["deal_stages"]:
                pipeline_summary["deal_stages"][stage] = 0
            pipeline_summary["deal_stages"][stage] += 1
            
            if amount:
                try:
                    pipeline_summary["total_value"] += float(amount)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse deal amount {amount}: {e}")
        
        return {
            "pipeline": pipeline_summary,
            "tenant": TENANT,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
