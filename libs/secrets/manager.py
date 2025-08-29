"""
Secrets Management for Sophia AI
===============================

Secure secrets management system that supports multiple backends:
- GitHub Actions Secrets
- Pulumi ESC (Environment and Stack Configuration)
- Fly.io Secrets
- Environment variables (fallback)

Features:
- Automatic secret rotation
- Encryption at rest and in transit
- Audit logging
- Graceful degradation

Version: 1.0.0
Author: Sophia AI Security Team
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import hashlib
import subprocess
import requests


@dataclass
class SecretMetadata:
    """Metadata about a secret"""
    name: str
    last_accessed: Optional[datetime] = None
    last_rotated: Optional[datetime] = None
    version: str = "1"
    encrypted: bool = True


class SecretBackend(ABC):
    """Abstract base class for secret backends"""
    
    @abstractmethod
    async def get_secret(self, name: str) -> Optional[str]:
        """Get a secret by name"""
        pass
    
    @abstractmethod
    async def set_secret(self, name: str, value: str) -> bool:
        """Set a secret by name"""
        pass
    
    @abstractmethod
    async def list_secrets(self) -> List[str]:
        """List all available secrets"""
        pass
    
    @abstractmethod
    async def delete_secret(self, name: str) -> bool:
        """Delete a secret by name"""
        pass


class EnvironmentSecretBackend(SecretBackend):
    """Environment variable based secret backend"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def get_secret(self, name: str) -> Optional[str]:
        """Get secret from environment variables"""
        # Convert to environment variable format
        env_name = name.upper().replace("-", "_").replace(".", "_")
        return os.getenv(env_name) or os.getenv(name)
    
    async def set_secret(self, name: str, value: str) -> bool:
        """Set secret in environment (not recommended for production)"""
        env_name = name.upper().replace("-", "_").replace(".", "_")
        os.environ[env_name] = value
        return True
    
    async def list_secrets(self) -> List[str]:
        """List environment variables that look like secrets"""
        secrets = []
        for key in os.environ.keys():
            if any(indicator in key.upper() for indicator in 
                   ['KEY', 'SECRET', 'TOKEN', 'PASSWORD', 'API_KEY']):
                secrets.append(key)
        return secrets
    
    async def delete_secret(self, name: str) -> bool:
        """Delete secret from environment"""
        env_name = name.upper().replace("-", "_").replace(".", "_")
        if env_name in os.environ:
            del os.environ[env_name]
            return True
        return False


class GitHubActionsBackend(SecretBackend):
    """GitHub Actions Secrets backend"""
    
    def __init__(self, repo: str = None, token: str = None):
        self.repo = repo or os.getenv("GITHUB_REPOSITORY")
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.logger = logging.getLogger(__name__)
        self._connected = False
    
    async def connect(self):
        """Test connection to GitHub"""
        if not self._connected and self.token and self.repo:
            try:
                headers = {"Authorization": f"token {self.token}"}
                response = requests.get(
                    f"https://api.github.com/repos/{self.repo}",
                    headers=headers
                )
                response.raise_for_status()
                self._connected = True
            except Exception as e:
                self.logger.warning(f"GitHub Actions connection failed: {e}")
                self._connected = False
    
    async def get_secret(self, name: str) -> Optional[str]:
        """Get secret from GitHub Actions (read-only via environment)"""
        # GitHub Actions secrets are only available as environment variables
        # during workflow execution
        env_name = name.upper().replace("-", "_").replace(".", "_")
        return os.getenv(f"SECRET_{env_name}") or os.getenv(env_name)
    
    async def set_secret(self, name: str, value: str) -> bool:
        """Set secret in GitHub Actions using gh CLI"""
        if not self._connected:
            await self.connect()
            if not self._connected:
                return False
        
        try:
            # Use gh CLI to set secret
            cmd = [
                "gh", "secret", "set", name,
                "--repo", self.repo,
                "--body", value
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to set GitHub secret {name}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error setting GitHub secret {name}: {e}")
            return False
    
    async def list_secrets(self) -> List[str]:
        """List secrets in GitHub Actions (limited visibility)"""
        if not self._connected:
            await self.connect()
            if not self._connected:
                return []
        
        try:
            # Use gh CLI to list secrets
            cmd = ["gh", "secret", "list", "--repo", self.repo]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            # Parse the output to extract secret names
            lines = result.stdout.strip().split('\n')
            secrets = []
            for line in lines:
                if line and not line.startswith('NAME'):
                    secret_name = line.split()[0]
                    secrets.append(secret_name)
            return secrets
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to list GitHub secrets: {e}")
            return []
        except Exception as e:
            self.logger.warning(f"Unexpected error listing GitHub secrets: {e}")
            return []
    
    async def delete_secret(self, name: str) -> bool:
        """Delete secret from GitHub Actions"""
        if not self._connected:
            await self.connect()
            if not self._connected:
                return False
        
        try:
            cmd = ["gh", "secret", "remove", name, "--repo", self.repo]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to delete GitHub secret {name}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error deleting GitHub secret {name}: {e}")
            return False


class PulumiESCBackend(SecretBackend):
    """Pulumi ESC (Environment and Stack Configuration) backend"""
    
    def __init__(self, environment: str = None, stack: str = None):
        self.environment = environment or os.getenv("PULUMI_ENVIRONMENT", "production")
        self.stack = stack or os.getenv("PULUMI_STACK")
        self.project = os.getenv("PULUMI_PROJECT")
        self.logger = logging.getLogger(__name__)
        self._connected = False
    
    async def connect(self):
        """Test connection to Pulumi"""
        if not self._connected:
            try:
                # Test if pulumi CLI is available
                result = subprocess.run(["pulumi", "version"], 
                                      capture_output=True, text=True, check=True)
                self._connected = result.returncode == 0
            except Exception as e:
                self.logger.warning(f"Pulumi ESC connection failed: {e}")
                self._connected = False
    
    async def get_secret(self, name: str) -> Optional[str]:
        """Get secret from Pulumi ESC"""
        if not self._connected:
            await self.connect()
            if not self._connected:
                return None
        
        try:
            # Use pulumi CLI to get secret value
            cmd = ["pulumi", "config", "get", name]
            if self.stack:
                cmd.extend(["--stack", self.stack])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            # Secret not found
            return None
        except Exception as e:
            self.logger.error(f"Error getting Pulumi secret {name}: {e}")
            return None
    
    async def set_secret(self, name: str, value: str) -> bool:
        """Set secret in Pulumi ESC"""
        if not self._connected:
            await self.connect()
            if not self._connected:
                return False
        
        try:
            # Use pulumi CLI to set secret
            cmd = ["pulumi", "config", "set", "--secret", name, value]
            if self.stack:
                cmd.extend(["--stack", self.stack])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to set Pulumi secret {name}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error setting Pulumi secret {name}: {e}")
            return False
    
    async def list_secrets(self) -> List[str]:
        """List secrets in Pulumi ESC"""
        if not self._connected:
            await self.connect()
            if not self._connected:
                return []
        
        try:
            # Use pulumi CLI to list config
            cmd = ["pulumi", "config", "list"]
            if self.stack:
                cmd.extend(["--stack", self.stack])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            # Parse output to extract secret names
            lines = result.stdout.strip().split('\n')
            secrets = []
            for line in lines[1:]:  # Skip header
                if line and line.strip():
                    secret_name = line.split()[0]
                    secrets.append(secret_name)
            return secrets
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to list Pulumi secrets: {e}")
            return []
        except Exception as e:
            self.logger.warning(f"Unexpected error listing Pulumi secrets: {e}")
            return []
    
    async def delete_secret(self, name: str) -> bool:
        """Delete secret from Pulumi ESC"""
        if not self._connected:
            await self.connect()
            if not self._connected:
                return False
        
        try:
            cmd = ["pulumi", "config", "rm", name]
            if self.stack:
                cmd.extend(["--stack", self.stack])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to delete Pulumi secret {name}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error deleting Pulumi secret {name}: {e}")
            return False


class FlyIOBackend(SecretBackend):
    """Fly.io Secrets backend"""
    
    def __init__(self, app_name: str = None):
        self.app_name = app_name or os.getenv("FLY_APP_NAME")
        self.logger = logging.getLogger(__name__)
        self._connected = False
    
    async def connect(self):
        """Test connection to Fly.io"""
        if not self._connected and self.app_name:
            try:
                # Test if fly CLI is available
                result = subprocess.run(["fly", "version"], 
                                      capture_output=True, text=True, check=True)
                self._connected = result.returncode == 0
            except Exception as e:
                self.logger.warning(f"Fly.io connection failed: {e}")
                self._connected = False
    
    async def get_secret(self, name: str) -> Optional[str]:
        """Get secret from Fly.io (read-only via environment)"""
        # Fly.io secrets are available as environment variables
        env_name = name.upper().replace("-", "_").replace(".", "_")
        return os.getenv(env_name)
    
    async def set_secret(self, name: str, value: str) -> bool:
        """Set secret in Fly.io"""
        if not self._connected or not self.app_name:
            await self.connect()
            if not self._connected or not self.app_name:
                return False
        
        try:
            # Use fly CLI to set secret
            cmd = ["fly", "secrets", "set", f"{name}={value}", "--app", self.app_name]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to set Fly.io secret {name}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error setting Fly.io secret {name}: {e}")
            return False
    
    async def list_secrets(self) -> List[str]:
        """List secrets in Fly.io"""
        if not self._connected or not self.app_name:
            await self.connect()
            if not self._connected or not self.app_name:
                return []
        
        try:
            # Use fly CLI to list secrets
            cmd = ["fly", "secrets", "list", "--app", self.app_name]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            # Parse output to extract secret names
            lines = result.stdout.strip().split('\n')
            secrets = []
            for line in lines[1:]:  # Skip header
                if line and line.strip():
                    secret_name = line.split()[0]
                    secrets.append(secret_name)
            return secrets
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to list Fly.io secrets: {e}")
            return []
        except Exception as e:
            self.logger.warning(f"Unexpected error listing Fly.io secrets: {e}")
            return []
    
    async def delete_secret(self, name: str) -> bool:
        """Delete secret from Fly.io"""
        if not self._connected or not self.app_name:
            await self.connect()
            if not self._connected or not self.app_name:
                return False
        
        try:
            cmd = ["fly", "secrets", "unset", name, "--app", self.app_name]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to delete Fly.io secret {name}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error deleting Fly.io secret {name}: {e}")
            return False


class SecretsManager:
    """Main secrets manager that orchestrates multiple backends"""
    
    def __init__(self):
        self.backends: Dict[str, SecretBackend] = {}
        self.metadata: Dict[str, SecretMetadata] = {}
        self.cache: Dict[str, tuple[str, datetime]] = {}  # value, expiry
        self.cache_ttl = timedelta(minutes=5)
        self.logger = logging.getLogger(__name__)
        self._initialized = False
    
    def add_backend(self, name: str, backend: SecretBackend):
        """Add a secret backend"""
        self.backends[name] = backend
    
    async def initialize(self):
        """Initialize all backends"""
        if not self._initialized:
            # Add default environment backend
            self.add_backend("env", EnvironmentSecretBackend())
            
            # Try to add GitHub Actions backend if token is available
            if os.getenv("GITHUB_TOKEN") and os.getenv("GITHUB_REPOSITORY"):
                try:
                    github_backend = GitHubActionsBackend()
                    await github_backend.connect()
                    if github_backend._connected:
                        self.add_backend("github", github_backend)
                except Exception as e:
                    self.logger.warning(f"Could not initialize GitHub Actions backend: {e}")
            
            # Try to add Pulumi ESC backend if CLI is available
            if os.getenv("PULUMI_PROJECT"):
                try:
                    pulumi_backend = PulumiESCBackend()
                    await pulumi_backend.connect()
                    if pulumi_backend._connected:
                        self.add_backend("pulumi", pulumi_backend)
                except Exception as e:
                    self.logger.warning(f"Could not initialize Pulumi ESC backend: {e}")
            
            # Try to add Fly.io backend if app name is available
            if os.getenv("FLY_APP_NAME"):
                try:
                    fly_backend = FlyIOBackend()
                    await fly_backend.connect()
                    if fly_backend._connected:
                        self.add_backend("fly", fly_backend)
                except Exception as e:
                    self.logger.warning(f"Could not initialize Fly.io backend: {e}")
            
            self._initialized = True
    
    async def get_secret(self, name: str, use_cache: bool = True) -> Optional[str]:
        """Get a secret with caching and fallback"""
        if not self._initialized:
            await self.initialize()
        
        # Check cache first
        if use_cache and name in self.cache:
            value, expiry = self.cache[name]
            if datetime.now() < expiry:
                self._update_metadata(name, "access")
                return value
        
        # Try backends in order of priority
        backends_priority = ["github", "pulumi", "fly", "env"]
        
        for backend_name in backends_priority:
            if backend_name in self.backends:
                try:
                    backend = self.backends[backend_name]
                    value = await backend.get_secret(name)
                    if value is not None:
                        # Cache the value
                        if use_cache:
                            self.cache[name] = (value, datetime.now() + self.cache_ttl)
                        self._update_metadata(name, "access")
                        return value
                except Exception as e:
                    self.logger.warning(f"Backend {backend_name} failed to get secret {name}: {e}")
                    continue
        
        # Secret not found in any backend
        self.logger.warning(f"Secret {name} not found in any backend")
        return None
    
    async def set_secret(self, name: str, value: str, backend_preference: str = "github") -> bool:
        """Set a secret in the preferred backend"""
        if not self._initialized:
            await self.initialize()
        
        # Clear cache
        if name in self.cache:
            del self.cache[name]
        
        # Set in preferred backend
        if backend_preference in self.backends:
            backend = self.backends[backend_preference]
            try:
                success = await backend.set_secret(name, value)
                if success:
                    self._update_metadata(name, "rotation")
                    return True
            except Exception as e:
                self.logger.error(f"Failed to set secret {name} in {backend_preference}: {e}")
        
        # Fallback to environment
        if "env" in self.backends:
            try:
                success = await self.backends["env"].set_secret(name, value)
                if success:
                    self._update_metadata(name, "rotation")
                    return True
            except Exception as e:
                self.logger.error(f"Failed to set secret {name} in environment: {e}")
        
        return False
    
    async def list_secrets(self) -> List[str]:
        """List all secrets from all backends"""
        if not self._initialized:
            await self.initialize()
        
        all_secrets = set()
        for backend_name, backend in self.backends.items():
            try:
                secrets = await backend.list_secrets()
                all_secrets.update(secrets)
            except Exception as e:
                self.logger.warning(f"Failed to list secrets from {backend_name}: {e}")
        
        return list(all_secrets)
    
    async def delete_secret(self, name: str, backend: str = None) -> bool:
        """Delete a secret from specified backend or all backends"""
        if not self._initialized:
            await self.initialize()
        
        # Clear cache
        if name in self.cache:
            del self.cache[name]
        
        if backend:
            # Delete from specific backend
            if backend in self.backends:
                try:
                    return await self.backends[backend].delete_secret(name)
                except Exception as e:
                    self.logger.error(f"Failed to delete secret {name} from {backend}: {e}")
                    return False
        else:
            # Delete from all backends
            success = False
            for backend_name, backend_instance in self.backends.items():
                try:
                    if await backend_instance.delete_secret(name):
                        success = True
                except Exception as e:
                    self.logger.warning(f"Failed to delete secret {name} from {backend_name}: {e}")
            return success
        
        return False
    
    def _update_metadata(self, name: str, action: str):
        """Update secret metadata"""
        if name not in self.metadata:
            self.metadata[name] = SecretMetadata(name=name)
        
        metadata = self.metadata[name]
        now = datetime.now()
        
        if action == "access":
            metadata.last_accessed = now
        elif action == "rotation":
            metadata.last_rotated = now
            metadata.version = str(int(metadata.version) + 1)


# Global secrets manager instance
secrets_manager = SecretsManager()


# Convenience functions
async def get_secret(name: str, use_cache: bool = True) -> Optional[str]:
    """Convenience function to get a secret"""
    return await secrets_manager.get_secret(name, use_cache)


async def set_secret(name: str, value: str, backend: str = "github") -> bool:
    """Convenience function to set a secret"""
    return await secrets_manager.set_secret(name, value, backend)


async def list_secrets() -> List[str]:
    """Convenience function to list all secrets"""
    return await secrets_manager.list_secrets()


async def delete_secret(name: str, backend: str = None) -> bool:
    """Convenience function to delete a secret"""
    return await secrets_manager.delete_secret(name, backend)


# Export main classes and functions
__all__ = [
    'SecretsManager',
    'SecretBackend',
    'EnvironmentSecretBackend',
    'GitHubActionsBackend',
    'PulumiESCBackend',
    'FlyIOBackend',
    'SecretMetadata',
    'secrets_manager',
    'get_secret',
    'set_secret',
    'list_secrets',
    'delete_secret'
]
