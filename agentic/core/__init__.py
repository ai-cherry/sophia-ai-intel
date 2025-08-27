# Sophia AI Core Agentic Module
# ================================
# Core agentic functionality including configuration and base agent creation

from .config import get_config, SophiaAgentConfig
from .base_agent import create_agent, SophiaAgentFactory

# Export all public functions
def get_swarm_manager():
    """Get swarm manager instance - placeholder for future implementation"""
    from ..swarms.research.deep_research_swarm import create_deep_research_swarm
    return create_deep_research_swarm()

def BaseAgent(**kwargs):
    """Create a base agent with default settings"""
    return create_agent(**kwargs)

__all__ = [
    "get_config",
    "SophiaAgentConfig",
    "create_agent",
    "SophiaAgentFactory",
    "get_swarm_manager",
    "BaseAgent"
]
