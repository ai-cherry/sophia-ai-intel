# Sophia AI Agentic Base Agent Factory
# =======================================
# Factory for creating Agno agents with proper model rankings and memory

from typing import Dict, List, Optional, Any, Union
import logging
import os
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude
from agno.models.google import Gemini
from agno.models.groq import Groq
from agno.models.cohere import CohereChat
from agno.models.together import Together
from agno.memory import AgentMemory
from agno.storage.redis import RedisMemory
from agno.knowledge import AgentKnowledge
import weaviate
from weaviate.classes.init import Auth
from .config import get_config, get_model_catalog

logger = logging.getLogger(__name__)


class SophiaAgentFactory:
    """Factory for creating optimized Agno agents with proper model ranking and memory management"""

    def __init__(self):
        self.config = get_config()
        self.catalog = get_model_catalog()
        self._model_instances = {}
        self._memory_instances = {}

    def create_agent(self,
                    agent_type: str = "general",
                    name: str = "SophiaAgent",
                    role: Optional[str] = None,
                    instructions: Optional[List[str]] = None,
                    tools: Optional[List[Any]] = None,
                    knowledge: Optional[List[Any]] = None,
                    memory: bool = True,
                    knowledge_base: bool = True) -> Agent:
        """
        Create an optimized Agno agent with proper model ranking and memory management

        Args:
            agent_type: Type of agent ('coding', 'research', 'business', 'general')
            name: Name for the agent
            role: Role description for the agent
            instructions: List of task-specific instructions
            tools: List of tools to attach to the agent
            knowledge: List of knowledge sources
            memory: Whether to enable memory
            knowledge_base: Whether to use vector knowledge base
        """

        # Get model configuration for the agent type
        model_config = self.catalog.get_model_config(agent_type)
        if not model_config:
            logger.warning(f"No model config found for {agent_type}, falling back to general")
            model_config = self.catalog.get_model_config("research")  # Fallback

        # Create primary model instance with fallbacks
        model = self._get_model_instance(model_config.primary_model)
        model_fallbacks = [self._get_model_instance(fm) for fm in model_config.fallback_models if fm.enabled]

        # Set up memory if requested
        agent_memory = None
        agent_knowledge = None

        if memory:
            agent_memory = self._create_memory(name)

        if knowledge_base:
            agent_knowledge = self._create_knowledge_base()

        # Default instructions based on agent type
        if not instructions:
            instructions = self._get_default_instructions(agent_type)

        # Create and return the agent
        agent = Agent(
            name=name,
            role=role or self._get_default_role(agent_type),
            model=model,
            model_fallbacks=model_fallbacks,
            instructions=instructions,
            tools=tools or [],
            knowledge=agent_knowledge,
            memory=agent_memory,
            add_datetime_to_instructions=True,
            show_tool_calls=True,
            markdown=True,
            debug=self.config.debug
        )

        logger.info(f"Created {agent_type} agent: {name}")
        return agent

    def _get_model_instance(self, model_config):
        """Get or create a model instance for the given configuration"""
        model_key = f"{model_config.model_name}_{model_config.api_key_env}"

        if model_key in self._model_instances:
            return self._model_instances[model_key]

        # Create model instance based on provider
        if "gpt" in model_config.model_name.lower():
            model = OpenAIChat(
                id=model_config.model_name,
                api_key=self._get_api_key(model_config.api_key_env)
            )
        elif "claude" in model_config.model_name.lower():
            model = Claude(
                id=model_config.model_name,
                api_key=self._get_api_key(model_config.api_key_env)
            )
        elif "gemini" in model_config.model_name.lower():
            model = Gemini(
                id=model_config.model_name,
                api_key=self._get_api_key(model_config.api_key_env)
            )
        elif "grok" in model_config.model_name.lower():
            model = Groq(
                id=model_config.model_name,
                api_key=self._get_api_key(model_config.api_key_env)
            )
        elif "cohere" in model_config.model_name.lower():
            model = CohereChat(
                id=model_config.model_name,
                api_key=self._get_api_key(model_config.api_key_env)
            )
        elif "together" in model_config.model_name.lower():
            model = Together(
                id=model_config.model_name,
                api_key=self._get_api_key(model_config.api_key_env)
            )
        else:
            logger.error(f"Unsupported model: {model_config.model_name}")
            raise ValueError(f"Unsupported model: {model_config.model_name}")

        self._model_instances[model_key] = model
        return model

    def _get_api_key(self, env_var: str) -> str:
        """Get API key from environment variable"""
        api_key = getattr(self.config, env_var.lower(), None)
        if not api_key:
            api_key = os.getenv(env_var)
        if not api_key:
            raise ValueError(f"API key for {env_var} not found in environment or config")
        return api_key

    def _create_memory(self, agent_name: str) -> AgentMemory:
        """Create memory configuration for the agent"""
        memory_key = f"memory_{agent_name}"

        if memory_key in self._memory_instances:
            return self._memory_instances[memory_key]

        # Create Redis memory for agent storage
        redis_memory = RedisMemory(
            url=self.config.redis_url,
            db=0,
            collection_name=f"agent_memory_{agent_name}"
        )

        # Use Redis memory directly for agent memory
        memory = AgentMemory(
            db=redis_memory,
            create_user_memories=True,
            create_session_summaries=True,
            update_user_memories_after_run=True
        )

        self._memory_instances[memory_key] = memory
        return memory

    def _create_knowledge_base(self) -> AgentKnowledge:
        """Create knowledge base configuration"""
        weaviate_client = weaviate.connect_to_weaviate_cloud(
            cluster_url=self.config.weaviate_url,
            auth_credentials=Auth.api_key(self.config.weaviate_api_key)
        )

        return AgentKnowledge(
            vector_db=weaviate_client,
            num_documents=10,
            optimizer={"chunk_size": 1500, "overlap": 100}
        )

    def _get_default_role(self, agent_type: str) -> str:
        """Get default role description for agent type"""
        roles = {
            "coding": "Senior Software Engineering Lead responsible for architecting, planning, and implementing robust software solutions",
            "research": "Research Director specialized in deep market analysis, competitive intelligence, and trend synthesis",
            "business": "Chief Strategy Officer focused on quantitative analysis, risk assessment, and business intelligence",
            "general": "Senior AI Assistant capable of complex multi-step tasks and strategic analysis"
        }
        return roles.get(agent_type, roles["general"])

    def _get_default_instructions(self, agent_type: str) -> List[str]:
        """Get default instructions for agent type"""
        instruction_sets = {
            "coding": [
                "You are a senior software engineering lead with expertise in system architecture, microservices, and scalable solutions.",
                "When planning code, always consider scalability, maintainability, security, and testing requirements.",
                "Break down complex problems into smaller, manageable components with clear interfaces.",
                "Use proper design patterns and follow established best practices for the technology stack.",
                "Always provide clear documentation and consider the deployment and operational aspects.",
                "Think step-by-step through complex problems, showing your reasoning clearly."
            ],
            "research": [
                "You are a research director specialized in deep market analysis and competitive intelligence.",
                "Use web scraping and AI search tools to gather comprehensive information.",
                "Synthesize findings into actionable insights and strategic recommendations.",
                "Always verify information from multiple sources and cite your references.",
                "Structure your research with clear sections and actionable conclusions.",
                "Consider both qualitative and quantitative aspects of your research topics."
            ],
            "business": [
                "You are a chief strategy officer focused on quantitative analysis and risk assessment.",
                "Use financial data tools and market analysis to provide strategic insights.",
                "Structure recommendations with clear risk assessments and ROI considerations.",
                "Always provide data-driven analysis with proper caveats and assumptions.",
                "Focus on strategic implications and actionable business decisions."
            ],
            "general": [
                "You are a senior AI assistant capable of complex multi-step tasks and strategic analysis.",
                "Approach problems systematically and provide well-structured solutions.",
                "Be thorough in your analysis while remaining practical and actionable.",
                "Ask clarifying questions when needed and provide alternative perspectives."
            ]
        }
        return instruction_sets.get(agent_type, instruction_sets["general"])


# Global factory instance
_factory_instance = None


def get_agent_factory() -> SophiaAgentFactory:
    """Get the global agent factory instance"""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = SophiaAgentFactory()
    return _factory_instance


def create_agent(agent_type: str = "general", **kwargs) -> Agent:
    """
    Convenience function to create an agent quickly

    Args:
        agent_type: Type of agent to create
        **kwargs: Additional arguments passed to create_agent method
    """
    factory = get_agent_factory()
    return factory.create_agent(agent_type=agent_type, **kwargs)
