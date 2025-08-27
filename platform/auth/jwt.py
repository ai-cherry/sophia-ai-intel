# platform/auth/jwt.py
"""
JWT Authentication Module for Sophia AI Platform
Provides JWT token creation, validation, and middleware for FastAPI applications.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Set

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..common.errors import SophiaError, err

# Configure logging
logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


class JWTError(SophiaError):
    """JWT-specific errors"""
    pass


class JWTManager:
    """
    JWT Manager for Sophia AI Platform
    Handles JWT token creation and validation with RSA signing
    """

    def __init__(
        self,
        private_key: Optional[bytes] = None,
        public_key: Optional[bytes] = None,
        issuer: str = "sophia-ai-platform",
        algorithm: str = "RS256",
        expiration_minutes: int = 60
    ):
        """
        Initialize JWT Manager

        Args:
            private_key: RSA private key for signing (PEM format)
            public_key: RSA public key for verification (PEM format)
            issuer: JWT issuer identifier
            algorithm: JWT signing algorithm
            expiration_minutes: Default token expiration time
        """
        self.issuer = issuer
        self.algorithm = algorithm
        self.expiration_minutes = expiration_minutes

        # Generate or load keys
        if private_key and public_key:
            self.private_key = serialization.load_pem_private_key(private_key, password=None)
            self.public_key = serialization.load_pem_public_key(public_key)
        else:
            # Generate new key pair for development/testing
            self._generate_key_pair()

    def _generate_key_pair(self):
        """Generate new RSA key pair for development"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self.private_key = private_key
        self.public_key = private_key.public_key()
        logger.info("🔐 Generated new RSA key pair for JWT")

    def create_token(
        self,
        subject: str,
        scopes: Optional[Set[str]] = None,
        expires_in_minutes: Optional[int] = None,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new JWT token

        Args:
            subject: Token subject (user/service identifier)
            scopes: Token scopes/permissions
            expires_in_minutes: Token expiration time (overrides default)
            additional_claims: Additional JWT claims

        Returns:
            Encoded JWT token string

        Raises:
            JWTError: If token creation fails
        """
        try:
            expiration = expires_in_minutes or self.expiration_minutes
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(minutes=expiration)

            payload = {
                # Standard JWT claims
                "iss": self.issuer,
                "sub": subject,
                "iat": int(now.timestamp()),
                "exp": int(expires_at.timestamp()),
                "jti": f"jwt_{int(now.timestamp())}_{hash(subject) % 10000:04d}",
                # Sophia-specific claims
                "scopes": sorted(list(scopes or set())),
                "token_type": "bearer",
                "version": "1.0",
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

            logger.info(f"🎫 Created JWT token for {subject}")
            return token

        except Exception as e:
            logger.error(f"❌ Token creation failed: {e}")
            raise JWTError(f"Token creation failed: {e}")

    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate and decode JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            JWTError: If token validation fails
        """
        try:
            # Decode and verify token
            payload = jwt.decode(
                token, self.public_key, algorithms=[self.algorithm], issuer=self.issuer
            )

            # Verify required claims
            required_claims = {"sub", "scopes", "token_type"}
            missing_claims = required_claims - set(payload.keys())
            if missing_claims:
                raise JWTError(f"Missing required claims: {missing_claims}")

            logger.debug(f"✅ Token validated for {payload.get('sub')}")
            return payload

        except jwt.ExpiredSignatureError:
            raise JWTError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise JWTError(f"Invalid token: {e}")
        except Exception as e:
            logger.error(f"❌ Token validation failed: {e}")
            raise JWTError(f"Token validation failed: {e}")

    def check_scopes(
        self,
        payload: Dict[str, Any],
        required_scopes: Set[str]
    ) -> bool:
        """
        Check if token has required scopes

        Args:
            payload: Decoded token payload
            required_scopes: Required scopes

        Returns:
            True if authorized, False otherwise

        Raises:
            JWTError: If authorization fails
        """
        token_scopes = set(payload.get("scopes", []))
        missing_scopes = required_scopes - token_scopes

        if missing_scopes:
            raise JWTError(f"Insufficient scopes: missing {missing_scopes}")

        logger.debug(f"✅ Scope check passed for {payload.get('sub')}")
        return True

    def export_public_key_pem(self) -> bytes:
        """Export public key in PEM format for verification"""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )


# Global JWT manager instance
_jwt_manager = None


def get_jwt_manager() -> JWTManager:
    """Get global JWT manager instance"""
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = JWTManager()
    return _jwt_manager


def create_jwt_token(
    subject: str,
    scopes: Optional[Set[str]] = None,
    expires_in_minutes: Optional[int] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Convenience function to create JWT token

    Args:
        subject: Token subject
        scopes: Token scopes
        expires_in_minutes: Expiration time
        additional_claims: Additional claims

    Returns:
        JWT token string
    """
    return get_jwt_manager().create_token(
        subject=subject,
        scopes=scopes,
        expires_in_minutes=expires_in_minutes,
        additional_claims=additional_claims,
    )


def validate_jwt_token(token: str) -> Dict[str, Any]:
    """
    Convenience function to validate JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded token payload
    """
    return get_jwt_manager().validate_token(token)


def require_jwt(
    required_scopes: Optional[Set[str]] = None
):
    """
    FastAPI dependency for JWT authentication

    Args:
        required_scopes: Required scopes for authorization

    Returns:
        FastAPI dependency function
    """
    async def jwt_dependency(
        credentials: HTTPAuthorizationCredentials = security
    ) -> Dict[str, Any]:
        try:
            # Validate token
            payload = get_jwt_manager().validate_token(credentials.credentials)

            # Check scopes if required
            if required_scopes:
                get_jwt_manager().check_scopes(payload, required_scopes)

            return payload

        except JWTError as e:
            raise HTTPException(
                status_code=401,
                detail=err(str(e), "JWT_ERROR", 401)
            )
        except Exception as e:
            logger.error(f"JWT dependency error: {e}")
            raise HTTPException(
                status_code=401,
                detail=err("Authentication failed", "AUTH_ERROR", 401)
            )

    return jwt_dependency


def get_current_user(
    request: Request
) -> Optional[str]:
    """
    Extract current user from JWT token in request

    Args:
        request: FastAPI request object

    Returns:
        Current user subject or None
    """
    try:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]  # Remove 'Bearer ' prefix
        payload = get_jwt_manager().validate_token(token)
        return payload.get("sub")

    except Exception:
        return None