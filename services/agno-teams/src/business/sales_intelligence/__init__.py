"""
Sales Intelligence Team for Sophia AI
Provides comprehensive sales pipeline analysis, deal scoring, and win probability predictions.
"""

from .sales_intelligence_team import SalesIntelligenceTeam, SalesAnalysisRequest, SalesInsight
from .agents.pipeline_analyst import PipelineAnalystAgent
from .agents.deal_scorer import DealScorerAgent
from .agents.competitor_analyst import CompetitorAnalystAgent
from .agents.sales_coach import SalesCoachAgent
from .agents.revenue_forecaster import RevenueForecastAgent

__all__ = [
    "SalesIntelligenceTeam",
    "SalesAnalysisRequest",
    "SalesInsight",
    "PipelineAnalystAgent",
    "DealScorerAgent",
    "CompetitorAnalystAgent",
    "SalesCoachAgent",
    "RevenueForecastAgent"
]