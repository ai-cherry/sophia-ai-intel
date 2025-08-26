"""
Competitor Analyst Agent - Analyzes competitive landscape and threats
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from agno import Agent
from agno.tools import tool

logger = logging.getLogger(__name__)

class CompetitorAnalystAgent(Agent):
    """Analyzes competitive landscape and provides strategic insights"""

    def __init__(self, name: str, crm_config: Dict[str, Any]):
        super().__init__(
            name=name,
            role="""I am a Competitor Analyst responsible for:
            - Analyzing competitive threats and opportunities
            - Assessing competitive advantages and disadvantages
            - Monitoring competitor activities and strategies
            - Providing strategic recommendations for competitive situations
            - Identifying market positioning opportunities
            """,
            tools=self._create_tools()
        )

        self.crm_config = crm_config
        self.known_competitors = self._load_known_competitors()

    def _create_tools(self) -> List[Any]:
        """Create tools for competitor analysis"""
        return [
            self.analyze_competitive_threats,
            self.assess_competitive_advantages,
            self.monitor_competitor_activity,
            self.analyze_market_positioning,
            self.generate_competitive_strategy
        ]

    def _load_known_competitors(self) -> List[str]:
        """Load list of known competitors"""
        return [
            "CompetitorA", "CompetitorB", "CompetitorC",
            "StartupX", "EnterpriseY", "CloudZ"
        ]

    @tool("analyze_competitive_threats")
    async def analyze_competitive_threats(
        self,
        deals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze competitive threats in the deal pipeline"""
        threats = []

        for deal in deals:
            deal_threats = await self._analyze_deal_threats(deal)
            if deal_threats:
                threats.extend(deal_threats)

        # Sort by severity
        threats.sort(key=lambda x: self._get_threat_severity(x), reverse=True)

        return threats

    @tool("assess_competitive_advantages")
    async def assess_competitive_advantages(
        self,
        win_probabilities: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Assess competitive advantages based on win probabilities"""
        advantages = []

        # Analyze patterns in win probabilities
        high_probability_deals = [
            deal_id for deal_id, prob in win_probabilities.items()
            if prob > 0.7
        ]

        low_probability_deals = [
            deal_id for deal_id, prob in win_probabilities.items()
            if prob < 0.3
        ]

        if len(high_probability_deals) > len(low_probability_deals):
            advantages.append({
                "type": "strong_positioning",
                "description": "Strong competitive positioning with high win rates",
                "strength": "high",
                "evidence": f"{len(high_probability_deals)} high-probability deals vs {len(low_probability_deals)} low-probability"
            })

        # Analyze deal size patterns
        large_deal_performance = await self._analyze_large_deal_performance(win_probabilities)
        if large_deal_performance["advantage"]:
            advantages.append(large_deal_performance)

        return advantages

    @tool("monitor_competitor_activity")
    async def monitor_competitor_activity(
        self,
        time_period: str = "last_30_days"
    ) -> Dict[str, Any]:
        """Monitor competitor activities and market moves"""
        # This would integrate with external data sources
        # For now, return structured analysis

        activities = {
            "competitor_moves": [
                {
                    "competitor": "CompetitorA",
                    "activity": "price_reduction",
                    "impact": "medium",
                    "description": "Reduced pricing by 15% for enterprise customers"
                },
                {
                    "competitor": "StartupX",
                    "activity": "feature_launch",
                    "impact": "high",
                    "description": "Launched AI-powered analytics feature"
                }
            ],
            "market_trends": [
                {
                    "trend": "ai_integration",
                    "direction": "increasing",
                    "impact": "high",
                    "description": "AI integration becoming standard requirement"
                }
            ],
            "recommendations": [
                "Monitor CompetitorA pricing strategy",
                "Accelerate feature development to match StartupX",
                "Highlight AI capabilities in messaging"
            ]
        }

        return activities

    @tool("analyze_market_positioning")
    async def analyze_market_positioning(
        self,
        deals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze market positioning based on deal characteristics"""
        positioning = {
            "market_segments": {},
            "competitive_strengths": [],
            "vulnerabilities": [],
            "opportunities": []
        }

        # Analyze by deal size
        small_deals = [d for d in deals if d.get("amount", 0) < 50000]
        medium_deals = [d for d in deals if 50000 <= d.get("amount", 0) < 200000]
        large_deals = [d for d in deals if d.get("amount", 0) >= 200000]

        positioning["market_segments"] = {
            "small_business": {
                "deal_count": len(small_deals),
                "avg_win_rate": self._calculate_segment_win_rate(small_deals),
                "competitive_advantage": "strong"
            },
            "mid_market": {
                "deal_count": len(medium_deals),
                "avg_win_rate": self._calculate_segment_win_rate(medium_deals),
                "competitive_advantage": "moderate"
            },
            "enterprise": {
                "deal_count": len(large_deals),
                "avg_win_rate": self._calculate_segment_win_rate(large_deals),
                "competitive_advantage": "weak"
            }
        }

        # Identify strengths and weaknesses
        for segment, data in positioning["market_segments"].items():
            if data["competitive_advantage"] == "strong":
                positioning["competitive_strengths"].append({
                    "segment": segment,
                    "description": f"Strong position in {segment} market",
                    "win_rate": data["avg_win_rate"]
                })
            elif data["competitive_advantage"] == "weak":
                positioning["vulnerabilities"].append({
                    "segment": segment,
                    "description": f"Weak position in {segment} market",
                    "win_rate": data["avg_win_rate"]
                })

        return positioning

    @tool("generate_competitive_strategy")
    async def generate_competitive_strategy(
        self,
        threats: List[Dict[str, Any]],
        advantages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate competitive strategy recommendations"""
        strategy = {
            "immediate_actions": [],
            "strategic_initiatives": [],
            "defensive_measures": [],
            "offensive_opportunities": []
        }

        # Analyze threats and generate responses
        for threat in threats:
            if threat.get("severity") == "high":
                strategy["immediate_actions"].append({
                    "threat": threat.get("description", "Unknown threat"),
                    "action": self._generate_threat_response(threat),
                    "priority": "high"
                })

        # Leverage advantages
        for advantage in advantages:
            if advantage.get("strength") == "high":
                strategy["offensive_opportunities"].append({
                    "advantage": advantage.get("description", "Unknown advantage"),
                    "opportunity": self._generate_advantage_leverage(advantage),
                    "priority": "medium"
                })

        # Strategic initiatives
        strategy["strategic_initiatives"] = [
            {
                "initiative": "market_intelligence_system",
                "description": "Implement automated competitor monitoring",
                "timeframe": "3 months",
                "priority": "high"
            },
            {
                "initiative": "value_proposition_refinement",
                "description": "Refine messaging based on competitive analysis",
                "timeframe": "2 months",
                "priority": "high"
            }
        ]

        return strategy

    async def _analyze_deal_threats(self, deal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze competitive threats for a specific deal"""
        threats = []

        # Check for known competitors
        competitors = deal.get("competitors", [])
        if not competitors:
            # Infer competitors based on deal characteristics
            competitors = self._infer_competitors(deal)

        for competitor in competitors:
            threat_level = await self._assess_competitor_threat(
                competitor, deal
            )

            if threat_level["severity"] != "low":
                threats.append({
                    "deal_id": deal.get("id"),
                    "competitor": competitor,
                    "severity": threat_level["severity"],
                    "description": threat_level["description"],
                    "factors": threat_level["factors"],
                    "recommendation": threat_level["recommendation"]
                })

        return threats

    def _infer_competitors(self, deal: Dict[str, Any]) -> List[str]:
        """Infer likely competitors based on deal characteristics"""
        competitors = []

        deal_size = deal.get("amount", 0)
        industry = deal.get("industry", "unknown")

        # Size-based competitor inference
        if deal_size > 500000:
            competitors.extend(["EnterpriseY", "CloudZ"])
        elif deal_size > 100000:
            competitors.extend(["CompetitorA", "CompetitorB"])
        else:
            competitors.extend(["StartupX", "CompetitorC"])

        return list(set(competitors))  # Remove duplicates

    async def _assess_competitor_threat(
        self,
        competitor: str,
        deal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess threat level from a specific competitor"""
        threat_factors = []

        # Factor 1: Competitor strength in this segment
        segment_strength = self._get_competitor_segment_strength(
            competitor, deal
        )
        threat_factors.append(segment_strength)

        # Factor 2: Recent competitor activity
        recent_activity = await self._check_recent_competitor_activity(
            competitor
        )
        threat_factors.append(recent_activity)

        # Factor 3: Deal-specific factors
        deal_factors = self._assess_deal_specific_threats(
            competitor, deal
        )
        threat_factors.append(deal_factors)

        # Calculate overall threat level
        threat_score = sum(f["score"] for f in threat_factors) / len(threat_factors)

        if threat_score >= 0.7:
            severity = "high"
            description = f"High threat from {competitor}"
        elif threat_score >= 0.4:
            severity = "medium"
            description = f"Moderate threat from {competitor}"
        else:
            severity = "low"
            description = f"Low threat from {competitor}"

        return {
            "severity": severity,
            "description": description,
            "factors": threat_factors,
            "recommendation": self._generate_competitor_recommendation(
                competitor, severity
            )
        }

    def _get_competitor_segment_strength(
        self,
        competitor: str,
        deal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get competitor strength in the relevant market segment"""
        # Mock competitor strength data
        competitor_strengths = {
            "CompetitorA": {
                "mid_market": 0.8,
                "enterprise": 0.6,
                "small_business": 0.4
            },
            "EnterpriseY": {
                "enterprise": 0.9,
                "mid_market": 0.5,
                "small_business": 0.2
            },
            "StartupX": {
                "small_business": 0.7,
                "mid_market": 0.4,
                "enterprise": 0.2
            }
        }

        deal_size = deal.get("amount", 0)
        if deal_size >= 200000:
            segment = "enterprise"
        elif deal_size >= 50000:
            segment = "mid_market"
        else:
            segment = "small_business"

        strength = competitor_strengths.get(competitor, {}).get(segment, 0.5)

        return {
            "factor": "segment_strength",
            "score": strength,
            "description": f"{competitor} has {strength:.1%} strength in {segment}"
        }

    async def _check_recent_competitor_activity(
        self,
        competitor: str
    ) -> Dict[str, Any]:
        """Check recent competitor activity"""
        # Mock recent activity data
        recent_activities = {
            "CompetitorA": {
                "activity_level": 0.8,
                "description": "Recent pricing changes and feature updates"
            },
            "StartupX": {
                "activity_level": 0.9,
                "description": "Major product launch and marketing campaign"
            },
            "EnterpriseY": {
                "activity_level": 0.6,
                "description": "Steady market presence with minor updates"
            }
        }

        activity = recent_activities.get(competitor, {"activity_level": 0.5})

        return {
            "factor": "recent_activity",
            "score": activity["activity_level"],
            "description": activity.get("description", "Normal activity level")
        }

    def _assess_deal_specific_threats(
        self,
        competitor: str,
        deal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess deal-specific competitive threats"""
        threat_score = 0.0
        factors = []

        # Check if competitor is already engaged
        if competitor in deal.get("engaged_competitors", []):
            threat_score += 0.8
            factors.append("competitor_already_engaged")

        # Check if competitor has better pricing
        if deal.get("competitor_pricing_advantage", False):
            threat_score += 0.6
            factors.append("pricing_advantage")

        # Check if competitor has better features
        if deal.get("competitor_feature_advantage", False):
            threat_score += 0.5
            factors.append("feature_advantage")

        # Check relationship strength
        competitor_relationship = deal.get(f"{competitor}_relationship", "unknown")
        if competitor_relationship in ["strong", "excellent"]:
            threat_score += 0.7
            factors.append("strong_relationship")

        return {
            "factor": "deal_specific",
            "score": min(1.0, threat_score),
            "description": f"Deal-specific factors: {', '.join(factors) if factors else 'none'}"
        }

    def _get_threat_severity(self, threat: Dict[str, Any]) -> int:
        """Get numerical severity score for threat sorting"""
        severity_map = {"high": 3, "medium": 2, "low": 1}
        return severity_map.get(threat.get("severity", "low"), 1)

    def _generate_threat_response(self, threat: Dict[str, Any]) -> str:
        """Generate response recommendation for a threat"""
        competitor = threat.get("competitor", "unknown")

        if "pricing" in threat.get("description", "").lower():
            return f"Develop pricing strategy to counter {competitor}"
        elif "feature" in threat.get("description", "").lower():
            return f"Highlight unique features against {competitor}"
        elif "relationship" in threat.get("description", "").lower():
            return f"Strengthen relationship and provide additional value"
        else:
            return f"Develop comprehensive strategy against {competitor}"

    def _generate_advantage_leverage(self, advantage: Dict[str, Any]) -> str:
        """Generate recommendation to leverage an advantage"""
        if "positioning" in advantage.get("description", "").lower():
            return "Use strong positioning to expand market share"
        elif "feature" in advantage.get("description", "").lower():
            return "Highlight feature advantages in marketing"
        else:
            return "Leverage advantage to win competitive deals"

    def _generate_competitor_recommendation(
        self,
        competitor: str,
        severity: str
    ) -> str:
        """Generate recommendation for dealing with a competitor"""
        if severity == "high":
            return f"Develop comprehensive strategy against {competitor}"
        elif severity == "medium":
            return f"Monitor {competitor} closely and strengthen position"
        else:
            return f"Keep standard monitoring on {competitor}"

    def _calculate_segment_win_rate(self, deals: List[Dict[str, Any]]) -> float:
        """Calculate win rate for a segment"""
        if not deals:
            return 0.0

        won_deals = [d for d in deals if d.get("stage") == "closed_won"]
        return len(won_deals) / len(deals)

    async def _analyze_large_deal_performance(
        self,
        win_probabilities: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze performance in large deals"""
        # Mock analysis - in real implementation would analyze actual deal data
        return {
            "type": "large_deal_performance",
            "description": "Strong performance in large enterprise deals",
            "strength": "high",
            "advantage": True,
            "evidence": "Higher win rates in deals over $200k"
        }