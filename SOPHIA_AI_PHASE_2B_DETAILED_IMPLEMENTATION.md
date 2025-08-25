# Sophia AI Phase 2B: Business Intelligence Enhancement - Detailed Implementation Plan

**Date**: August 25, 2025  
**Duration**: 2 Weeks (Weeks 7-8)  
**Priority**: HIGH - Following Phase 2A  
**Goal**: Implement AGNO business intelligence teams with advanced CRM integration and predictive analytics

## Executive Summary

Phase 2B extends the AGNO team capabilities into business intelligence, creating specialized teams that integrate with Salesforce, HubSpot, Gong.io, and other business services. This phase demonstrates how AI agents can provide actionable business insights, automate workflows, and deliver predictive analytics for revenue optimization.

### Key Objectives
1. Create Sales Intelligence Team with multi-CRM integration
2. Implement Client Health Monitoring with predictive analytics
3. Build Business Workflow Automation capabilities
4. Develop Revenue Optimization and forecasting insights
5. Enable proactive business intelligence notifications

## Business Intelligence Architecture

### Team Structure

| Team | Primary Focus | Integrations | Key Outputs |
|------|--------------|--------------|-------------|
| Sales Intelligence Team | Deal analysis, pipeline health | Salesforce, HubSpot, Gong | Deal insights, win probability |
| Client Health Team | Customer success, churn prevention | Intercom, Support tickets, Usage data | Health scores, risk alerts |
| Revenue Analytics Team | Forecasting, optimization | Financial systems, CRM data | Revenue forecasts, opportunities |
| Workflow Automation Team | Process optimization | Slack, Asana, Linear | Automated workflows, efficiency |

### Integration Points

1. **CRM Systems**: Salesforce, HubSpot via existing MCP services
2. **Communication**: Gong.io for call analysis, Slack for notifications
3. **Support**: Intercom for customer interactions
4. **Analytics**: Looker for visualization, custom analytics engine
5. **Workflow**: Asana, Linear for task management

## Week 7: Sales Intelligence Team

### Day 1-2: Sales Team Foundation

#### 7.1 Sales Intelligence Team Base
```python
# services/agno-teams/src/business/sales_intelligence_team.py
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
from enum import Enum

from agno import Team, Agent, Memory
from agno.collaboration import CollaborationMode
from agno_wrappers.agents import BusinessIntelligenceAgent, CRMAgent

class SalesPhase(Enum):
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
            
            return formatted_insights
            
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
                
        scoring_results = await asyncio.gather(*scoring_tasks)
        
        # Map scores to deal IDs
        for i, deal in enumerate(deals):
            if self._should_score_deal(deal, filters):
                scores[deal["id"]] = scoring_results.pop(0)
                
        # Update cached scores
        self.deal_scores.update(scores)
        
        return scores
        
    async def monitor_deal_changes(self):
        """Continuous monitoring of deal changes"""
        while True:
            try:
                # Fetch recent deal updates
                updates = await self._fetch_deal_updates()
                
                if updates:
                    # Analyze impact of changes
                    impacts = await self._analyze_deal_impacts(updates)
                    
                    # Generate alerts for significant changes
                    alerts = self._generate_alerts(impacts)
                    
                    # Send notifications
                    await self._send_notifications(alerts)
                    
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error monitoring deals: {e}")
                await asyncio.sleep(600)  # Back off on error
```

#### 7.2 Pipeline Analyst Agent
```python
# services/agno-teams/src/agents/sales/pipeline_analyst.py
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import statistics

from agno import Agent
from agno.tools import tool
from agno_wrappers.agents import CRMAgent

class PipelineAnalystAgent(Agent):
    """Analyzes sales pipeline health and identifies opportunities"""
    
    def __init__(self, name: str, crm_config: Dict[str, Any]):
        super().__init__(
            name=name,
            role="""I am a Pipeline Analyst responsible for:
            - Analyzing sales pipeline health and velocity
            - Identifying bottlenecks and stuck deals
            - Tracking conversion rates between stages
            - Providing pipeline coverage insights
            - Detecting trends and anomalies
            """,
            tools=self._create_tools()
        )
        
        # Initialize CRM connections
        self.salesforce = CRMAgent(crm_config["salesforce"])
        self.hubspot = CRMAgent(crm_config["hubspot"])
        
    @tool("fetch_pipeline_data")
    async def fetch_pipeline_data(
        self,
        time_period: str = "current_quarter",
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fetch comprehensive pipeline data from all CRM sources"""
        # Determine date range
        date_range = self._calculate_date_range(time_period)
        
        # Fetch from multiple sources in parallel
        sf_task = self.salesforce.get_opportunities(
            start_date=date_range["start"],
            end_date=date_range["end"],
            filters=filters
        )
        
        hs_task = self.hubspot.get_deals(
            start_date=date_range["start"],
            end_date=date_range["end"],
            filters=filters
        )
        
        sf_data, hs_data = await asyncio.gather(sf_task, hs_task)
        
        # Merge and normalize data
        merged_pipeline = self._merge_pipeline_data(sf_data, hs_data)
        
        # Calculate key metrics
        metrics = self._calculate_pipeline_metrics(merged_pipeline)
        
        return {
            "deals": merged_pipeline,
            "metrics": metrics,
            "date_range": date_range,
            "total_value": sum(d["amount"] for d in merged_pipeline),
            "deal_count": len(merged_pipeline)
        }
        
    @tool("analyze_pipeline_health")
    async def analyze_pipeline_health(
        self,
        pipeline_data: Dict[str, Any],
        historical_comparison: bool = True
    ) -> Dict[str, Any]:
        """Analyze overall pipeline health"""
        deals = pipeline_data["deals"]
        metrics = pipeline_data["metrics"]
        
        health_score = 0
        health_factors = []
        
        # Factor 1: Pipeline Coverage (vs quota)
        coverage = await self._calculate_pipeline_coverage(
            pipeline_data["total_value"]
        )
        health_factors.append({
            "factor": "pipeline_coverage",
            "score": coverage["score"],
            "status": coverage["status"],
            "details": f"{coverage['ratio']:.1f}x coverage"
        })
        health_score += coverage["score"] * 0.3
        
        # Factor 2: Stage Distribution
        distribution = self._analyze_stage_distribution(deals)
        health_factors.append({
            "factor": "stage_distribution",
            "score": distribution["score"],
            "status": distribution["status"],
            "details": distribution["message"]
        })
        health_score += distribution["score"] * 0.2
        
        # Factor 3: Deal Velocity
        velocity = self._calculate_deal_velocity(deals)
        health_factors.append({
            "factor": "deal_velocity",
            "score": velocity["score"],
            "status": velocity["status"],
            "details": f"Avg {velocity['days']:.0f} days in pipeline"
        })
        health_score += velocity["score"] * 0.2
        
        # Factor 4: Win Rate Trend
        if historical_comparison:
            win_trend = await self._analyze_win_rate_trend()
            health_factors.append({
                "factor": "win_rate_trend",
                "score": win_trend["score"],
                "status": win_trend["status"],
                "details": win_trend["message"]
            })
            health_score += win_trend["score"] * 0.3
            
        return {
            "overall_health_score": health_score,
            "health_status": self._get_health_status(health_score),
            "factors": health_factors,
            "recommendations": self._generate_health_recommendations(health_factors)
        }
        
    @tool("identify_bottlenecks")
    async def identify_bottlenecks(
        self,
        pipeline_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify pipeline bottlenecks and stuck deals"""
        deals = pipeline_data["deals"]
        bottlenecks = []
        
        # Analyze stage conversion rates
        stage_analysis = self._analyze_stage_conversions(deals)
        
        for stage, data in stage_analysis.items():
            if data["conversion_rate"] < 0.6:  # Less than 60% conversion
                bottlenecks.append({
                    "type": "low_conversion",
                    "stage": stage,
                    "severity": "high" if data["conversion_rate"] < 0.4 else "medium",
                    "conversion_rate": data["conversion_rate"],
                    "stuck_deals": data["stuck_count"],
                    "avg_days_stuck": data["avg_days"],
                    "recommendation": f"Focus on improving {stage} conversion"
                })
                
        # Identify stuck deals
        stuck_deals = self._find_stuck_deals(deals)
        if stuck_deals:
            bottlenecks.append({
                "type": "stuck_deals",
                "severity": "high" if len(stuck_deals) > 10 else "medium",
                "count": len(stuck_deals),
                "total_value": sum(d["amount"] for d in stuck_deals),
                "deals": stuck_deals[:5],  # Top 5
                "recommendation": "Review and re-engage stuck opportunities"
            })
            
        # Analyze rep performance disparities
        rep_performance = self._analyze_rep_performance(deals)
        for rep, stats in rep_performance.items():
            if stats["performance_index"] < 0.7:
                bottlenecks.append({
                    "type": "rep_performance",
                    "severity": "medium",
                    "rep": rep,
                    "performance_index": stats["performance_index"],
                    "deal_count": stats["deal_count"],
                    "recommendation": f"Provide coaching support for {rep}"
                })
                
        return sorted(bottlenecks, key=lambda x: 
                     {"high": 0, "medium": 1, "low": 2}[x["severity"]])
        
    def _analyze_stage_distribution(
        self,
        deals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze distribution of deals across stages"""
        stage_counts = {}
        total_deals = len(deals)
        
        for deal in deals:
            stage = deal.get("stage", "unknown")
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
            
        # Check for healthy funnel shape
        early_stage = sum(
            count for stage, count in stage_counts.items()
            if stage in ["qualification", "discovery", "demo"]
        )
        late_stage = sum(
            count for stage, count in stage_counts.items()
            if stage in ["negotiation", "closing"]
        )
        
        if total_deals == 0:
            return {
                "score": 0,
                "status": "critical",
                "message": "No deals in pipeline"
            }
            
        ratio = early_stage / late_stage if late_stage > 0 else float('inf')
        
        if 2 <= ratio <= 4:  # Healthy funnel ratio
            score = 100
            status = "healthy"
            message = "Well-balanced pipeline distribution"
        elif 1.5 <= ratio < 2 or 4 < ratio <= 5:
            score = 70
            status = "warning"
            message = "Pipeline distribution needs attention"
        else:
            score = 40
            status = "critical"
            message = "Unbalanced pipeline distribution"
            
        return {
            "score": score,
            "status": status,
            "message": message,
            "distribution": stage_counts
        }
```

### Day 3: Client Health Monitoring

#### 7.3 Client Health Team
```python
# services/agno-teams/src/business/client_health_team.py
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from agno import Team, Agent
from agno.tools import tool

@dataclass
class ClientHealthRequest:
    """Client health analysis request"""
    client_ids: Optional[List[str]] = None  # None means all clients
    include_predictions: bool = True
    time_window: int = 90  # days
    alert_threshold: float = 0.3  # Risk score threshold

@dataclass
class ClientHealthScore:
    """Client health assessment"""
    client_id: str
    client_name: str
    overall_score: float  # 0-1, higher is healthier
    risk_level: str  # low, medium, high, critical
    churn_probability: float
    factors: List[Dict[str, Any]]
    recommendations: List[str]
    predicted_ltv: float
    last_updated: datetime

class ClientHealthTeam(Team):
    """Team for monitoring and predicting client health"""
    
    def __init__(
        self,
        name: str = "SophiaClientHealthTeam",
        memory: Optional[Memory] = None,
        integrations: Optional[Dict[str, str]] = None
    ):
        self.integrations = integrations or self._default_integrations()
        
        # Initialize ML models
        self.churn_model = self._initialize_churn_model()
        self.ltv_model = self._initialize_ltv_model()
        
        # Initialize agents
        self.agents = self._create_agents()
        
        super().__init__(
            name=name,
            agents=list(self.agents.values()),
            mode=CollaborationMode.PARALLEL,
            memory=memory
        )
        
        # Health monitoring state
        self.health_scores = {}
        self.alert_history = []
        
    def _create_agents(self) -> Dict[str, Agent]:
        """Create specialized client health agents"""
        return {
            "usage_analyst": UsageAnalystAgent(
                name="UsageAnalyst",
                integrations=self.integrations
            ),
            "support_analyst": SupportAnalystAgent(
                name="SupportAnalyst",
                integrations=self.integrations
            ),
            "engagement_analyst": EngagementAnalystAgent(
                name="EngagementAnalyst",
                integrations=self.integrations
            ),
            "financial_analyst": FinancialAnalystAgent(
                name="FinancialAnalyst",
                integrations=self.integrations
            )
        }
        
    async def analyze_client_health(
        self,
        request: ClientHealthRequest
    ) -> List[ClientHealthScore]:
        """Perform comprehensive client health analysis"""
        # Get client list
        clients = await self._get_clients(request.client_ids)
        
        # Analyze each client in parallel
        health_tasks = []
        for client in clients:
            health_tasks.append(
                self._analyze_single_client(client, request)
            )
            
        health_scores = await asyncio.gather(*health_tasks)
        
        # Sort by risk level
        health_scores.sort(key=lambda x: x.churn_probability, reverse=True)
        
        # Generate alerts for at-risk clients
        alerts = self._generate_health_alerts(
            health_scores,
            request.alert_threshold
        )
        
        if alerts:
            await self._send_health_alerts(alerts)
            
        # Update cache
        for score in health_scores:
            self.health_scores[score.client_id] = score
            
        return health_scores
        
    async def _analyze_single_client(
        self,
        client: Dict[str, Any],
        request: ClientHealthRequest
    ) -> ClientHealthScore:
        """Analyze health for a single client"""
        client_id = client["id"]
        
        # Gather data from all sources in parallel
        usage_task = self.agents["usage_analyst"].analyze_usage(
            client_id,
            days=request.time_window
        )
        
        support_task = self.agents["support_analyst"].analyze_support(
            client_id,
            days=request.time_window
        )
        
        engagement_task = self.agents["engagement_analyst"].analyze_engagement(
            client_id,
            days=request.time_window
        )
        
        financial_task = self.agents["financial_analyst"].analyze_financials(
            client_id
        )
        
        # Gather all analyses
        usage, support, engagement, financial = await asyncio.gather(
            usage_task, support_task, engagement_task, financial_task
        )
        
        # Calculate health factors
        factors = []
        
        # Usage health
        usage_score = self._calculate_usage_score(usage)
        factors.append({
            "category": "usage",
            "score": usage_score,
            "weight": 0.3,
            "details": usage
        })
        
        # Support health
        support_score = self._calculate_support_score(support)
        factors.append({
            "category": "support",
            "score": support_score,
            "weight": 0.25,
            "details": support
        })
        
        # Engagement health
        engagement_score = self._calculate_engagement_score(engagement)
        factors.append({
            "category": "engagement",
            "score": engagement_score,
            "weight": 0.25,
            "details": engagement
        })
        
        # Financial health
        financial_score = self._calculate_financial_score(financial)
        factors.append({
            "category": "financial",
            "score": financial_score,
            "weight": 0.2,
            "details": financial
        })
        
        # Calculate overall health score
        overall_score = sum(
            f["score"] * f["weight"] for f in factors
        )
        
        # Predict churn probability if requested
        churn_probability = 0.0
        if request.include_predictions:
            features = self._extract_ml_features(
                usage, support, engagement, financial
            )
            churn_probability = self.churn_model.predict_proba([features])[0][1]
            
        # Predict LTV
        predicted_ltv = self._predict_ltv(
            financial, overall_score, churn_probability
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(
            overall_score, churn_probability
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            factors, risk_level
        )
        
        return ClientHealthScore(
            client_id=client_id,
            client_name=client["name"],
            overall_score=overall_score,
            risk_level=risk_level,
            churn_probability=churn_probability,
            factors=factors,
            recommendations=recommendations,
            predicted_ltv=predicted_ltv,
            last_updated=datetime.now()
        )
        
    def _calculate_usage_score(self, usage_data: Dict[str, Any]) -> float:
        """Calculate usage health score"""
        score = 0.0
        
        # Login frequency
        login_score = min(usage_data["login_count"] / 20, 1.0)  # 20+ logins is healthy
        score += login_score * 0.3
        
        # Feature adoption
        adoption_rate = usage_data["features_used"] / usage_data["total_features"]
        score += adoption_rate * 0.4
        
        # Usage trend
        if usage_data["trend"] == "increasing":
            score += 0.3
        elif usage_data["trend"] == "stable":
            score += 0.2
        else:  # decreasing
            score += 0.0
            
        return score
        
    async def monitor_health_changes(self):
        """Continuous monitoring of client health changes"""
        while True:
            try:
                # Get list of clients to monitor
                high_value_clients = await self._get_high_value_clients()
                
                # Quick health check for each
                for client in high_value_clients:
                    current_score = await self._quick_health_check(client["id"])
                    
                    # Compare with previous score
                    previous = self.health_scores.get(client["id"])
                    if previous and current_score:
                        score_change = current_score - previous.overall_score
                        
                        # Alert on significant degradation
                        if score_change < -0.1:  # 10% drop
                            await self._send_degradation_alert(
                                client,
                                previous,
                                current_score,
                                score_change
                            )
                            
                await asyncio.sleep(3600)  # Check hourly
                
            except Exception as e:
                logger.error(f"Error monitoring health: {e}")
                await asyncio.sleep(3600)
```

### Day 4: Revenue Analytics & Workflow Automation

#### 7.4 Revenue Analytics Team
```python
# services/agno-teams/src/business/revenue_analytics_team.py
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from agno import Team, Agent
from agno.tools import tool

class RevenueAnalyticsTeam(Team):
    """Team for revenue forecasting and optimization"""
    
    def __init__(
        self,
        name: str = "SophiaRevenueTeam",
        memory: Optional[Memory] = None
    ):
        self.agents = self._create_agents()
        
        super().__init__(
            name=name,
            agents=list(self.agents.values()),
            mode=CollaborationMode.COLLABORATIVE,
            memory=memory
        )
        
        # Forecasting models
        self.forecast_models = {}
        self.optimization_history = []
        
    @tool("forecast_revenue")
    async def forecast_revenue(
        self,
        time_horizon: int = 90,  # days
        confidence_level: float = 0.95,
        include_scenarios: bool = True
    ) -> Dict[str, Any]:
        """Generate revenue forecasts with confidence intervals"""
        # Gather historical data
        historical_data = await self._gather_historical_revenue()
        
        # Prepare time series data
        ts_data = self._prepare_timeseries(historical_data)
        
        # Generate base forecast
        base_forecast = self._generate_base_forecast(
            ts_data,
            time_horizon
        )
        
        # Calculate confidence intervals
        confidence_intervals = self._calculate_confidence_intervals(
            base_forecast,
            confidence_level
        )
        
        # Generate scenarios if requested
        scenarios = {}
        if include_scenarios:
            scenarios = await self._generate_scenarios(
                base_forecast,
                ts_data
            )
            
        # Identify revenue opportunities
        opportunities = await self._identify_opportunities(
            base_forecast,
            historical_data
        )
        
        return {
            "forecast": base_forecast,
            "confidence_intervals": confidence_intervals,
            "scenarios": scenarios,
            "opportunities": opportunities,
            "methodology": {
                "model": "Exponential Smoothing with seasonality",
                "confidence_level": confidence_level,
                "historical_period": len(ts_data)
            }
        }
        
    async def _identify_opportunities(
        self,
        forecast: pd.DataFrame,
        historical_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify revenue optimization opportunities"""
        opportunities = []
        
        # Analyze product mix opportunities
        product_analysis = await self.agents["product_analyst"].analyze_product_revenue(
            historical_data
        )
        
        for product in product_analysis["underperforming"]:
            opportunities.append({
                "type": "product_optimization",
                "product": product["name"],
                "current_revenue": product["revenue"],
                "potential_increase": product["potential"],
