#!/usr/bin/env python3
"""
Lambda Labs MCP Service - GPU Compute Integration
=================================================

High-performance GPU compute orchestration service for Sophia AI platform.
Provides Lambda Labs integration for AI training, inference, and batch processing.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiohttp
import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Environment configuration
LAMBDA_API_KEY = os.getenv("LAMBDA_API_KEY", "secret_sophiacloudapi_17cf7f3cedca48f18b4b8ea46cbb258f.EsLXt0lkGlhZ1Nd369Ld5DMSuhJg9O9y")
LAMBDA_PRIVATE_SSH_KEY = os.getenv("LAMBDA_PRIVATE_SSH_KEY", """-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACD7o6LbAggKrpqP5/WWcFWVHI8vC7t9YPq2UXeVZcfs0AAAAKhOiNSdTojU
nQAAAAtzc2gtZWQyNTUxOQAAACD7o6LbAggKrpqP5/WWcFWVHI8vC7t9YPq2UXeVZcfs0A
AAAEAGUPlkGE0k0DKawkILgrUEnx6e9VZmEbpx5LolLW6NjvujotsCCAqumo/n9ZZwVZUc
jy8Lu31g+rZRd5Vlx+zQAAAAIlNPUEhJQSBQcm9kdWN0aW9uIEtleSAtIDIwMjUtMDgtMT
UBAgM=
-----END OPENSSH PRIVATE KEY-----""")
LAMBDA_PUBLIC_SSH_KEY = os.getenv("LAMBDA_PUBLIC_SSH_KEY", "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPujotsCCAqumo/n9ZZwVZUcjy8Lu31g+rZRd5Vlx+zQ SOPHIA Production Key - 2025-08-15")
LAMBDA_API_ENDPOINT = "https://cloud.lambdalabs.com/api/v1"
DATABASE_URL = os.getenv("DATABASE_URL", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
TENANT = os.getenv("TENANT", "pay-ready")

# FastAPI application
app = FastAPI(
    title="Sophia AI Lambda MCP Service",
    description="GPU compute orchestration via Lambda Labs",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global connections
redis_client: Optional[redis.Redis] = None
db_pool: Optional[asyncpg.Pool] = None

class GPUInstanceRequest(BaseModel):
    instance_type: str = Field(..., description="GPU instance type")
    count: int = Field(1, ge=1, le=8)
    duration_hours: int = Field(1, ge=1, le=24)

class HealthResponse(BaseModel):
    status: str
    lambda_connection: str
    active_instances: int
    uptime_seconds: float

class LambdaClient:
    """Lambda Labs API client"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = LAMBDA_API_ENDPOINT
        self.connected = bool(api_key)
    
    async def list_instances(self) -> List[Dict[str, Any]]:
        """List all active Lambda Labs instances"""
        if not self.connected:
            return []
        
        async with aiohttp.ClientSession() as session:
            try:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with session.get(f"{self.base_url}/instances", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])
                    else:
                        logger.error(f"Lambda API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"Lambda API request failed: {e}")
                return []
    
    async def launch_instance(self, instance_type: str, count: int = 1) -> Dict[str, Any]:
        """Launch new Lambda Labs GPU instance"""
        if not self.connected:
            return {
                "id": f"mock-{instance_type.lower()}",
                "status": "pending",
                "message": "Mock instance - configure LAMBDA_API_KEY for real provisioning"
            }
        
        payload = {
            "region_name": "us-west-1",
            "instance_type_name": instance_type,
            "quantity": count
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with session.post(f"{self.base_url}/instance-operations/launch", 
                                      json=payload, headers=headers) as response:
                    if response.status in [200, 202]:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise HTTPException(status_code=response.status, detail=error_text)
            except Exception as e:
                logger.error(f"Lambda launch failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

lambda_client = LambdaClient(LAMBDA_API_KEY)

@app.on_event("startup")
async def startup_event():
    """Initialize connections"""
    global redis_client, db_pool
    logger.info("🚀 Starting Lambda MCP service...")

@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    
    # Test Lambda connection
    lambda_status = "connected" if LAMBDA_API_KEY else "no_api_key"
    if LAMBDA_API_KEY:
        try:
            instances = await lambda_client.list_instances()
            lambda_status = f"connected ({len(instances)} instances)"
        except Exception as e:
            lambda_status = f"error: {str(e)[:50]}"
    
    return HealthResponse(
        status="healthy",
        lambda_connection=lambda_status,
        active_instances=0,
        uptime_seconds=0.0
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Sophia AI Lambda MCP",
        "version": "2.0.0",
        "status": "operational",
        "lambda_configured": bool(LAMBDA_API_KEY),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/instances")
async def list_instances():
    """List all active Lambda Labs instances"""
    try:
        instances = await lambda_client.list_instances()
        return {
            "instances": instances,
            "count": len(instances),
            "tenant": TENANT,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to list instances: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/provision_gpu")
async def provision_gpu(request: GPUInstanceRequest):
    """Provision new GPU instance on Lambda Labs"""
    logger.info(f"🚀 GPU provisioning request: {request.instance_type} x{request.count}")
    
    try:
        result = await lambda_client.launch_instance(
            instance_type=request.instance_type,
            count=request.count
        )
        
        return {
            "success": True,
            "result": result,
            "tenant": TENANT,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"GPU provisioning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ssh_tunnel/{instance_id}")
async def get_ssh_tunnel(instance_id: str):
    """Get SSH connection details for instance"""
    
    try:
        instances = await lambda_client.list_instances()
        
        for instance in instances:
            if instance.get("id") == instance_id:
                ip = instance.get("ip")
                if ip:
                    return {
                        "instance_id": instance_id,
                        "ip_address": ip,
                        "ssh_command": f"ssh ubuntu@{ip}",
                        "ssh_user": "ubuntu",
                        "status": "available"
                    }
        
        raise HTTPException(status_code=404, detail="Instance not found")
    
    except Exception as e:
        logger.error(f"SSH tunnel request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
