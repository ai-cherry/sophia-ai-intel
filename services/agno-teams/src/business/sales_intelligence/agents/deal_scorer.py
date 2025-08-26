"""
Deal Scorer Agent - Evaluates deal quality and potential
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from agno import Agent
from agno.tools import tool

logger = logging.getLogger(__name__)

class DealScorerAgent(Agent):
    """Evaluates and scores sales deals based on multiple factors"""

    def __init__(self, name: str, crm_config: Dict[str, Any]):
        super().__init__(
            name=name,
            role="""I am a Deal Scorer responsible for:
            - Evaluating deal quality and potential
            - Calculating deal scores based on multiple factors
            - Assessing deal risk and opportunity
            - Providing scoring insights and recommendations
            - Identifying high-value opportunities
            """,
            tools=self._create_tools()
        )

        self.crm_config = crm_config
        self.scoring_weights = self._default_scoring_weights()

    def _create_tools(self) -> List[Any]:
        """Create tools for deal scoring"""
        return [
            self.score_deal,
            self.batch_score_deals,
            self.analyze_deal_factors,
            self.calculate_risk_score,
            self.predict_deal_outcome
        ]

    def _default_scoring_weights(self) -> Dict[str, float]:
        """Default weights for scoring factors"""
        return {
            "deal_size": 0.25,
            "probability": 0.20,
            "competition": 0.15,
            "relationship": 0.15,
            "timeline": 0.10,
            "budget": 0.10,
            "authority": 0.05
        }

    @tool("score_deal")
    async def score_deal(self, deal: Dict[str, Any]) -> float:
        """Score a single deal based on multiple factors"""
        try:
            # Extract deal factors
            factors = await self._extract_deal_factors(deal)

            # Calculate weighted score
            score = self._calculate_weighted_score(factors)

            # Apply risk adjustment
            risk_adjustment = await self.calculate_risk_score(deal)
            final_score = score * (1 - risk_adjustment)

            logger.info(f"Scored deal {deal.get('id', 'unknown')}: {final_score:.2f}")

            return max(0.0, min(1.0, final_score))  # Clamp between 0 and 1

        except Exception as e:
            logger.error(f"Error scoring deal {deal.get('id', 'unknown')}: {e}")
            return 0.5  # Default neutral score

    @tool("batch_score_deals")
    async def batch_score_deals(self, deals: List[Dict[str, Any]]) -> Dict[str, float]:
        """Score multiple deals efficiently"""
        scores = {}

        # Score deals in parallel for better performance
        import asyncio
        scoring_tasks = [self.score_deal(deal) for deal in deals]
        results = await asyncio.gather(*scoring_tasks, return_exceptions=True)

        for i, result in enumerate(results):
            deal_id = deals[i].get('id', f'deal_{i}')
            if isinstance(result, Exception):
                logger.error(f"Error scoring deal {deal_id}: {result}")
                scores[deal_id] = 0.5
            else:
                scores[deal_id] = result

        return scores

    @tool("analyze_deal_factors")
    async def analyze_deal_factors(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual factors contributing to deal score"""
        factors = await self._extract_deal_factors(deal)

        analysis = {}
        for factor_name, factor_value in factors.items():
            analysis[factor_name] = {
                "value": factor_value,
                "weight": self.scoring_weights.get(factor_name, 0.1),
                "contribution": factor_value * self.scoring_weights.get(factor_name, 0.1),
                "assessment": self._assess_factor(factor_name, factor_value)
            }

        return analysis

    @tool("calculate_risk_score")
    async def calculate_risk_score(self, deal: Dict[str, Any]) -> float:
        """Calculate risk adjustment factor for deal score"""
        risk_factors = []

        # Timeline risk
        days_in_pipeline = self._calculate_days_in_pipeline(deal)
        if days_in_pipeline > 90:
            risk_factors.append(0.3)  # High risk for old deals
        elif days_in_pipeline > 60:
            risk_factors.append(0.2)  # Medium risk
        elif days_in_pipeline > 30:
            risk_factors.append(0.1)  # Low risk

        # Competition risk
        competition_level = deal.get('competition_level', 'unknown')
        if competition_level == 'high':
            risk_factors.append(0.2)
        elif competition_level == 'medium':
            risk_factors.append(0.1)

        # Budget risk
        budget_confirmed = deal.get('budget_confirmed', False)
        if not budget_confirmed:
            risk_factors.append(0.15)

        # Authority risk
        decision_maker = deal.get('decision_maker_involved', False)
        if not decision_maker:
            risk_factors.append(0.1)

        # Calculate overall risk
        if risk_factors:
            return min(0.5, sum(risk_factors) / len(risk_factors))
        return 0.0

    @tool("predict_deal_outcome")
    async def predict_deal_outcome(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        """Predict likely outcome of the deal"""
        score = await self.score_deal(deal)
        risk = await self.calculate_risk_score(deal)

        # Simple prediction model
        if score >= 0.8 and risk <= 0.1:
            prediction = "high_confidence_win"
            confidence = 0.85
        elif score >= 0.6 and risk <= 0.2:
            prediction = "likely_win"
            confidence = 0.7
        elif score >= 0.4 and risk <= 0.3:
            prediction = "possible_win"
            confidence = 0.5
        elif score >= 0.2:
            prediction = "long_shot"
            confidence = 0.3
        else:
            prediction = "unlikely_win"
            confidence = 0.1

        return {
            "prediction": prediction,
            "confidence": confidence,
            "score": score,
            "risk": risk,
            "recommendation": self._get_outcome_recommendation(prediction, score, risk)
        }

    async def _extract_deal_factors(self, deal: Dict[str, Any]) -> Dict[str, float]:
        """Extract scoring factors from deal data"""
        factors = {}

        # Deal size factor (normalized to 0-1 scale)
        deal_size = deal.get('amount', 0)
        factors['deal_size'] = self._normalize_deal_size(deal_size)

        # Probability factor
        probability = deal.get('probability', 0) / 100.0  # Convert percentage to decimal
        factors['probability'] = min(1.0, max(0.0, probability))

        # Competition factor
        competition = deal.get('competition_level', 'medium')
        factors['competition'] = self._assess_competition(competition)

        # Relationship factor
        relationship = deal.get('relationship_strength', 'medium')
        factors['relationship'] = self._assess_relationship(relationship)

        # Timeline factor
        timeline = deal.get('timeline_urgency', 'medium')
        factors['timeline'] = self._assess_timeline(timeline)

        # Budget factor
        budget = deal.get('budget_confirmed', False)
        factors['budget'] = 1.0 if budget else 0.3

        # Authority factor
        authority = deal.get('decision_maker_involved', False)
        factors['authority'] = 1.0 if authority else 0.4

        return factors

    def _calculate_weighted_score(self, factors: Dict[str, float]) -> float:
        """Calculate weighted score from factors"""
        score = 0.0
        total_weight = 0.0

        for factor_name, factor_value in factors.items():
            weight = self.scoring_weights.get(factor_name, 0.1)
            score += factor_value * weight
            total_weight += weight

        return score / total_weight if total_weight > 0 else 0.0

    def _normalize_deal_size(self, amount: float) -> float:
        """Normalize deal size to 0-1 scale"""
        if amount <= 0:
            return 0.0
        elif amount < 10000:  # Small deals
            return 0.3
        elif amount < 50000:  # Medium deals
            return 0.6
        elif amount < 200000:  # Large deals
            return 0.8
        else:  # Very large deals
            return 1.0

    def _assess_competition(self, level: str) -> float:
        """Assess competition level"""
        assessment_map = {
            'none': 1.0,
            'low': 0.8,
            'medium': 0.6,
            'high': 0.3,
            'extreme': 0.1
        }
        return assessment_map.get(level.lower(), 0.6)

    def _assess_relationship(self, strength: str) -> float:
        """Assess relationship strength"""
        assessment_map = {
            'excellent': 1.0,
            'strong': 0.8,
            'good': 0.7,
            'medium': 0.5,
            'weak': 0.3,
            'poor': 0.1
        }
        return assessment_map.get(strength.lower(), 0.5)

    def _assess_timeline(self, urgency: str) -> float:
        """Assess timeline urgency"""
        assessment_map = {
            'immediate': 1.0,
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4,
            'flexible': 0.2
        }
        return assessment_map.get(urgency.lower(), 0.6)

    def _assess_factor(self, factor_name: str, value: float) -> str:
        """Provide qualitative assessment of factor"""
        if factor_name == 'deal_size':
            if value >= 0.8:
                return "Very large deal - high potential impact"
            elif value >= 0.6:
                return "Large deal - significant opportunity"
            elif value >= 0.4:
                return "Medium deal - solid opportunity"
            else:
                return "Small deal - quick win potential"
        elif factor_name == 'probability':
            if value >= 0.8:
                return "High probability - strong likelihood of closing"
            elif value >= 0.6:
                return "Good probability - favorable position"
            elif value >= 0.4:
                return "Moderate probability - needs work"
            else:
                return "Low probability - significant risk"
        elif factor_name == 'competition':
            if value >= 0.8:
                return "Low competition - strong position"
            elif value >= 0.6:
                return "Moderate competition - manageable"
            elif value >= 0.4:
                return "High competition - challenging"
            else:
                return "Extreme competition - very challenging"
        else:
            if value >= 0.8:
                return "Strong positive factor"
            elif value >= 0.6:
                return "Positive factor"
            elif value >= 0.4:
                return "Neutral factor"
            else:
                return "Negative factor"

    def _calculate_days_in_pipeline(self, deal: Dict[str, Any]) -> int:
        """Calculate days deal has been in pipeline"""
        created_date = deal.get('created_date')
        if not created_date:
            return 0

        try:
            created = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
            return (datetime.now() - created).days
        except:
            return 30  # Default assumption

    def _get_outcome_recommendation(
        self,
        prediction: str,
        score: float,
        risk: float
    ) -> str:
        """Get recommendation based on prediction"""
        if prediction == "high_confidence_win":
            return "Focus on closing activities and relationship building"
        elif prediction == "likely_win":
            return "Continue current strategy, monitor for changes"
        elif prediction == "possible_win":
            return "Address risk factors and strengthen position"
        elif prediction == "long_shot":
            return "Consider if resources are better allocated elsewhere"
        else:
            return "Re-evaluate deal viability and consider disqualification"

    async def score_deals_by_segment(
        self,
        deals: List[Dict[str, Any]],
        segment_field: str
    ) -> Dict[str, Dict[str, Any]]:
        """Score deals grouped by segment"""
        segments = {}

        for deal in deals:
            segment = deal.get(segment_field, 'unknown')
            if segment not in segments:
                segments[segment] = []

            segments[segment].append(deal)

        # Score each segment
        segment_scores = {}
        for segment, segment_deals in segments.items():
            scores = await self.batch_score_deals(segment_deals)
            avg_score = sum(scores.values()) / len(scores) if scores else 0

            segment_scores[segment] = {
                "deals": segment_deals,
                "scores": scores,
                "average_score": avg_score,
                "total_value": sum(d.get('amount', 0) for d in segment_deals),
                "deal_count": len(segment_deals)
            }

        return segment_scores

    async def identify_best_bets(self, deals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify the best deals to focus on"""
        scored_deals = []

        for deal in deals:
            score = await self.score_deal(deal)
            risk = await self.calculate_risk_score(deal)

            scored_deals.append({
                **deal,
                "score": score,
                "risk": risk,
                "score_risk_ratio": score / (risk + 0.1)  # Avoid division by zero
            })

        # Sort by score-risk ratio (higher is better)
        scored_deals.sort(key=lambda x: x["score_risk_ratio"], reverse=True)

        return scored_deals[:10]  # Top 10 best bets

    async def analyze_score_distribution(
        self,
        deals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze the distribution of deal scores"""
        if not deals:
            return {"error": "No deals to analyze"}

        scores = []
        for deal in deals:
            score = await self.score_deal(deal)
            scores.append(score)

        import statistics

        return {
            "count": len(scores),
            "average": statistics.mean(scores),
            "median": statistics.median(scores),
            "min": min(scores),
            "max": max(scores),
            "distribution": {
                "excellent": len([s for s in scores if s >= 0.8]),
                "good": len([s for s in scores if 0.6 <= s < 0.8]),
                "fair": len([s for s in scores if 0.4 <= s < 0.6]),
                "poor": len([s for s in scores if s < 0.4])
            }
        }