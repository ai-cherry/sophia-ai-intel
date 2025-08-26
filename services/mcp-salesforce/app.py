#!/usr/bin/env python3
"""
Salesforce MCP Service - CRM Integration
========================================

Salesforce integration for Sophia AI platform.
Provides access to leads, accounts, opportunities, and sales data.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

import aiohttp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import base64

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Environment configuration
SALESFORCE_CLIENT_ID = os.getenv("SALESFORCE_CLIENT_ID", "")
SALESFORCE_CLIENT_SECRET = os.getenv("SALESFORCE_CLIENT_SECRET", "")
SALESFORCE_USERNAME = os.getenv("SALESFORCE_USERNAME", "")
SALESFORCE_PASSWORD = os.getenv("SALESFORCE_PASSWORD", "")
SALESFORCE_INSTANCE_URL = os.getenv("SALESFORCE_INSTANCE_URL", "")
TENANT = os.getenv("TENANT", "pay-ready")

app = FastAPI(
    title="Sophia AI Salesforce MCP Service",
    description="Salesforce CRM integration and sales pipeline management",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SalesforceClient:
    def __init__(self, client_id: str, client_secret: str, username: str, password: str, instance_url: str = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.instance_url = instance_url
        self.access_token = None
        self.connected = bool(client_id and client_secret and username and password)

    async def authenticate(self) -> bool:
        """Authenticate with Salesforce and get access token"""
        if not self.connected:
            return False

        async with aiohttp.ClientSession() as session:
            # Use password flow for authentication
            auth_data = {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.username,
                "password": self.password
            }

            try:
                async with session.post(
                    "https://login.salesforce.com/services/oauth2/token",
                    data=auth_data
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.access_token = data.get("access_token")
                        self.instance_url = data.get("instance_url")
                        return True
                    else:
                        logger.error(f"Salesforce auth error: {response.status}")
                        return False
            except Exception as e:
                logger.error(f"Salesforce auth request failed: {e}")
                return False

    async def get_accounts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get accounts from Salesforce"""
        if not self.access_token or not self.instance_url:
            if not await self.authenticate():
                return []

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.access_token}"}

            try:
                query = f"SELECT Id, Name, Type, Industry, AnnualRevenue FROM Account LIMIT {limit}"
                params = {"q": query}

                async with session.get(
                    f"{self.instance_url}/services/data/v59.0/query",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("records", [])
                    else:
                        logger.error(f"Salesforce accounts API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Salesforce accounts request failed: {e}")
                return []

    async def get_opportunities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get opportunities from Salesforce"""
        if not self.access_token or not self.instance_url:
            if not await self.authenticate():
                return []

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.access_token}"}

            try:
                query = f"SELECT Id, Name, StageName, Amount, CloseDate, Account.Name FROM Opportunity LIMIT {limit}"
                params = {"q": query}

                async with session.get(
                    f"{self.instance_url}/services/data/v59.0/query",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("records", [])
                    else:
                        logger.error(f"Salesforce opportunities API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Salesforce opportunities request failed: {e}")
                return []

salesforce_client = SalesforceClient(
    SALESFORCE_CLIENT_ID,
    SALESFORCE_CLIENT_SECRET,
    SALESFORCE_USERNAME,
    SALESFORCE_PASSWORD,
    SALESFORCE_INSTANCE_URL
)

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    salesforce_status = "configured" if (SALESFORCE_CLIENT_ID and SALESFORCE_USERNAME) else "no_credentials"

    if SALESFORCE_CLIENT_ID and SALESFORCE_USERNAME:
        try:
            # Test authentication and get a few records
            accounts = await salesforce_client.get_accounts(1)
            opportunities = await salesforce_client.get_opportunities(1)
            salesforce_status = f"connected (accounts: {len(accounts)}, opportunities: {len(opportunities)})"
        except Exception as e:
            salesforce_status = f"error: {str(e)[:50]}"

    return {
        "status": "healthy",
        "salesforce_connection": salesforce_status,
        "tenant": TENANT,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/")
async def root():
    return {
        "service": "Sophia AI Salesforce MCP",
        "version": "2.0.0",
        "status": "operational",
        "salesforce_configured": bool(SALESFORCE_CLIENT_ID and SALESFORCE_USERNAME),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/accounts")
async def get_accounts(limit: int = 50):
    """Get Salesforce accounts"""
    try:
        accounts = await salesforce_client.get_accounts(limit)
        return {
            "accounts": accounts,
            "count": len(accounts),
            "tenant": TENANT,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/opportunities")
async def get_opportunities(limit: int = 50):
    """Get Salesforce opportunities"""
    try:
        opportunities = await salesforce_client.get_opportunities(limit)
        return {
            "opportunities": opportunities,
            "count": len(opportunities),
            "tenant": TENANT,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipeline")
async def get_pipeline():
    """Get sales pipeline summary"""
    try:
        opportunities = await salesforce_client.get_opportunities(100)
        accounts = await salesforce_client.get_accounts(100)

        # Analyze pipeline
        pipeline_summary = {
            "total_opportunities": len(opportunities),
            "total_accounts": len(accounts),
            "stage_distribution": {},
            "total_value": 0,
            "avg_deal_size": 0
        }

        total_amount = 0
        count_with_amount = 0

        for opp in opportunities:
            stage = opp.get("StageName", "unknown")

            if stage not in pipeline_summary["stage_distribution"]:
                pipeline_summary["stage_distribution"][stage] = 0
            pipeline_summary["stage_distribution"][stage] += 1

            amount = opp.get("Amount")
            if amount:
                total_amount += amount
                count_with_amount += 1

        pipeline_summary["total_value"] = total_amount
        if count_with_amount > 0:
            pipeline_summary["avg_deal_size"] = total_amount / count_with_amount

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