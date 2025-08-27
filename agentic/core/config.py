# Sophia AI Agentic Core Configuration
# ====================================
# Model configuration and environment management for Agno agents

import os
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)


class ModelConfig(BaseModel):
    """Configuration for a specific model provider"""
    model_name: str
    api_key_env: str
    model_params: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class ProviderConfig(BaseModel):
    """Configuration for a model provider (OpenAI, Anthropic, etc.)"""
    primary_model: ModelConfig
    fallback_models: List[ModelConfig] = Field(default_factory=list)
    priority: int = 1


class SophiaAgentConfig(BaseSettings):
    """Main configuration for Sophia AI Agentic system"""

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")

    # Vector Database Configuration
    qdrant_url: str = Field(default="http://localhost:6333", env="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(default=None, env="QDRANT_API_KEY")
    qdrant_collection_research: str = "research_docs"
    qdrant_collection_embeddings: str = "embeddings"

    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_organization: Optional[str] = Field(default=None, env="OPENAI_ORGANIZATION")

    # Anthropic Configuration
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")

    # Google/Gemini Configuration
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    gemini_embed_key: Optional[str] = Field(default=None, env="GEMINI_EMBED_KEY")

    # Grok Configuration
    grok_api_key: Optional[str] = Field(default=None, env="GROK_API_KEY")
    grok_api_key_heavy: Optional[str] = Field(default=None, env="GROK_API_KEY_HEAVY")

    # Cohere Configuration
    cohere_api_key: Optional[str] = Field(default=None, env="COHERE_API_KEY")

    # Together AI Configuration
    together_api_key: Optional[str] = Field(default=None, env="TOGETHER_API_KEY")

    # Tavily for Research
    tavily_api_key: Optional[str] = Field(default=None, env="TAVILY_API_KEY")

    # Perplexity for Research
    perplexity_api_key: Optional[str] = Field(default=None, env="PERPLEXITY_API_KEY")

    # Serper.dev for Search
    serper_api_key: Optional[str] = Field(default=None, env="SERPER_API_KEY")

    # Apify for Web Scraping
    apify_api_token: Optional[str] = Field(default=None, env="APIFY_API_TOKEN")

    # ZenRows/Playwright for Scraping
    zenrows_api_key: Optional[str] = Field(default=None, env="ZENROWS_API_KEY")
    brightdata_api_key: Optional[str] = Field(default=None, env="BRIGHTDATA_API_KEY")

    # Postgres/Neon Configuration
    postgres_url: str = Field(default="postgresql://user:pass@localhost:5432/db", env="POSTGRES_URL")

    # Service Configuration
    agentic_port: int = Field(default=8080, env="AGENTIC_PORT")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    class Config:
        env_file = ".env"
        case_sensitive = False


class ModelCatalog:
    """Catalog of available models with performance rankings"""

    def __init__(self, config: SophiaAgentConfig):
        self.config = config
        self._model_rankings = self._build_model_rankings()
        self._validate_configuration()

    def _build_model_rankings(self) -> Dict[str, Dict[str, ProviderConfig]]:
        """Build the model ranking system based on task types"""

        # Code Planning & Strategy Models (Prioritized in order)
        code_planning_models = [
            ModelConfig(
                model_name="gpt-5",
                api_key_env="OPENAI_API_KEY",
                model_params={"temperature": 0.1, "max_tokens": 4096},
                enabled=bool(self.config.openai_api_key)
            ),
            ModelConfig(
                model_name="claude-3-5-sonnet-20241022",
                api_key_env="ANTHROPIC_API_KEY",
                model_params={"temperature": 0.1, "max_tokens": 4096},
                enabled=bool(self.config.anthropic_api_key)
            ),
            ModelConfig(
                model_name="grok-beta",
                api_key_env="GROK_API_KEY",
                model_params={"temperature": 0.1, "max_tokens": 4096},
                enabled=bool(self.config.grok_api_key)
            ),
            ModelConfig(
                model_name="gemini-2.0-flash-exp",
                api_key_env="GEMINI_API_KEY",
                model_params={"temperature": 0.1, "max_tokens": 4096},
                enabled=bool(self.config.gemini_api_key)
            )
        ]

        # Code Writing Models
        code_writing_models = [
            ModelConfig(
                model_name="gemini-2.0-flash-exp",
                api_key_env="GEMINI_API_KEY",
                model_params={"temperature": 0.3, "max_tokens": 8192},
                enabled=bool(self.config.gemini_api_key)
            ),
            ModelConfig(
                model_name="claude-3-5-sonnet-20241022",
                api_key_env="ANTHROPIC_API_KEY",
                model_params={"temperature": 0.3, "max_tokens": 8192},
                enabled=bool(self.config.anthropic_api_key)
            ),
            ModelConfig(
                model_name="gpt-5",
                api_key_env="OPENAI_API_KEY",
                model_params={"temperature": 0.3, "max_tokens": 8192},
                enabled=bool(self.config.openai_api_key)
            )
        ]

        # Embedding Models
        embedding_models = [
            ModelConfig(
                model_name="text-embedding-3-large",
                api_key_env="OPENAI_API_KEY",
                model_params={"dimensions": 3072},
                enabled=bool(self.config.openai_api_key)
            ),
            ModelConfig(
                model_name="gemini-embedding-exp-0827",
                api_key_env="GEMINI_EMBED_KEY",
                model_params={},
                enabled=bool(self.config.gemini_embed_key)
            ),
            ModelConfig(
                model_name="embed-english-v3.0",
                api_key_env="COHERE_API_KEY",
                model_params={},
                enabled=bool(self.config.cohere_api_key)
            )
        ]

        # Research Models
        research_models = [
            ModelConfig(
                model_name="gemini-2.0-flash-exp",
                api_key_env="GEMINI_API_KEY",
                model_params={"temperature": 0.2, "max_tokens": 16384},
                enabled=bool(self.config.gemini_api_key)
            ),
            ModelConfig(
                model_name="claude-3-5-sonnet-20241022",
                api_key_env="ANTHROPIC_API_KEY",
                model_params={"temperature": 0.2, "max_tokens": 16384},
                enabled=bool(self.config.anthropic_api_key)
            ),
            ModelConfig(
                model_name="gpt-4-turbo-preview",
                api_key_env="OPENAI_API_KEY",
                model_params={"temperature": 0.2, "max_tokens": 16384},
                enabled=bool(self.config.openai_api_key)
            )
        ]

        # Business Intelligence Models
        business_models = [
            ModelConfig(
                model_name="claude-3-5-sonnet-20241022",
                api_key_env="ANTHROPIC_API_KEY",
                model_params={"temperature": 0.1, "max_tokens": 12288},
                enabled=bool(self.config.anthropic_api_key)
            ),
            ModelConfig(
                model_name="gpt-5",
                api_key_env="OPENAI_API_KEY",
                model_params={"temperature": 0.1, "max_tokens": 12288},
                enabled=bool(self.config.openai_api_key)
            )
        ]

        return {
            "code_planning": self._create_provider_config(code_planning_models, "code_planning"),
            "code_writing": self._create_provider_config(code_writing_models, "code_writing"),
            "embeddings": self._create_provider_config(embedding_models, "embeddings"),
            "research": self._create_provider_config(research_models, "research"),
            "business": self._create_provider_config(business_models, "business")
        }

    def _create_provider_config(self, models: List[ModelConfig], task_type: str) -> ProviderConfig:
        """Create provider configuration with fallback chain"""
        primary_config = models[0]
        fallback_configs = models[1:] if len(models) > 1 else []

        return ProviderConfig(
            primary_model=primary_config,
            fallback_models=fallback_configs,
            priority=1
        )

    def _validate_configuration(self):
        """Validate that at least one model is available for each task"""
        critical_tasks = ["code_planning", "code_writing", "embeddings", "research"]

        for task in critical_tasks:
            if task not in self._model_rankings:
                logger.warning(f"No models configured for task: {task}")
                continue

            provider_config = self._model_rankings[task]
            all_models_disabled = not provider_config.primary_model.enabled and \
                               not any(fallback.enabled for fallback in provider_config.fallback_models)

            if all_models_disabled:
                logger.error(f"CRITICAL: No enabled models available for task '{task}'")
                logger.error("Please configure at least one API key for this functionality")

    def get_model_config(self, task_type: str) -> Optional[ProviderConfig]:
        """Get the best available model configuration for a specific task"""
        if task_type not in self._model_rankings:
            logger.warning(f"Unknown task type: {task_type}")
            return None

        return self._model_rankings[task_type]

    def get_available_models(self) -> Dict[str, List[str]]:
        """Get list of available models by task type"""
        available = {}
        for task_type, provider_config in self._model_rankings.items():
            models = [provider_config.primary_model.model_name]
            models.extend([fm.model_name for fm in provider_config.fallback_models if fm.enabled])
            available[task_type] = [m for m in models if m]  # Filter out empty strings
        return available

    def validate_api_keys(self) -> Dict[str, bool]:
        """Validate that all configured API keys are present"""
        validation_results = {}

        # Check all API key environment variables
        api_key_fields = [
            "openai_api_key", "anthropic_api_key", "gemini_api_key", "gemini_embed_key",
            "grok_api_key", "grok_api_key_heavy", "cohere_api_key", "together_api_key",
            "tavily_api_key", "perplexity_api_key", "serper_api_key", "apify_api_token",
            "zenrows_api_key", "brightdata_api_key"
        ]

        for field_name in api_key_fields:
            field_value = getattr(self.config, field_name)
            validation_results[field_name] = field_value is not None and len(str(field_value)) > 0

        return validation_results


# Global configuration instance
_config_instance = None
_catalog_instance = None


def get_config() -> SophiaAgentConfig:
    """Get the global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = SophiaAgentConfig()
    return _config_instance


def get_model_catalog() -> ModelCatalog:
    """Get the global model catalog instance"""
    global _catalog_instance
    if _catalog_instance is None:
        config = get_config()
        _catalog_instance = ModelCatalog(config)
    return _catalog_instance


def validate_environment_setup() -> Dict[str, Any]:
    """Validate the complete environment setup"""
    config = get_config()
    catalog = get_model_catalog()

    validation_results = {
        "config_loaded": True,
        "api_keys_validation": catalog.validate_api_keys(),
        "available_models": catalog.get_available_models(),
        "redis_connection": bool(config.redis_url),
        "vector_database": bool(config.qdrant_url),
        "database_connection": bool(config.postgres_url)
    }

    return validation_results
