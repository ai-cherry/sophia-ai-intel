"""
Sophia AI Configuration System
==============================

Centralized configuration management that integrates with the secrets manager
and provides typed configuration objects for all services.

Version: 1.0.0
Author: Sophia AI Infrastructure Team
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import logging

from libs.secrets.manager import secrets_manager, get_secret


@dataclass
class LLMConfig:
    """LLM provider configuration"""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""
    perplexity_api_key: str = ""
    xai_api_key: str = ""
    default_model: str = "gpt-4-turbo"
    default_temperature: float = 0.7
    default_max_tokens: int = 2048


@dataclass
class SearchConfig:
    """Search provider configuration"""
    tavily_api_key: str = ""
    serper_api_key: str = ""
    brave_api_key: str = ""
    exa_api_key: str = ""
    default_provider: str = "tavily"


@dataclass
class BusinessIntegrationsConfig:
    """Business integration configuration"""
    # HubSpot
    hubspot_access_token: str = ""
    hubspot_api_key: str = ""
    
    # Salesforce
    salesforce_client_id: str = ""
    salesforce_client_secret: str = ""
    salesforce_username: str = ""
    salesforce_password: str = ""
    salesforce_security_token: str = ""
    
    # Gong
    gong_api_key: str = ""
    gong_email: str = ""
    
    # GitHub
    github_app_id: str = ""
    github_app_private_key: str = ""
    github_webhook_secret: str = ""


@dataclass
class DatabaseConfig:
    """Database and vector store configuration"""
    # Neon PostgreSQL
    neon_database_url: str = ""
    
    # Qdrant Vector Database
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    
    # Redis (for caching)
    redis_url: str = "redis://localhost:6379"


@dataclass
class ContextConfig:
    """Context service configuration"""
    embed_endpoint: str = "https://api.openai.com/v1/embeddings"
    embed_model: str = "text-embedding-3-large"
    chunk_size: int = 1000
    chunk_overlap: int = 200


@dataclass
class SwarmConfig:
    """Agent swarm configuration"""
    websocket_url: str = "ws://localhost:8100"
    max_concurrent_swarms: int = 10
    timeout_seconds: int = 300


@dataclass
class SecurityConfig:
    """Security and monitoring configuration"""
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"
    jwt_secret: str = ""
    encryption_key: str = ""


@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    port: int = 3000
    node_env: str = "development"
    debug: bool = False


@dataclass
class SophiaConfig:
    """Main configuration class for Sophia AI"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    business: BusinessIntegrationsConfig = field(default_factory=BusinessIntegrationsConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    context: ContextConfig = field(default_factory=ContextConfig)
    swarm: SwarmConfig = field(default_factory=SwarmConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    deployment: DeploymentConfig = field(default_factory=DeploymentConfig)
    
    @classmethod
    async def load(cls) -> 'SophiaConfig':
        """Load configuration from secrets manager and environment"""
        config = cls()
        
        # Initialize secrets manager
        await secrets_manager.initialize()
        
        # Load LLM configuration
        config.llm = await cls._load_llm_config()
        
        # Load search configuration
        config.search = await cls._load_search_config()
        
        # Load business integrations configuration
        config.business = await cls._load_business_config()
        
        # Load database configuration
        config.database = await cls._load_database_config()
        
        # Load context configuration
        config.context = await cls._load_context_config()
        
        # Load swarm configuration
        config.swarm = await cls._load_swarm_config()
        
        # Load security configuration
        config.security = await cls._load_security_config()
        
        # Load deployment configuration
        config.deployment = await cls._load_deployment_config()
        
        return config
    
    @classmethod
    async def _load_llm_config(cls) -> LLMConfig:
        """Load LLM configuration from secrets"""
        return LLMConfig(
            openai_api_key=await get_secret("OPENAI_API_KEY") or "",
            anthropic_api_key=await get_secret("ANTHROPIC_API_KEY") or "",
            openrouter_api_key=await get_secret("OPENROUTER_API_KEY") or "",
            perplexity_api_key=await get_secret("PERPLEXITY_API_KEY") or "",
            xai_api_key=await get_secret("XAI_API_KEY") or "",
            default_model=os.getenv("LLM_DEFAULT_MODEL", "gpt-4-turbo"),
            default_temperature=float(os.getenv("LLM_DEFAULT_TEMPERATURE", "0.7")),
            default_max_tokens=int(os.getenv("LLM_DEFAULT_MAX_TOKENS", "2048"))
        )
    
    @classmethod
    async def _load_search_config(cls) -> SearchConfig:
        """Load search configuration from secrets"""
        return SearchConfig(
            tavily_api_key=await get_secret("TAVILY_API_KEY") or "",
            serper_api_key=await get_secret("SERPER_API_KEY") or "",
            brave_api_key=await get_secret("BRAVE_API_KEY") or "",
            exa_api_key=await get_secret("EXA_API_KEY") or "",
            default_provider=os.getenv("SEARCH_DEFAULT_PROVIDER", "tavily")
        )
    
    @classmethod
    async def _load_business_config(cls) -> BusinessIntegrationsConfig:
        """Load business integrations configuration from secrets"""
        return BusinessIntegrationsConfig(
            hubspot_access_token=await get_secret("HUBSPOT_ACCESS_TOKEN") or "",
            hubspot_api_key=await get_secret("HUBSPOT_API_KEY") or "",
            salesforce_client_id=await get_secret("SALESFORCE_CLIENT_ID") or "",
            salesforce_client_secret=await get_secret("SALESFORCE_CLIENT_SECRET") or "",
            salesforce_username=await get_secret("SALESFORCE_USERNAME") or "",
            salesforce_password=await get_secret("SALESFORCE_PASSWORD") or "",
            salesforce_security_token=await get_secret("SALESFORCE_SECURITY_TOKEN") or "",
            gong_api_key=await get_secret("GONG_API_KEY") or "",
            gong_email=await get_secret("GONG_EMAIL") or "",
            github_app_id=await get_secret("GITHUB_APP_ID") or "",
            github_app_private_key=await get_secret("GITHUB_APP_PRIVATE_KEY") or "",
            github_webhook_secret=await get_secret("GITHUB_WEBHOOK_SECRET") or ""
        )
    
    @classmethod
    async def _load_database_config(cls) -> DatabaseConfig:
        """Load database configuration from secrets"""
        return DatabaseConfig(
            neon_database_url=await get_secret("NEON_DATABASE_URL") or "",
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            qdrant_api_key=await get_secret("QDRANT_API_KEY") or "",
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379")
        )
    
    @classmethod
    async def _load_context_config(cls) -> ContextConfig:
        """Load context service configuration"""
        return ContextConfig(
            embed_endpoint=os.getenv("EMBED_ENDPOINT", "https://api.openai.com/v1/embeddings"),
            embed_model=os.getenv("EMBED_MODEL", "text-embedding-3-large"),
            chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200"))
        )
    
    @classmethod
    async def _load_swarm_config(cls) -> SwarmConfig:
        """Load swarm configuration"""
        return SwarmConfig(
            websocket_url=os.getenv("SWARM_WEBSOCKET_URL", "ws://localhost:8100"),
            max_concurrent_swarms=int(os.getenv("MAX_CONCURRENT_SWARMS", "10")),
            timeout_seconds=int(os.getenv("SWARM_TIMEOUT_SECONDS", "300"))
        )
    
    @classmethod
    async def _load_security_config(cls) -> SecurityConfig:
        """Load security configuration from secrets"""
        return SecurityConfig(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            cors_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000"),
            jwt_secret=await get_secret("JWT_SECRET") or "",
            encryption_key=await get_secret("ENCRYPTION_KEY") or ""
        )
    
    @classmethod
    async def _load_deployment_config(cls) -> DeploymentConfig:
        """Load deployment configuration"""
        return DeploymentConfig(
            port=int(os.getenv("PORT", "3000")),
            node_env=os.getenv("NODE_ENV", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true"
        )


# Global configuration instance
config: Optional[SophiaConfig] = None


async def load_config() -> SophiaConfig:
    """Load and return the global configuration"""
    global config
    if config is None:
        config = await SophiaConfig.load()
    return config


# Export main classes and functions
__all__ = [
    'SophiaConfig',
    'LLMConfig',
    'SearchConfig',
    'BusinessIntegrationsConfig',
    'DatabaseConfig',
    'ContextConfig',
    'SwarmConfig',
    'SecurityConfig',
    'DeploymentConfig',
    'load_config'
]
