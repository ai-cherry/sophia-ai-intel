#!/usr/bin/env python3
"""
MCP Capability Token System
===========================

JWT-based authentication system for MCP services with scope-limited permissions.
Supports tenant/swarm/pii_level/tools/collections scoping for fine-grained access control.

Features:
- JWT token generation and validation
- Scope-based authorization (tenant, swarm, pii_level, tools, collections)
- Token expiration and refresh
- Normalized error responses
- Proof-first architecture compliance
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Set

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


# Configure logging
logger = logging.getLogger(__name__)


class MCPTokenError(Exception):
    """Base exception for MCP token errors"""

    pass


class MCPTokenValidationError(MCPTokenError):
    """Token validation failed"""

    pass


class MCPTokenAuthorizationError(MCPTokenError):
    """Token authorization/scope check failed"""

    pass


class MCPTokenManager:
    """
    MCP Token Manager - handles JWT generation and validation
    with scope-based authorization for MCP services
    """

    def __init__(
        self,
        private_key: Optional[bytes] = None,
        public_key: Optional[bytes] = None,
        issuer: str = "sophia-ai-mcp",
        algorithm: str = "RS256",
    ):
        """
        Initialize MCP Token Manager

        Args:
            private_key: RSA private key for signing (PEM format)
            public_key: RSA public key for verification (PEM format)
            issuer: JWT issuer identifier
            algorithm: JWT signing algorithm
        """
        self.issuer = issuer
        self.algorithm = algorithm

        # Generate or load keys
        if private_key and public_key:
            self.private_key = serialization.load_pem_private_key(
                private_key, password=None
            )
            self.public_key = serialization.load_pem_public_key(public_key)
        else:
            # Generate new key pair for development/testing
            self._generate_key_pair()

        # Define valid scopes
        self.valid_tenants = {"pay-ready", "dev", "staging", "test"}
        self.valid_swarms = {"default", "research", "business", "context", "github"}
        self.valid_pii_levels = {"none", "low", "medium", "high"}
        self.valid_tools = {
            "search",
            "index",
            "embed",
            "chunk",
            "retrieve",
            "chat",
            "generate",
            "analyze",
            "upload",
            "download",
            "create",
            "read",
            "update",
            "delete",
            "list",
            "health",
            "metrics",
            "status",
            "admin",
        }
        self.valid_collections = {
            "documents",
            "embeddings",
            "metadata",
            "cache",
            "sessions",
            "logs",
            "metrics",
            "configs",
            "prospects",
            "signals",
            "research",
            "context",
        }

    def _generate_key_pair(self):
        """Generate new RSA key pair for development"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self.private_key = private_key
        self.public_key = private_key.public_key()

        logger.info("🔐 Generated new RSA key pair for MCP tokens")

    def create_token(
        self,
        subject: str,
        tenant: str,
        swarm: str = "default",
        pii_level: str = "none",
        tools: Optional[Set[str]] = None,
        collections: Optional[Set[str]] = None,
        expires_in_minutes: int = 60,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new MCP capability token

        Args:
            subject: Token subject (user/service identifier)
            tenant: Tenant scope (e.g., "pay-ready")
            swarm: Swarm scope (e.g., "research", "business")
            pii_level: PII access level ("none", "low", "medium", "high")
            tools: Allowed tools/operations
            collections: Allowed data collections
            expires_in_minutes: Token expiration time
            additional_claims: Additional JWT claims

        Returns:
            Encoded JWT token string

        Raises:
            MCPTokenError: If token creation fails
        """
        try:
            # Validate scopes
            if tenant not in self.valid_tenants:
                raise MCPTokenError(f"Invalid tenant: {tenant}")
            if swarm not in self.valid_swarms:
                raise MCPTokenError(f"Invalid swarm: {swarm}")
            if pii_level not in self.valid_pii_levels:
                raise MCPTokenError(f"Invalid PII level: {pii_level}")

            # Default tools and collections if not specified
            if tools is None:
                tools = {"read", "health", "status"}
            if collections is None:
                collections = {"metadata", "cache"}

            # Validate tool and collection permissions
            invalid_tools = tools - self.valid_tools
            if invalid_tools:
                raise MCPTokenError(f"Invalid tools: {invalid_tools}")

            invalid_collections = collections - self.valid_collections
            if invalid_collections:
                raise MCPTokenError(f"Invalid collections: {invalid_collections}")

            # Create JWT payload
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(minutes=expires_in_minutes)

            payload = {
                # Standard JWT claims
                "iss": self.issuer,
                "sub": subject,
                "iat": int(now.timestamp()),
                "exp": int(expires_at.timestamp()),
                "jti": f"mcp_{int(now.timestamp())}_{hash(subject) % 10000:04d}",
                # MCP capability scopes
                "tenant": tenant,
                "swarm": swarm,
                "pii_level": pii_level,
                "tools": sorted(list(tools)),
                "collections": sorted(list(collections)),
                # Token metadata
                "token_type": "mcp_capability",
                "version": "1.0",
                "created_at": now.isoformat(),
            }

            # Add additional claims
            if additional_claims:
                payload.update(additional_claims)

            # Sign and encode token
            token = jwt.encode(
                payload,
                self.private_key,
                algorithm=self.algorithm,
                headers={"typ": "JWT", "alg": self.algorithm},
            )

            logger.info(
                f"🎫 Created MCP token for {subject} (tenant={tenant}, swarm={swarm})"
            )
            return token

        except Exception as e:
            logger.error(f"❌ Token creation failed: {e}")
            raise MCPTokenError(f"Token creation failed: {e}")

    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate and decode MCP token

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            MCPTokenValidationError: If token validation fails
        """
        try:
            # Decode and verify token
            payload = jwt.decode(
                token, self.public_key, algorithms=[self.algorithm], issuer=self.issuer
            )

            # Verify token type
            if payload.get("token_type") != "mcp_capability":
                raise MCPTokenValidationError("Invalid token type")

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
                raise MCPTokenValidationError(
                    f"Missing required claims: {missing_claims}"
                )

            logger.debug(f"✅ Token validated for {payload.get('sub')}")
            return payload

        except jwt.ExpiredSignatureError:
            raise MCPTokenValidationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise MCPTokenValidationError(f"Invalid token: {e}")
        except Exception as e:
            logger.error(f"❌ Token validation failed: {e}")
            raise MCPTokenValidationError(f"Token validation failed: {e}")

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
            True if authorized, False otherwise

        Raises:
            MCPTokenAuthorizationError: If authorization fails
        """
        try:
            # Check tenant
            if required_tenant and payload.get("tenant") != required_tenant:
                raise MCPTokenAuthorizationError(
                    f"Insufficient tenant access: required {required_tenant}, got {payload.get('tenant')}"
                )

            # Check swarm
            if required_swarm and payload.get("swarm") != required_swarm:
                raise MCPTokenAuthorizationError(
                    f"Insufficient swarm access: required {required_swarm}, got {payload.get('swarm')}"
                )

            # Check PII level (hierarchical: none < low < medium < high)
            if required_pii_level:
                pii_levels = ["none", "low", "medium", "high"]
                token_pii_index = pii_levels.index(payload.get("pii_level", "none"))
                required_pii_index = pii_levels.index(required_pii_level)

                if token_pii_index < required_pii_index:
                    raise MCPTokenAuthorizationError(
                        f"Insufficient PII access: required {required_pii_level}, got {payload.get('pii_level')}"
                    )

            # Check tool permissions
            if required_tools:
                token_tools = set(payload.get("tools", []))
                missing_tools = required_tools - token_tools
                if missing_tools:
                    raise MCPTokenAuthorizationError(
                        f"Insufficient tool permissions: missing {missing_tools}"
                    )

            # Check collection permissions
            if required_collections:
                token_collections = set(payload.get("collections", []))
                missing_collections = required_collections - token_collections
                if missing_collections:
                    raise MCPTokenAuthorizationError(
                        f"Insufficient collection permissions: missing {missing_collections}"
                    )

            logger.debug(f"✅ Authorization check passed for {payload.get('sub')}")
            return True

        except MCPTokenAuthorizationError:
            raise
        except Exception as e:
            logger.error(f"❌ Authorization check failed: {e}")
            raise MCPTokenAuthorizationError(f"Authorization check failed: {e}")

    def create_service_token(self, service_name: str, tenant: str = "pay-ready") -> str:
        """
        Create a service-to-service token with appropriate permissions

        Args:
            service_name: Name of the service (research, business, context, github)
            tenant: Tenant scope

        Returns:
            Service JWT token
        """
        # Define service-specific permissions
        service_permissions = {
            "research": {
                "swarm": "research",
                "pii_level": "low",
                "tools": {"search", "retrieve", "analyze", "read", "health"},
                "collections": {"research", "cache", "metadata"},
            },
            "business": {
                "swarm": "business",
                "pii_level": "medium",
                "tools": {"search", "create", "read", "update", "analyze", "health"},
                "collections": {"prospects", "signals", "cache", "metadata"},
            },
            "context": {
                "swarm": "context",
                "pii_level": "low",
                "tools": {"index", "embed", "chunk", "search", "retrieve", "health"},
                "collections": {"documents", "embeddings", "metadata", "cache"},
            },
            "github": {
                "swarm": "github",
                "pii_level": "none",
                "tools": {"read", "list", "search", "health"},
                "collections": {"metadata", "cache"},
            },
        }

        if service_name not in service_permissions:
            raise MCPTokenError(f"Unknown service: {service_name}")

        perms = service_permissions[service_name]

        return self.create_token(
            subject=f"service:{service_name}",
            tenant=tenant,
            swarm=perms["swarm"],
            pii_level=perms["pii_level"],
            tools=perms["tools"],
            collections=perms["collections"],
            expires_in_minutes=720,  # 12 hours for service tokens
            additional_claims={
                "service": service_name,
                "token_purpose": "service_to_service",
            },
        )

    def export_public_key_pem(self) -> bytes:
        """Export public key in PEM format for verification"""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def generate_demo_tokens(self) -> Dict[str, str]:
        """Generate demo tokens for testing and validation"""
        return {
            "admin_token": self.create_token(
                subject="admin@pay-ready.com",
                tenant="pay-ready",
                swarm="default",
                pii_level="high",
                tools=self.valid_tools,
                collections=self.valid_collections,
                expires_in_minutes=120,
            ),
            "research_service_token": self.create_service_token("research"),
            "business_service_token": self.create_service_token("business"),
            "context_service_token": self.create_service_token("context"),
            "github_service_token": self.create_service_token("github"),
            "readonly_token": self.create_token(
                subject="readonly@pay-ready.com",
                tenant="pay-ready",
                swarm="default",
                pii_level="none",
                tools={"read", "health", "status"},
                collections={"metadata", "cache"},
                expires_in_minutes=60,
            ),
        }


def create_flask_middleware(token_manager: MCPTokenManager):
    """
    Create Flask middleware for MCP token validation

    Args:
        token_manager: MCP token manager instance

    Returns:
        Flask middleware function
    """
    from functools import wraps

    def require_mcp_token(
        required_tools: Optional[Set[str]] = None,
        required_collections: Optional[Set[str]] = None,
        required_pii_level: Optional[str] = None,
    ):
        """Decorator for requiring MCP token authentication"""

        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                from flask import request, jsonify

                try:
                    # Get token from Authorization header
                    auth_header = request.headers.get("Authorization", "")
                    if not auth_header.startswith("Bearer "):
                        return jsonify(
                            {
                                "error": "missing_token",
                                "message": "Missing or invalid Authorization header",
                                "expected_format": "Bearer <mcp_token>",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        ), 401

                    token = auth_header[7:]  # Remove 'Bearer ' prefix

                    # Validate token
                    payload = token_manager.validate_token(token)

                    # Check authorization
                    token_manager.check_authorization(
                        payload,
                        required_tools=required_tools,
                        required_collections=required_collections,
                        required_pii_level=required_pii_level,
                    )

                    # Add token payload to request context
                    request.mcp_token = payload

                    return f(*args, **kwargs)

                except (MCPTokenValidationError, MCPTokenAuthorizationError) as e:
                    return jsonify(
                        {
                            "error": "token_error",
                            "message": str(e),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    ), 403

                except Exception as e:
                    logger.error(f"❌ Token middleware error: {e}")
                    return jsonify(
                        {
                            "error": "internal_error",
                            "message": "Token validation failed",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    ), 500

            return decorated_function

        return decorator

    return require_mcp_token


# Global token manager instance
_token_manager = None


def get_token_manager() -> MCPTokenManager:
    """Get global token manager instance"""
    global _token_manager
    if _token_manager is None:
        _token_manager = MCPTokenManager()
    return _token_manager


if __name__ == "__main__":
    # Demo/testing
    print("🎫 MCP Capability Token System Demo")

    # Create token manager
    manager = MCPTokenManager()

    # Generate demo tokens
    demo_tokens = manager.generate_demo_tokens()

    print(f"\n📋 Generated {len(demo_tokens)} demo tokens:")
    for name, token in demo_tokens.items():
        print(f"  • {name}: {token[:50]}...")

        # Validate each token
        try:
            payload = manager.validate_token(token)
            print(
                f"    ✅ Valid - Subject: {payload['sub']}, Tenant: {payload['tenant']}"
            )
        except Exception as e:
            print(f"    ❌ Invalid: {e}")

    print("\n🔐 Public key (for verification):")
    print(manager.export_public_key_pem().decode("utf-8"))
