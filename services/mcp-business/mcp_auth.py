#!/usr/bin/env python3
"""
MCP Authentication Module

Provides token validation and authorization functions for MCP services.
"""

import time
from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

# Simple token validation for now
security = HTTPBearer(auto_error=False)

def create_demo_error_response(error_type: str = "auth_required") -> Dict[str, Any]:
    """Create a demo error response for authentication failures"""
    return {
        "status": "error",
        "code": error_type,
        "message": "MCP token validation required",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "demo_mode": True
    }

def validate_mcp_token(token: str) -> Dict[str, Any]:
    """
    Validate MCP token and return payload.
    For now, this is a simple validation - in production would verify JWT signature.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Missing MCP token")
    
    # Simple token validation - in production would verify JWT
    if token.startswith("mcp_"):
        return {
            "valid": True,
            "user_id": "demo_user",
            "role": "business",
            "tenant": "pay-ready",
            "expires": time.time() + 3600
        }
    
    raise HTTPException(status_code=401, detail="Invalid MCP token")

def require_business_auth():
    """Dependency for business-level authentication"""
    def auth_dependency(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Dict[str, Any]:
        # For now, allow requests without tokens in development
        if not credentials:
            logger.warning("No MCP token provided - allowing for development")
            return {
                "user_id": "dev_user",
                "role": "business", 
                "tenant": "pay-ready",
                "demo_mode": True
            }
        
        return validate_mcp_token(credentials.credentials)
    
    return auth_dependency

def require_admin_auth():
    """Dependency for admin-level authentication"""
    def auth_dependency(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Dict[str, Any]:
        # For now, allow requests without tokens in development
        if not credentials:
            logger.warning("No MCP admin token provided - allowing for development")
            return {
                "user_id": "dev_admin",
                "role": "admin",
                "tenant": "pay-ready", 
                "demo_mode": True
            }
        
        payload = validate_mcp_token(credentials.credentials)
        if payload.get("role") not in ["admin", "business"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        return payload
    
    return auth_dependency
