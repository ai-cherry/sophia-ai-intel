"""
Client Health Team - Main implementation for comprehensive client health monitoring
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

class HealthRiskLevel(Enum):
    """Client health risk levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class ClientHealthRequest:
    """Client health analysis request structure"""
    client_ids: Optional[List[str]] = None  # None means all clients
    include_predictions: bool = True
    time_window: int = 90  # days to analyze
    alert_threshold: float = 0.3  # Risk score threshold for alerts
    focus_areas: Optional[List[str]] = None  # usage, support, engagement, financial

@dataclass
class ClientHealthScore:
    """Client health assessment result"""
    client_id: str
    client_name: str
    overall_score: float  # 0-1, higher is healthier
    risk_level: str  # excellent, good, warning, critical
    churn_probability: float
    factors: List[Dict[str, Any]]
    recommendations: List[str]
    predicted_ltv: float
    last_updated: datetime
    next_review_date: Optional[datetime] = None

class ClientHealthTeam(Team):
    """AGNO Client Health Team for monitoring and predicting client health"""

    def __init__(
        self,
        name: str = "SophiaClientHealthTeam",
        memory: Optional[Memory] = None,
        integrations: Optional[Dict[str, str]] = None
    ):
        self.integrations = integrations or self._default_integrations()

        # Initialize ML models for churn prediction and LTV forecasting
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
        self.monitoring_active = False

        logger.info(f"Initialized {name} with {len(self.agents)} agents")

    def _default_integrations(self) -> Dict[str, str]:
        """Default integration endpoints"""
        return {
            "intercom": "http://mcp-intercom:8080",
            "support_tickets": "http://mcp-support:8080",
            "usage_metrics": "http://mcp-usage:8080",
            "financial_data": "http://mcp-financial:8080",
            "engagement_data": "http://mcp-engagement:8080"
        }

    def _create_agents(self) -> Dict[str, Agent]:
        """Create specialized client health agents"""
        from .agents.usage_analyst import UsageAnalystAgent
        from .agents.support_ticket_analyst import SupportTicketAnalystAgent
        from .agents.client_success_manager import ClientSuccessManagerAgent

        agents = {}

        # Usage Analyst
        agents["usage_analyst"] = UsageAnalystAgent(
            name="UsageAnalyst",
            integrations=self.integrations
        )

        # Support Analyst
        agents["support_analyst"] = SupportTicketAnalystAgent(
            name="SupportTicketAnalyst",
            integrations=self.integrations
        )

        # Client Success Manager
        agents["client_success_manager"] = ClientSuccessManagerAgent(
            name="ClientSuccessManager",
            integrations=self.integrations
        )

        return agents

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

        # Sort by risk level and churn probability
        health_scores.sort(key=lambda x: (
            self._risk_level_priority(x.risk_level),
            x.churn_probability
        ), reverse=True)

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

        logger.info(f"Analyzed {len(health_scores)} clients, generated {len(alerts)} alerts")

        return health_scores

    async def _analyze_single_client(
        self,
        client: Dict[str, Any],
        request: ClientHealthRequest
    ) -> ClientHealthScore:
        """Analyze health for a single client"""
        client_id = client["id"]

        # Gather data from all sources in parallel
        data_tasks = []
        focus_areas = request.focus_areas or ["usage", "support"]

        if "usage" in focus_areas:
            data_tasks.append(self.agents["usage_analyst"].analyze_usage(
                client_id, days=request.time_window
            ))

        if "support" in focus_areas:
            data_tasks.append(self.agents["support_analyst"].analyze_support_tickets(
                client_id, days=request.time_window
            ))

        

        # Gather all analyses
        results = await asyncio.gather(*data_tasks, return_exceptions=True)

        # Process results and handle exceptions
        analyses = {}
        for i, result in enumerate(results):
            area = focus_areas[i]
            if isinstance(result, Exception):
                logger.error(f"Error analyzing {area} for client {client_id}: {result}")
                analyses[area] = {"error": str(result)}
            else:
                analyses[area] = result

        # Calculate health factors
        factors = []
        factor_weights = {
            "usage": 0.50,
            "support": 0.50
        }

        for area in focus_areas:
            if area in analyses and "error" not in analyses[area]:
                analysis = analyses[area]
                score = self._calculate_area_score(area, analysis)
                factors.append({
                    "category": area,
                    "score": score,
                    "weight": factor_weights.get(area, 0.25),
                    "details": analysis,
                    "assessment": self._assess_area_health(area, score)
                })

        # Calculate overall health score
        overall_score = sum(
            f["score"] * f["weight"] for f in factors
        ) if factors else 0.0

        # Predict churn probability if requested
        churn_probability = 0.0
        if request.include_predictions and factors:
            features = self._extract_ml_features(factors)
            churn_probability = self.churn_model.predict_proba([features])[0][1]

        # Predict LTV
        predicted_ltv = self._predict_ltv(client, overall_score, churn_probability)

        # Determine risk level
        risk_level = self._determine_risk_level(overall_score, churn_probability)

        # Generate recommendations
        recommendations = self._generate_recommendations(factors, risk_level)

        # Calculate next review date based on risk level
        next_review = self._calculate_next_review_date(risk_level)

        return ClientHealthScore(
            client_id=client_id,
            client_name=client["name"],
            overall_score=overall_score,
            risk_level=risk_level,
            churn_probability=churn_probability,
            factors=factors,
            recommendations=recommendations,
            predicted_ltv=predicted_ltv,
            last_updated=datetime.now(),
            next_review_date=next_review
        )

    def _calculate_area_score(self, area: str, analysis: Dict[str, Any]) -> float:
        """Calculate health score for a specific area"""
        if area == "usage":
            return self._calculate_usage_score(analysis)
        elif area == "support":
            return self._calculate_support_score(analysis)
        else:
            return 0.5  # Neutral score for unknown areas

    def _calculate_usage_score(self, usage_data: Dict[str, Any]) -> float:
        """Calculate usage health score"""
        score = 0.0

        # Login frequency (30% weight)
        login_score = min(usage_data.get("login_count", 0) / 20, 1.0)  # 20+ logins is healthy
        score += login_score * 0.3

        # Feature adoption (40% weight)
        adoption_rate = usage_data.get("features_used", 0) / max(usage_data.get("total_features", 1), 1)
        score += adoption_rate * 0.4

        # Usage trend (30% weight)
        trend = usage_data.get("trend", "stable")
        if trend == "increasing":
            score += 0.3
        elif trend == "stable":
            score += 0.2
        else:  # decreasing
            score += 0.0

        return min(1.0, max(0.0, score))

    def _calculate_support_score(self, support_data: Dict[str, Any]) -> float:
        """Calculate support health score"""
        score = 0.0

        # Response time (40% weight)
        avg_response_time = support_data.get("avg_response_time", 24)  # hours
        response_score = max(0, 1 - (avg_response_time / 48))  # Better if under 48 hours
        score += response_score * 0.4

        # Ticket volume (30% weight)
        ticket_count = support_data.get("ticket_count", 0)
        # Moderate ticket count is healthy (not too many, not too few)
        if ticket_count < 5:
            volume_score = 0.3  # Too few tickets might indicate disengagement
        elif ticket_count < 20:
            volume_score = 1.0  # Healthy engagement
        else:
            volume_score = 0.6  # High volume might indicate issues
        score += volume_score * 0.3

        # Resolution rate (30% weight)
        resolution_rate = support_data.get("resolution_rate", 0.8)
        score += resolution_rate * 0.3

        return min(1.0, max(0.0, score))

    

    def _assess_area_health(self, area: str, score: float) -> str:
        """Provide qualitative assessment of area health"""
        if score >= 0.8:
            return f"{area.title()} health is excellent"
        elif score >= 0.6:
            return f"{area.title()} health is good"
        elif score >= 0.4:
            return f"{area.title()} health needs attention"
        else:
            return f"{area.title()} health is critical"

    def _extract_ml_features(self, factors: List[Dict[str, Any]]) -> List[float]:
        """Extract features for ML prediction"""
        features = []

        # Create feature vector from health factors
        for factor in factors:
            features.append(factor["score"])

        # Pad with zeros if we don't have all factors
        while len(features) < 2:
            features.append(0.5)

        return features[:2]  # Use first 2 features

    def _predict_ltv(self, client: Dict[str, Any], health_score: float, churn_prob: float) -> float:
        """Predict Lifetime Value"""
        base_revenue = client.get("annual_revenue", 50000)
        contract_length = client.get("contract_months", 12)

        # Adjust for health and churn risk
        health_multiplier = 0.5 + (health_score * 0.5)  # 0.5 to 1.0
        churn_adjustment = 1 - (churn_prob * 0.5)  # Reduce LTV for high churn risk

        predicted_ltv = base_revenue * (contract_length / 12) * health_multiplier * churn_adjustment

        return max(0, predicted_ltv)

    def _determine_risk_level(self, health_score: float, churn_probability: float) -> str:
        """Determine overall risk level"""
        # Combine health score and churn probability
        combined_risk = (1 - health_score) * 0.6 + churn_probability * 0.4

        if combined_risk <= 0.2:
            return HealthRiskLevel.EXCELLENT.value
        elif combined_risk <= 0.4:
            return HealthRiskLevel.GOOD.value
        elif combined_risk <= 0.6:
            return HealthRiskLevel.WARNING.value
        else:
            return HealthRiskLevel.CRITICAL.value

    def _generate_recommendations(
        self,
        factors: List[Dict[str, Any]],
        risk_level: str
    ) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []

        # Area-specific recommendations
        for factor in factors:
            area = factor["category"]
            score = factor["score"]

            if score < 0.6:
                if area == "usage":
                    recommendations.extend([
                        "Schedule product adoption review call",
                        "Provide personalized onboarding session",
                        "Send targeted feature education materials"
                    ])
                elif area == "support":
                    recommendations.extend([
                        "Proactive outreach to check satisfaction",
                        "Review support ticket trends",
                        "Offer additional training resources"
                    ])
                

        # Risk-level specific recommendations
        if risk_level == HealthRiskLevel.CRITICAL.value:
            recommendations.insert(0, "URGENT: Schedule immediate executive intervention")
        elif risk_level == HealthRiskLevel.WARNING.value:
            recommendations.insert(0, "HIGH PRIORITY: Schedule client success review within 7 days")

        return list(set(recommendations))  # Remove duplicates

    def _calculate_next_review_date(self, risk_level: str) -> datetime:
        """Calculate next review date based on risk level"""
        now = datetime.now()

        if risk_level == HealthRiskLevel.CRITICAL.value:
            return now + timedelta(days=7)
        elif risk_level == HealthRiskLevel.WARNING.value:
            return now + timedelta(days=14)
        elif risk_level == HealthRiskLevel.GOOD.value:
            return now + timedelta(days=30)
        else:  # EXCELLENT
            return now + timedelta(days=60)

    def _generate_health_alerts(
        self,
        health_scores: List[ClientHealthScore],
        threshold: float
    ) -> List[Dict[str, Any]]:
        """Generate alerts for at-risk clients"""
        alerts = []

        for score in health_scores:
            if score.churn_probability >= threshold or score.risk_level in ["critical", "warning"]:
                alerts.append({
                    "client_id": score.client_id,
                    "client_name": score.client_name,
                    "risk_level": score.risk_level,
                    "churn_probability": score.churn_probability,
                    "overall_score": score.overall_score,
                    "recommendations": score.recommendations,
                    "priority": "high" if score.risk_level == "critical" else "medium"
                })

        return alerts

    async def _send_health_alerts(self, alerts: List[Dict[str, Any]]):
        """Send health alerts through appropriate channels"""
        # This would integrate with notification systems
        logger.info(f"Sending {len(alerts)} health alerts")

        # Store in alert history
        self.alert_history.extend(alerts)

        # In a real implementation, this would:
        # - Send Slack notifications
        # - Create Salesforce tasks
        # - Send email alerts
        # - Update CRM records

    async def _get_clients(self, client_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get list of clients to analyze"""
        # Mock client data - in real implementation would fetch from CRM
        all_clients = [
            {"id": "client_001", "name": "Acme Corp", "annual_revenue": 150000, "contract_months": 12},
            {"id": "client_002", "name": "TechStart Inc", "annual_revenue": 75000, "contract_months": 6},
            {"id": "client_003", "name": "Enterprise Co", "annual_revenue": 500000, "contract_months": 24},
        ]

        if client_ids:
            return [c for c in all_clients if c["id"] in client_ids]
        else:
            return all_clients

    def _risk_level_priority(self, risk_level: str) -> int:
        """Get priority score for risk level sorting"""
        priorities = {
            "critical": 4,
            "warning": 3,
            "good": 2,
            "excellent": 1
        }
        return priorities.get(risk_level, 0)

    def _initialize_churn_model(self):
        """Initialize churn prediction model"""
        # Mock model - in real implementation would load trained ML model
        class MockChurnModel:
            def predict_proba(self, features):
                # Simple mock prediction based on features
                avg_feature = sum(features[0]) / len(features[0])
                churn_prob = max(0, min(1, 0.5 - avg_feature + 0.1))
                return [[1 - churn_prob, churn_prob]]

        return MockChurnModel()

    def _initialize_ltv_model(self):
        """Initialize LTV prediction model"""
        # Mock model - in real implementation would load trained ML model
        class MockLTVModel:
            def predict(self, features):
                # Simple mock prediction
                return [50000]  # Mock LTV value

        return MockLTVModel()

    async def get_client_health(self, client_id: str) -> Optional[ClientHealthScore]:
        """Get current health score for a specific client"""
        return self.health_scores.get(client_id)

    async def get_high_risk_clients(self, limit: int = 10) -> List[ClientHealthScore]:
        """Get highest risk clients"""
        high_risk = [
            score for score in self.health_scores.values()
            if score.risk_level in ["critical", "warning"]
        ]

        high_risk.sort(key=lambda x: x.churn_probability, reverse=True)
        return high_risk[:limit]

    async def get_health_trends(
        self,
        client_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get health trends for a client over time"""
        # Mock trend data - in real implementation would query historical data
        trends = []
        base_date = datetime.now() - timedelta(days=days)

        for i in range(days):
            date = base_date + timedelta(days=i)
            # Mock trend data
            trends.append({
                "date": date.strftime("%Y-%m-%d"),
                "overall_score": 0.6 + (i * 0.01),  # Slight upward trend
                "churn_probability": 0.3 - (i * 0.005)  # Slight downward trend
            })

        return trends

    async def start_monitoring(self):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True

        while self.monitoring_active:
            try:
                # Get high-value clients for frequent monitoring
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
                logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(3600)

    async def stop_monitoring(self):
        """Stop continuous health monitoring"""
        self.monitoring_active = False

    async def _get_high_value_clients(self) -> List[Dict[str, Any]]:
        """Get list of high-value clients for monitoring"""
        clients = await self._get_clients()
        # Filter for high-value clients
        return [c for c in clients if c.get("annual_revenue", 0) > 100000]

    async def _quick_health_check(self, client_id: str) -> Optional[float]:
        """Perform quick health check for monitoring"""
        # Simplified health check for frequent monitoring
        try:
            # Get recent usage data
            usage_data = await self.agents["usage_analyst"].analyze_usage(
                client_id, days=7
            )

            # Quick health calculation
            return self._calculate_usage_score(usage_data)

        except Exception as e:
            logger.error(f"Error in quick health check for {client_id}: {e}")
            return None

    async def _send_degradation_alert(
        self,
        client: Dict[str, Any],
        previous_score: ClientHealthScore,
        current_score: float,
        change: float
    ):
        """Send alert for significant health degradation"""
        alert = {
            "type": "health_degradation",
            "client_id": client["id"],
            "client_name": client["name"],
            "previous_score": previous_score.overall_score,
            "current_score": current_score,
            "change": change,
            "severity": "high" if change < -0.2 else "medium",
            "timestamp": datetime.now()
        }

        logger.warning(f"Health degradation alert: {alert}")
        self.alert_history.append(alert)

        # In real implementation, would send notifications