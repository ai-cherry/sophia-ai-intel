"""
Sales Intelligence Team - Main implementation for comprehensive sales analysis
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

from agno import Team, Agent, Memory
from agno.collaboration import CollaborationMode

# Configure logging
logger = logging.getLogger(__name__)

class SalesPhase(Enum):
    """Sales analysis phases"""
    PIPELINE_ANALYSIS = "pipeline_analysis"
    DEAL_SCORING = "deal_scoring"
    WIN_PROBABILITY = "win_probability"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    RECOMMENDATION = "recommendation"

@dataclass
class SalesAnalysisRequest:
    """Sales analysis request structure"""
    analysis_type: str  # pipeline, deal, forecast, competitor
    time_period: str = "current_quarter"
    filters: Dict[str, Any] = None
    include_predictions: bool = True
    output_format: str = "dashboard"  # dashboard, report, alerts
    priority_threshold: float = 0.7  # Minimum priority score for alerts

@dataclass
class SalesInsight:
    """Sales insight result"""
    insight_id: str
    type: str  # opportunity, risk, trend, anomaly
    priority: str  # high, medium, low
    title: str
    description: str
    data: Dict[str, Any]
    recommended_actions: List[str]
    confidence: float
    impact_estimate: Dict[str, float]  # revenue impact
    created_at: datetime
    expires_at: Optional[datetime] = None

class SalesIntelligenceTeam(Team):
    """AGNO Sales Intelligence Team"""

    def __init__(
        self,
        name: str = "SophiaSalesTeam",
        memory: Optional[Memory] = None,
        crm_config: Optional[Dict[str, Any]] = None
    ):
        self.crm_config = crm_config or self._default_crm_config()

        # Initialize agents
        self.agents = self._create_agents()

        super().__init__(
            name=name,
            agents=list(self.agents.values()),
            mode=CollaborationMode.COLLABORATIVE,
            memory=memory
        )

        # Sales state tracking
        self.pipeline_cache = {}
        self.deal_scores = {}
        self.active_analyses = {}
        self.insights_history = []

        logger.info(f"Initialized {name} with {len(self.agents)} agents")

    def _default_crm_config(self) -> Dict[str, Any]:
        """Default CRM configuration"""
        return {
            "salesforce": {
                "url": "http://mcp-salesforce:8080",
                "sync_interval": 300  # 5 minutes
            },
            "hubspot": {
                "url": "http://mcp-hubspot:8080",
                "sync_interval": 300
            },
            "gong": {
                "url": "http://mcp-gong:8080",
                "sync_interval": 3600  # 1 hour
            }
        }

    def _create_agents(self) -> Dict[str, Agent]:
        """Create specialized sales agents"""
        from .agents.pipeline_analyst import PipelineAnalystAgent
        from .agents.deal_scorer import DealScorerAgent
        from .agents.competitor_analyst import CompetitorAnalystAgent
        from .agents.sales_coach import SalesCoachAgent
        from .agents.revenue_forecaster import RevenueForecastAgent

        agents = {}

        # Pipeline Analyst
        agents["pipeline_analyst"] = PipelineAnalystAgent(
            name="PipelineAnalyst",
            crm_config=self.crm_config
        )

        # Deal Scorer
        agents["deal_scorer"] = DealScorerAgent(
            name="DealScorer",
            crm_config=self.crm_config
        )

        # Competitor Analyst
        agents["competitor_analyst"] = CompetitorAnalystAgent(
            name="CompetitorAnalyst",
            crm_config=self.crm_config
        )

        # Sales Coach (using Gong insights)
        agents["sales_coach"] = SalesCoachAgent(
            name="SalesCoach",
            gong_config=self.crm_config["gong"]
        )

        # Revenue Forecaster
        agents["forecaster"] = RevenueForecastAgent(
            name="RevenueForecaster",
            crm_config=self.crm_config
        )

        return agents

    async def analyze_sales(
        self,
        request: SalesAnalysisRequest
    ) -> List[SalesInsight]:
        """Perform comprehensive sales analysis"""
        analysis_id = self._generate_analysis_id()
        self.active_analyses[analysis_id] = request

        try:
            logger.info(f"Starting sales analysis {analysis_id} for {request.analysis_type}")

            # Phase 1: Pipeline Analysis
            pipeline_data = await self._analyze_pipeline(request)

            # Phase 2: Deal Scoring
            deal_scores = await self._score_deals(
                pipeline_data,
                request.filters
            )

            # Phase 3: Win Probability Calculation
            win_probabilities = await self._calculate_win_probability(
                deal_scores,
                include_predictions=request.include_predictions
            )

            # Phase 4: Competitor Analysis
            competitor_insights = await self._analyze_competitors(
                pipeline_data,
                win_probabilities
            )

            # Phase 5: Generate Recommendations
            insights = await self._generate_insights(
                pipeline_data,
                deal_scores,
                win_probabilities,
                competitor_insights
            )

            # Format output
            formatted_insights = self._format_insights(
                insights,
                request.output_format
            )

            # Store insights
            self.insights_history.extend(formatted_insights)

            logger.info(f"Completed sales analysis {analysis_id} with {len(formatted_insights)} insights")

            return formatted_insights

        except Exception as e:
            logger.error(f"Error in sales analysis {analysis_id}: {e}")
            raise
        finally:
            del self.active_analyses[analysis_id]

    async def _analyze_pipeline(
        self,
        request: SalesAnalysisRequest
    ) -> Dict[str, Any]:
        """Analyze sales pipeline health"""
        analyst = self.agents["pipeline_analyst"]

        # Fetch current pipeline data
        pipeline_data = await analyst.fetch_pipeline_data(
            time_period=request.time_period,
            filters=request.filters
        )

        # Analyze pipeline health
        health_analysis = await analyst.analyze_pipeline_health(
            pipeline_data,
            historical_comparison=True
        )

        # Identify bottlenecks
        bottlenecks = await analyst.identify_bottlenecks(pipeline_data)

        # Cache results
        self.pipeline_cache[request.time_period] = {
            "data": pipeline_data,
            "health": health_analysis,
            "bottlenecks": bottlenecks,
            "timestamp": datetime.now()
        }

        return {
            "pipeline": pipeline_data,
            "health_metrics": health_analysis,
            "bottlenecks": bottlenecks
        }

    async def _score_deals(
        self,
        pipeline_data: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """Score all deals in pipeline"""
        scorer = self.agents["deal_scorer"]

        deals = pipeline_data["pipeline"]["deals"]
        scores = {}

        # Score deals in parallel
        scoring_tasks = []
        for deal in deals:
            if self._should_score_deal(deal, filters):
                scoring_tasks.append(
                    scorer.score_deal(deal)
                )

        if scoring_tasks:
            scoring_results = await asyncio.gather(*scoring_tasks)

            # Map scores to deal IDs
            for i, deal in enumerate(deals):
                if self._should_score_deal(deal, filters):
                    scores[deal["id"]] = scoring_results.pop(0)

        # Update cached scores
        self.deal_scores.update(scores)

        return scores

    async def _calculate_win_probability(
        self,
        deal_scores: Dict[str, float],
        include_predictions: bool = True
    ) -> Dict[str, float]:
        """Calculate win probability for deals"""
        forecaster = self.agents["forecaster"]

        probabilities = {}

        for deal_id, score in deal_scores.items():
            if include_predictions:
                # Use ML model for prediction
                probability = await forecaster.predict_win_probability(
                    deal_id, score
                )
            else:
                # Use rule-based estimation
                probability = self._estimate_win_probability(score)

            probabilities[deal_id] = probability

        return probabilities

    async def _analyze_competitors(
        self,
        pipeline_data: Dict[str, Any],
        win_probabilities: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze competitor landscape"""
        competitor_analyst = self.agents["competitor_analyst"]

        # Analyze competitive threats
        competitor_analysis = await competitor_analyst.analyze_competitive_threats(
            pipeline_data["pipeline"]["deals"]
        )

        # Assess competitive advantages
        competitive_advantages = await competitor_analyst.assess_competitive_advantages(
            win_probabilities
        )

        return {
            "threats": competitor_analysis,
            "advantages": competitive_advantages
        }

    async def _generate_insights(
        self,
        pipeline_data: Dict[str, Any],
        deal_scores: Dict[str, float],
        win_probabilities: Dict[str, float],
        competitor_insights: Dict[str, Any]
    ) -> List[SalesInsight]:
        """Generate actionable insights from all analyses"""
        insights = []

        # Generate pipeline health insights
        pipeline_insights = self._generate_pipeline_insights(
            pipeline_data
        )
        insights.extend(pipeline_insights)

        # Generate deal-specific insights
        deal_insights = self._generate_deal_insights(
            deal_scores, win_probabilities
        )
        insights.extend(deal_insights)

        # Generate competitor insights
        competitor_insights_list = self._generate_competitor_insights(
            competitor_insights
        )
        insights.extend(competitor_insights_list)

        # Generate coaching insights
        coaching_insights = await self._generate_coaching_insights()
        insights.extend(coaching_insights)

        return insights

    def _generate_pipeline_insights(
        self,
        pipeline_data: Dict[str, Any]
    ) -> List[SalesInsight]:
        """Generate insights from pipeline analysis"""
        insights = []
        health = pipeline_data["health_metrics"]
        bottlenecks = pipeline_data["bottlenecks"]

        # Pipeline health insights
        if health["overall_health_score"] < 60:
            insights.append(SalesInsight(
                insight_id=self._generate_insight_id(),
                type="risk",
                priority="high",
                title="Pipeline Health Critical",
                description=f"Overall pipeline health score is {health['overall_health_score']:.1f}%. Immediate attention required.",
                data={"health_score": health["overall_health_score"], "factors": health["factors"]},
                recommended_actions=[
                    "Review pipeline coverage and identify gaps",
                    "Address stage conversion bottlenecks",
                    "Focus on high-value deal progression"
                ],
                confidence=0.85,
                impact_estimate={"revenue_impact": -0.15},  # 15% potential revenue loss
                created_at=datetime.now()
            ))

        # Bottleneck insights
        for bottleneck in bottlenecks:
            if bottleneck["severity"] == "high":
                insights.append(SalesInsight(
                    insight_id=self._generate_insight_id(),
                    type="opportunity",
                    priority="high",
                    title=f"Critical Bottleneck: {bottleneck['type']}",
                    description=bottleneck.get("recommendation", "Address this bottleneck immediately"),
                    data=bottleneck,
                    recommended_actions=[bottleneck.get("recommendation", "Review and address")],
                    confidence=0.8,
                    impact_estimate={"revenue_impact": 0.1},  # 10% potential revenue gain
                    created_at=datetime.now()
                ))

        return insights

    def _generate_deal_insights(
        self,
        deal_scores: Dict[str, float],
        win_probabilities: Dict[str, float]
    ) -> List[SalesInsight]:
        """Generate insights from deal analysis"""
        insights = []

        for deal_id, score in deal_scores.items():
            probability = win_probabilities.get(deal_id, 0)

            # High-value deals with low win probability
            if score > 0.8 and probability < 0.4:
                insights.append(SalesInsight(
                    insight_id=self._generate_insight_id(),
                    type="risk",
                    priority="high",
                    title="High-Value Deal at Risk",
                    description=f"Deal {deal_id} has high value but low win probability ({probability:.1%})",
                    data={"deal_id": deal_id, "score": score, "probability": probability},
                    recommended_actions=[
                        "Schedule immediate follow-up",
                        "Address key concerns identified",
                        "Consider involving executive sponsor"
                    ],
                    confidence=0.75,
                    impact_estimate={"revenue_impact": -0.2},  # 20% risk to this deal
                    created_at=datetime.now()
                ))

            # Low-value deals with high win probability
            elif score < 0.3 and probability > 0.7:
                insights.append(SalesInsight(
                    insight_id=self._generate_insight_id(),
                    type="opportunity",
                    priority="medium",
                    title="Quick Win Opportunity",
                    description=f"Deal {deal_id} has high win probability but lower value",
                    data={"deal_id": deal_id, "score": score, "probability": probability},
                    recommended_actions=[
                        "Fast-track this deal for quick closure",
                        "Minimize resources while ensuring success",
                        "Use as reference for similar deals"
                    ],
                    confidence=0.7,
                    impact_estimate={"revenue_impact": 0.05},  # 5% revenue gain
                    created_at=datetime.now()
                ))

        return insights

    def _generate_competitor_insights(
        self,
        competitor_data: Dict[str, Any]
    ) -> List[SalesInsight]:
        """Generate insights from competitor analysis"""
        insights = []

        threats = competitor_data.get("threats", [])
        advantages = competitor_data.get("advantages", [])

        # High-threat competitors
        for threat in threats:
            if threat.get("severity", "low") == "high":
                insights.append(SalesInsight(
                    insight_id=self._generate_insight_id(),
                    type="risk",
                    priority="high",
                    title=f"Competitive Threat: {threat.get('competitor', 'Unknown')}",
                    description=threat.get("description", "Competitive pressure detected"),
                    data=threat,
                    recommended_actions=[
                        "Develop competitive response strategy",
                        "Highlight unique value propositions",
                        "Accelerate deal closure timeline"
                    ],
                    confidence=0.8,
                    impact_estimate={"revenue_impact": -0.1},  # 10% potential revenue loss
                    created_at=datetime.now()
                ))

        # Competitive advantages
        for advantage in advantages:
            if advantage.get("strength", "low") == "high":
                insights.append(SalesInsight(
                    insight_id=self._generate_insight_id(),
                    type="opportunity",
                    priority="medium",
                    title=f"Competitive Advantage: {advantage.get('area', 'Unknown')}",
                    description=advantage.get("description", "Strong competitive position"),
                    data=advantage,
                    recommended_actions=[
                        "Leverage this advantage in messaging",
                        "Highlight in competitive situations",
                        "Use as differentiator in negotiations"
                    ],
                    confidence=0.75,
                    impact_estimate={"revenue_impact": 0.08},  # 8% potential revenue gain
                    created_at=datetime.now()
                ))

        return insights

    async def _generate_coaching_insights(self) -> List[SalesInsight]:
        """Generate coaching insights from sales interactions"""
        coach = self.agents["sales_coach"]

        # Get recent coaching opportunities
        coaching_opportunities = await coach.identify_coaching_opportunities()

        insights = []
        for opportunity in coaching_opportunities:
            if opportunity.get("priority", "low") == "high":
                insights.append(SalesInsight(
                    insight_id=self._generate_insight_id(),
                    type="opportunity",
                    priority="medium",
                    title=f"Coaching Opportunity: {opportunity.get('rep_name', 'Unknown')}",
                    description=opportunity.get("description", "Coaching opportunity identified"),
                    data=opportunity,
                    recommended_actions=[
                        "Schedule coaching session",
                        "Provide specific feedback",
                        "Share best practices"
                    ],
                    confidence=0.7,
                    impact_estimate={"revenue_impact": 0.05},  # 5% potential revenue gain
                    created_at=datetime.now()
                ))

        return insights

    def _format_insights(
        self,
        insights: List[SalesInsight],
        output_format: str
    ) -> List[SalesInsight]:
        """Format insights for output"""
        if output_format == "dashboard":
            # Sort by priority and impact
            insights.sort(key=lambda x: (
                {"high": 0, "medium": 1, "low": 2}[x.priority],
                -abs(x.impact_estimate.get("revenue_impact", 0))
            ))
        elif output_format == "alerts":
            # Filter for high-priority insights only
            insights = [i for i in insights if i.priority == "high"]

        return insights

    def _should_score_deal(
        self,
        deal: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Determine if a deal should be scored"""
        if not filters:
            return True

        # Apply filters
        if "min_amount" in filters and deal.get("amount", 0) < filters["min_amount"]:
            return False

        if "max_amount" in filters and deal.get("amount", 0) > filters["max_amount"]:
            return False

        if "stages" in filters and deal.get("stage") not in filters["stages"]:
            return False

        return True

    def _estimate_win_probability(self, score: float) -> float:
        """Simple rule-based win probability estimation"""
        if score >= 0.8:
            return 0.75
        elif score >= 0.6:
            return 0.5
        elif score >= 0.4:
            return 0.25
        else:
            return 0.1

    def _generate_analysis_id(self) -> str:
        """Generate unique analysis ID"""
        return f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(self)}"

    def _generate_insight_id(self) -> str:
        """Generate unique insight ID"""
        return f"insight_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(self)}"

    async def get_pipeline_health(self) -> Dict[str, Any]:
        """Get current pipeline health status"""
        cache_key = "current_quarter"
        if cache_key in self.pipeline_cache:
            cached = self.pipeline_cache[cache_key]
            if (datetime.now() - cached["timestamp"]).seconds < 300:  # 5 minutes
                return cached

        # Fetch fresh data
        request = SalesAnalysisRequest(
            analysis_type="pipeline",
            time_period="current_quarter"
        )
        pipeline_data = await self._analyze_pipeline(request)

        return pipeline_data

    async def get_deal_score(self, deal_id: str) -> Optional[float]:
        """Get score for specific deal"""
        if deal_id in self.deal_scores:
            return self.deal_scores[deal_id]

        # Score the deal
        scorer = self.agents["deal_scorer"]
        score = await scorer.score_deal({"id": deal_id})

        self.deal_scores[deal_id] = score
        return score

    async def get_recent_insights(
        self,
        limit: int = 10,
        priority_filter: Optional[str] = None
    ) -> List[SalesInsight]:
        """Get recent insights with optional filtering"""
        insights = self.insights_history[-limit:]

        if priority_filter:
            insights = [i for i in insights if i.priority == priority_filter]

        return insights

    async def cleanup_old_data(self, days: int = 30):
        """Clean up old cached data"""
        cutoff_date = datetime.now() - timedelta(days=days)

        # Clean pipeline cache
        self.pipeline_cache = {
            k: v for k, v in self.pipeline_cache.items()
            if v["timestamp"] > cutoff_date
        }

        # Clean insights history
        self.insights_history = [
            i for i in self.insights_history
            if i.created_at > cutoff_date
        ]

        logger.info(f"Cleaned up data older than {days} days")