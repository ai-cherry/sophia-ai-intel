#!/usr/bin/env python3
"""
MCP Token Validation for Business Service
========================================

FastAPI integration for MCP capability token validation.
Provides middleware and decorators for scope-based authorization.
"""

import json
import logging
import os
from datetime import datetime, timezone
from functools import wraps
from typing import Dict, Any, Optional, Set

import jwt
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)

# Default public key for token validation (in production, load from environment)
DEFAULT_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1234567890ABCDEF1234
567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234
567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234
567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234
567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234
567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234
567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF
-----END PUBLIC KEY-----"""


class MCPTokenError(HTTPException):
    """MCP Token validation error"""

    def __init__(self, detail: str, status_code: int = 403):
        super().__init__(status_code=status_code, detail=detail)


class MCPTokenValidator:
    """MCP Token validator for FastAPI"""

    def __init__(self, public_key_pem: Optional[str] = None):
        """
        Initialize validator with public key

        Args:
            public_key_pem: RSA public key in PEM format
        """
        self.issuer = "sophia-ai-mcp"
        self.algorithm = "RS256"

        # Load public key
        public_key_str = public_key_pem or os.getenv(
            "MCP_PUBLIC_KEY", DEFAULT_PUBLIC_KEY
        )
        try:
            self.public_key = serialization.load_pem_public_key(public_key_str.encode())
        except Exception as e:
            logger.warning(f"Failed to load MCP public key: {e}")
            self.public_key = None

    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate and decode MCP token

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            MCPTokenError: If token validation fails
        """
        if not self.public_key:
            # In development, allow bypass if no key configured
            logger.warning("⚠️ MCP token validation bypassed - no public key configured")
            return {
                "sub": "dev-bypass",
                "tenant": "pay-ready",
                "swarm": "business",
                "pii_level": "medium",
                "tools": ["search", "create", "read", "update", "analyze", "health"],
                "collections": ["prospects", "signals", "cache", "metadata"],
                "bypass": True,
            }

        try:
            # Decode and verify token
            payload = jwt.decode(
                token, self.public_key, algorithms=[self.algorithm], issuer=self.issuer
            )

            # Verify token type
            if payload.get("token_type") != "mcp_capability":
                raise MCPTokenError("Invalid token type")

            # Verify required claims
            required_claims = {
                "sub",
                "tenant",
                "swarm",
                "pii_level",
                "tools",
                "collections",
            }
            missing_claims = required_claims - set(payload.keys())
            if missing_claims:
                raise MCPTokenError(f"Missing required claims: {missing_claims}")

            logger.debug(f"✅ Token validated for {payload.get('sub')}")
            return payload

        except jwt.ExpiredSignatureError:
            raise MCPTokenError("Token has expired", status_code=401)
        except jwt.InvalidTokenError as e:
            raise MCPTokenError(f"Invalid token: {e}", status_code=401)
        except Exception as e:
            logger.error(f"❌ Token validation failed: {e}")
            raise MCPTokenError(f"Token validation failed: {e}")

    def check_authorization(
        self,
        payload: Dict[str, Any],
        required_tenant: Optional[str] = None,
        required_swarm: Optional[str] = None,
        required_pii_level: Optional[str] = None,
        required_tools: Optional[Set[str]] = None,
        required_collections: Optional[Set[str]] = None,
    ) -> bool:
        """
        Check if token has required authorization scopes

        Args:
            payload: Decoded token payload
            required_tenant: Required tenant access
            required_swarm: Required swarm access
            required_pii_level: Minimum PII level required
            required_tools: Required tool permissions
            required_collections: Required collection permissions

        Returns:
            True if authorized

        Raises:
            MCPTokenError: If authorization fails
        """
        # Skip authorization check if bypassed (development mode)
        if payload.get("bypass"):
            logger.debug("🚧 Authorization check bypassed - development mode")
            return True

        try:
            # Check tenant
            if required_tenant and payload.get("tenant") != required_tenant:
                raise MCPTokenError(
                    f"Insufficient tenant access: required {required_tenant}, got {payload.get('tenant')}"
                )

            # Check swarm
            if required_swarm and payload.get("swarm") != required_swarm:
                raise MCPTokenError(
                    f"Insufficient swarm access: required {required_swarm}, got {payload.get('swarm')}"
                )

            # Check PII level (hierarchical: none < low < medium < high)
            if required_pii_level:
                pii_levels = ["none", "low", "medium", "high"]
                token_pii_index = pii_levels.index(payload.get("pii_level", "none"))
                required_pii_index = pii_levels.index(required_pii_level)

                if token_pii_index < required_pii_index:
                    raise MCPTokenError(
                        f"Insufficient PII access: required {required_pii_level}, got {payload.get('pii_level')}"
                    )

            # Check tool permissions
            if required_tools:
                token_tools = set(payload.get("tools", []))
                missing_tools = required_tools - token_tools
                if missing_tools:
                    raise MCPTokenError(
                        f"Insufficient tool permissions: missing {missing_tools}"
                    )

            # Check collection permissions
            if required_collections:
                token_collections = set(payload.get("collections", []))
                missing_collections = required_collections - token_collections
                if missing_collections:
                    raise MCPTokenError(
                        f"Insufficient collection permissions: missing {missing_collections}"
                    )

            logger.debug(f"✅ Authorization check passed for {payload.get('sub')}")
            return True

        except MCPTokenError:
            raise
        except Exception as e:
            logger.error(f"❌ Authorization check failed: {e}")
            raise MCPTokenError(f"Authorization check failed: {e}")


# Global validator instance
_validator = MCPTokenValidator()

# FastAPI Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    FastAPI dependency to get and validate current MCP token

    Returns:
        Decoded token payload

    Raises:
        MCPTokenError: If token validation fails
    """
    if not credentials:
        raise MCPTokenError("Missing Authorization header", status_code=401)

    token = credentials.credentials
    payload = _validator.validate_token(token)
    return payload


def require_mcp_auth(
    required_tenant: Optional[str] = "pay-ready",
    required_swarm: Optional[str] = "business",
    required_pii_level: Optional[str] = None,
    required_tools: Optional[Set[str]] = None,
    required_collections: Optional[Set[str]] = None,
):
    """
    FastAPI dependency factory for MCP token authorization

    Args:
        required_tenant: Required tenant access
        required_swarm: Required swarm access
        required_pii_level: Minimum PII level required
        required_tools: Required tool permissions
        required_collections: Required collection permissions

    Returns:
        FastAPI dependency function
    """

    async def verify_authorization(
        token_payload: Dict[str, Any] = Depends(get_current_token),
    ):
        """Verify token authorization"""
        _validator.check_authorization(
            token_payload,
            required_tenant=required_tenant,
            required_swarm=required_swarm,
            required_pii_level=required_pii_level,
            required_tools=required_tools,
            required_collections=required_collections,
        )
        return token_payload

    return verify_authorization


def require_business_auth():
    """FastAPI dependency for business service authentication"""
    return require_mcp_auth(
        required_tenant="pay-ready",
        required_swarm="business",
        required_pii_level="medium",
        required_tools={"read", "search"},
        required_collections={"prospects", "signals"},
    )


def require_admin_auth():
    """FastAPI dependency for admin operations"""
    return require_mcp_auth(
        required_tenant="pay-ready",
        required_pii_level="high",
        required_tools={"admin", "create", "update", "delete"},
        required_collections={"prospects", "signals", "metadata"},
    )


def create_demo_error_response(operation: str) -> Dict[str, Any]:
    """Create demonstration error response for invalid tokens"""
    return {
        "error": "mcp_token_required",
        "message": f"Operation '{operation}' requires valid MCP capability token",
        "operation": operation,
        "required_scopes": {
            "tenant": "pay-ready",
            "swarm": "business",
            "pii_level": "medium",
            "tools": ["read", "search"],
            "collections": ["prospects", "signals"],
        },
        "examples": {
            "curl": f"curl -H 'Authorization: Bearer <mcp_token>' https://sophiaai-mcp-business-v2.fly.dev/{operation}",
            "javascript": f"fetch('//{operation}', {{ headers: {{ 'Authorization': 'Bearer ' + mcpToken }} }})",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "proof_artifact": True,
    }
