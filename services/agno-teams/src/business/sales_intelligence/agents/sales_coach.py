"""
Sales Coach Agent - Provides coaching insights from sales interactions
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from agno import Agent
from agno.tools import tool

logger = logging.getLogger(__name__)

class SalesCoachAgent(Agent):
    """Provides coaching insights and recommendations based on sales interactions"""

    def __init__(self, name: str, gong_config: Dict[str, Any]):
        super().__init__(
            name=name,
            role="""I am a Sales Coach responsible for:
            - Analyzing sales conversations and interactions
            - Identifying coaching opportunities for sales reps
            - Providing personalized coaching recommendations
            - Tracking performance improvement over time
            - Suggesting best practices and techniques
            """,
            tools=self._create_tools()
        )

        self.gong_config = gong_config
        self.coaching_history = []

    def _create_tools(self) -> List[Any]:
        """Create tools for sales coaching"""
        return [
            self.identify_coaching_opportunities,
            self.analyze_conversation_quality,
            self.generate_coaching_recommendations,
            self.track_performance_improvement,
            self.suggest_best_practices
        ]

    @tool("identify_coaching_opportunities")
    async def identify_coaching_opportunities(
        self,
        time_period: str = "last_30_days"
    ) -> List[Dict[str, Any]]:
        """Identify coaching opportunities from recent sales interactions"""
        opportunities = []

        try:
            # Fetch recent sales conversations
            conversations = await self._fetch_recent_conversations(time_period)

            for conversation in conversations:
                analysis = await self._analyze_conversation(conversation)

                if analysis["needs_coaching"]:
                    opportunity = {
                        "rep_name": conversation.get("rep_name", "Unknown"),
                        "conversation_id": conversation.get("id"),
                        "priority": analysis["priority"],
                        "issue_type": analysis["issue_type"],
                        "description": analysis["description"],
                        "specific_feedback": analysis["feedback"],
                        "recommended_action": analysis["recommendation"],
                        "expected_impact": analysis["impact"],
                        "timestamp": conversation.get("timestamp")
                    }
                    opportunities.append(opportunity)

            # Sort by priority
            opportunities.sort(key=lambda x: self._get_priority_score(x), reverse=True)

        except Exception as e:
            logger.error(f"Error identifying coaching opportunities: {e}")

        return opportunities

    @tool("analyze_conversation_quality")
    async def analyze_conversation_quality(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Analyze the quality of a specific sales conversation"""
        try:
            # Fetch conversation details
            conversation = await self._fetch_conversation_details(conversation_id)

            if not conversation:
                return {"error": "Conversation not found"}

            # Analyze different aspects
            analysis = {
                "overall_score": 0,
                "aspects": {},
                "strengths": [],
                "improvement_areas": [],
                "recommendations": []
            }

            # Analyze opening
            opening_analysis = self._analyze_conversation_opening(conversation)
            analysis["aspects"]["opening"] = opening_analysis

            # Analyze discovery
            discovery_analysis = self._analyze_discovery_phase(conversation)
            analysis["aspects"]["discovery"] = discovery_analysis

            # Analyze objection handling
            objection_analysis = self._analyze_objection_handling(conversation)
            analysis["aspects"]["objections"] = objection_analysis

            # Analyze closing
            closing_analysis = self._analyze_closing_technique(conversation)
            analysis["aspects"]["closing"] = closing_analysis

            # Calculate overall score
            aspect_scores = [aspect["score"] for aspect in analysis["aspects"].values()]
            analysis["overall_score"] = sum(aspect_scores) / len(aspect_scores)

            # Generate recommendations
            analysis["recommendations"] = self._generate_conversation_recommendations(
                analysis["aspects"]
            )

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing conversation {conversation_id}: {e}")
            return {"error": str(e)}

    @tool("generate_coaching_recommendations")
    async def generate_coaching_recommendations(
        self,
        rep_name: str,
        time_period: str = "last_30_days"
    ) -> Dict[str, Any]:
        """Generate personalized coaching recommendations for a sales rep"""
        try:
            # Get rep's recent performance data
            performance_data = await self._get_rep_performance_data(rep_name, time_period)

            # Analyze patterns and trends
            patterns = self._analyze_performance_patterns(performance_data)

            # Generate recommendations
            recommendations = {
                "rep_name": rep_name,
                "time_period": time_period,
                "overall_assessment": patterns["overall_assessment"],
                "key_strengths": patterns["strengths"],
                "improvement_areas": patterns["weaknesses"],
                "specific_recommendations": [],
                "development_plan": [],
                "expected_outcomes": []
            }

            # Generate specific recommendations based on patterns
            if patterns["weaknesses"]:
                recommendations["specific_recommendations"] = self._generate_specific_recommendations(
                    patterns["weaknesses"]
                )

            # Create development plan
            recommendations["development_plan"] = self._create_development_plan(
                patterns["weaknesses"]
            )

            # Define expected outcomes
            recommendations["expected_outcomes"] = self._define_expected_outcomes(
                recommendations["specific_recommendations"]
            )

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations for {rep_name}: {e}")
            return {"error": str(e)}

    @tool("track_performance_improvement")
    async def track_performance_improvement(
        self,
        rep_name: str,
        metric: str = "win_rate",
        time_period: str = "last_90_days"
    ) -> Dict[str, Any]:
        """Track performance improvement over time"""
        try:
            # Get historical performance data
            historical_data = await self._get_historical_performance(
                rep_name, metric, time_period
            )

            if not historical_data:
                return {"error": "No historical data available"}

            # Analyze improvement trends
            trend_analysis = self._analyze_improvement_trends(historical_data)

            # Calculate improvement metrics
            improvement_metrics = self._calculate_improvement_metrics(historical_data)

            return {
                "rep_name": rep_name,
                "metric": metric,
                "time_period": time_period,
                "current_performance": historical_data[-1] if historical_data else None,
                "baseline_performance": historical_data[0] if historical_data else None,
                "trend": trend_analysis["trend"],
                "improvement_rate": improvement_metrics["improvement_rate"],
                "confidence_level": trend_analysis["confidence"],
                "key_insights": trend_analysis["insights"],
                "recommendations": self._generate_improvement_recommendations(trend_analysis)
            }

        except Exception as e:
            logger.error(f"Error tracking improvement for {rep_name}: {e}")
            return {"error": str(e)}

    @tool("suggest_best_practices")
    async def suggest_best_practices(
        self,
        scenario: str,
        industry: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Suggest best practices for specific sales scenarios"""
        best_practices = {
            "handling_objections": [
                {
                    "practice": "Feel-Felt-Found technique",
                    "description": "Acknowledge the prospect's concern, share that others felt the same, then explain what was found",
                    "when_to_use": "When prospect raises common objections",
                    "expected_impact": "Increases trust and addresses concerns effectively"
                },
                {
                    "practice": "Question the objection",
                    "description": "Ask probing questions to understand the real concern behind the objection",
                    "when_to_use": "When objection seems surface-level",
                    "expected_impact": "Uncovers root issues and provides better solutions"
                }
            ],
            "discovery_questions": [
                {
                    "practice": "SPIN questioning",
                    "description": "Use Situation, Problem, Implication, Need-payoff questions",
                    "when_to_use": "During discovery phase",
                    "expected_impact": "Better understanding of customer needs"
                }
            ],
            "closing_techniques": [
                {
                    "practice": "Assumptive close",
                    "description": "Talk about next steps as if the deal is already decided",
                    "when_to_use": "When strong buying signals are present",
                    "expected_impact": "Reduces decision friction"
                }
            ]
        }

        if scenario in best_practices:
            practices = best_practices[scenario]
        else:
            # Return general best practices
            practices = [
                practice for sublist in best_practices.values()
                for practice in sublist
            ][:5]  # Return top 5

        # Filter by industry if specified
        if industry:
            practices = [p for p in practices if self._is_relevant_to_industry(p, industry)]

        return practices

    async def _fetch_recent_conversations(self, time_period: str) -> List[Dict[str, Any]]:
        """Fetch recent sales conversations from Gong or similar platform"""
        # Mock data - in real implementation would call Gong API
        return [
            {
                "id": "conv_001",
                "rep_name": "John Doe",
                "timestamp": "2024-01-15T10:00:00Z",
                "duration": 1800,  # 30 minutes
                "prospect": "Acme Corp",
                "stage": "discovery",
                "transcript": "Sample conversation transcript...",
                "outcome": "follow_up"
            },
            {
                "id": "conv_002",
                "rep_name": "Jane Smith",
                "timestamp": "2024-01-16T14:30:00Z",
                "duration": 2400,  # 40 minutes
                "prospect": "Tech Startup",
                "stage": "demo",
                "transcript": "Another sample transcript...",
                "outcome": "proposal"
            }
        ]

    async def _analyze_conversation(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single conversation for coaching opportunities"""
        analysis = {
            "needs_coaching": False,
            "priority": "low",
            "issue_type": None,
            "description": "",
            "feedback": "",
            "recommendation": "",
            "impact": "low"
        }

        # Analyze conversation duration
        duration_minutes = conversation.get("duration", 0) / 60
        if duration_minutes < 15:
            analysis.update({
                "needs_coaching": True,
                "priority": "medium",
                "issue_type": "call_too_short",
                "description": "Conversation ended too quickly",
                "feedback": "Calls should typically last 20-30 minutes for effective discovery",
                "recommendation": "Prepare better questions and engage more deeply",
                "impact": "medium"
            })

        # Analyze outcome
        outcome = conversation.get("outcome", "")
        if outcome == "no_answer" and duration_minutes > 5:
            analysis.update({
                "needs_coaching": True,
                "priority": "high",
                "issue_type": "poor_qualification",
                "description": "Poor prospect qualification",
                "feedback": "Should qualify prospects before investing significant time",
                "recommendation": "Use BANT or similar qualification framework",
                "impact": "high"
            })

        return analysis

    def _get_priority_score(self, opportunity: Dict[str, Any]) -> int:
        """Get numerical priority score for sorting"""
        priority_map = {"high": 3, "medium": 2, "low": 1}
        return priority_map.get(opportunity.get("priority", "low"), 1)

    async def _fetch_conversation_details(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed conversation data"""
        # Mock implementation
        return {
            "id": conversation_id,
            "transcript": "Full conversation transcript...",
            "duration": 1800,
            "participants": ["rep", "prospect"],
            "topics": ["pricing", "features", "timeline"]
        }

    def _analyze_conversation_opening(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation opening effectiveness"""
        transcript = conversation.get("transcript", "")

        # Simple analysis based on keywords
        opening_indicators = ["hello", "thank you", "how are you", "pleasure to speak"]
        opening_score = sum(1 for indicator in opening_indicators
                          if indicator.lower() in transcript.lower()) / len(opening_indicators)

        return {
            "score": opening_score,
            "strengths": ["Good greeting"] if opening_score > 0.5 else [],
            "improvements": ["Better opening needed"] if opening_score < 0.5 else []
        }

    def _analyze_discovery_phase(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze discovery phase effectiveness"""
        transcript = conversation.get("transcript", "")

        # Look for discovery questions
        discovery_questions = ["what are you", "how do you", "what challenges", "current solution"]
        discovery_score = sum(1 for question in discovery_questions
                            if question.lower() in transcript.lower()) / len(discovery_questions)

        return {
            "score": discovery_score,
            "questions_asked": discovery_score * len(discovery_questions),
            "depth": "good" if discovery_score > 0.6 else "needs_improvement"
        }

    def _analyze_objection_handling(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze objection handling effectiveness"""
        transcript = conversation.get("transcript", "")

        # Look for objection handling patterns
        objection_indicators = ["understand", "feel that way", "what if", "solution"]
        objection_score = sum(1 for indicator in objection_indicators
                            if indicator.lower() in transcript.lower()) / len(objection_indicators)

        return {
            "score": objection_score,
            "objections_handled": objection_score > 0.5,
            "technique_used": "feel_felt_found" if "feel that way" in transcript.lower() else "direct_response"
        }

    def _analyze_closing_technique(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze closing technique effectiveness"""
        transcript = conversation.get("transcript", "")

        # Look for closing indicators
        closing_indicators = ["next steps", "when can we", "shall we", "proposal"]
        closing_score = sum(1 for indicator in closing_indicators
                          if indicator.lower() in transcript.lower()) / len(closing_indicators)

        return {
            "score": closing_score,
            "closing_attempted": closing_score > 0.3,
            "technique": "assumptive" if "next steps" in transcript.lower() else "direct"
        }

    def _generate_conversation_recommendations(self, aspects: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on conversation analysis"""
        recommendations = []

        for aspect_name, analysis in aspects.items():
            if analysis["score"] < 0.6:
                if aspect_name == "opening":
                    recommendations.append("Start with a stronger, more personalized opening")
                elif aspect_name == "discovery":
                    recommendations.append("Ask more probing discovery questions")
                elif aspect_name == "objections":
                    recommendations.append("Use structured objection handling techniques")
                elif aspect_name == "closing":
                    recommendations.append("Practice assumptive closing techniques")

        return recommendations

    async def _get_rep_performance_data(self, rep_name: str, time_period: str) -> Dict[str, Any]:
        """Get performance data for a sales rep"""
        # Mock implementation
        return {
            "win_rate": 0.35,
            "avg_deal_size": 75000,
            "calls_per_day": 15,
            "conversion_rate": 0.25,
            "recent_trends": "improving"
        }

    def _analyze_performance_patterns(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance patterns and identify strengths/weaknesses"""
        patterns = {
            "overall_assessment": "needs_improvement",
            "strengths": [],
            "weaknesses": []
        }

        # Analyze win rate
        win_rate = performance_data.get("win_rate", 0)
        if win_rate > 0.4:
            patterns["strengths"].append("strong_closing")
        elif win_rate < 0.25:
            patterns["weaknesses"].append("closing_technique")

        # Analyze activity
        calls_per_day = performance_data.get("calls_per_day", 0)
        if calls_per_day > 20:
            patterns["strengths"].append("high_activity")
        elif calls_per_day < 10:
            patterns["weaknesses"].append("low_activity")

        return patterns

    def _generate_specific_recommendations(self, weaknesses: List[str]) -> List[str]:
        """Generate specific recommendations based on weaknesses"""
        recommendations = []

        for weakness in weaknesses:
            if weakness == "closing_technique":
                recommendations.extend([
                    "Practice assumptive closing techniques",
                    "Role-play common closing scenarios",
                    "Study successful deal closings"
                ])
            elif weakness == "low_activity":
                recommendations.extend([
                    "Increase daily call volume",
                    "Improve time management",
                    "Use automated outreach tools"
                ])

        return recommendations

    def _create_development_plan(self, weaknesses: List[str]) -> List[Dict[str, Any]]:
        """Create a development plan based on weaknesses"""
        plan = []

        for weakness in weaknesses:
            if weakness == "closing_technique":
                plan.append({
                    "focus_area": "Closing Skills",
                    "activities": ["Weekly role-playing", "Study top performers"],
                    "timeframe": "4 weeks",
                    "milestones": ["Complete 5 role-plays", "Close 3 deals using new techniques"]
                })

        return plan

    def _define_expected_outcomes(self, recommendations: List[str]) -> List[str]:
        """Define expected outcomes from recommendations"""
        outcomes = []

        if any("closing" in rec.lower() for rec in recommendations):
            outcomes.append("15-20% improvement in win rate within 30 days")

        if any("activity" in rec.lower() for rec in recommendations):
            outcomes.append("Increase in qualified conversations by 25%")

        return outcomes

    async def _get_historical_performance(
        self,
        rep_name: str,
        metric: str,
        time_period: str
    ) -> List[float]:
        """Get historical performance data"""
        # Mock historical data
        return [0.25, 0.28, 0.32, 0.35, 0.38]  # Improving trend

    def _analyze_improvement_trends(self, historical_data: List[float]) -> Dict[str, Any]:
        """Analyze improvement trends in performance data"""
        if len(historical_data) < 2:
            return {"trend": "insufficient_data", "confidence": 0, "insights": []}

        # Calculate trend
        recent_avg = sum(historical_data[-3:]) / 3
        earlier_avg = sum(historical_data[:3]) / 3

        if recent_avg > earlier_avg * 1.1:
            trend = "improving"
            confidence = 0.8
        elif recent_avg < earlier_avg * 0.9:
            trend = "declining"
            confidence = 0.8
        else:
            trend = "stable"
            confidence = 0.6

        return {
            "trend": trend,
            "confidence": confidence,
            "insights": [f"Performance has {trend} over the period"]
        }

    def _calculate_improvement_metrics(self, historical_data: List[float]) -> Dict[str, Any]:
        """Calculate improvement metrics"""
        if len(historical_data) < 2:
            return {"improvement_rate": 0}

        first_value = historical_data[0]
        last_value = historical_data[-1]

        if first_value == 0:
            improvement_rate = 0
        else:
            improvement_rate = (last_value - first_value) / first_value

        return {"improvement_rate": improvement_rate}

    def _generate_improvement_recommendations(self, trend_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on improvement trends"""
        if trend_analysis["trend"] == "improving":
            return ["Continue current approach", "Share best practices with team"]
        elif trend_analysis["trend"] == "declining":
            return ["Review recent changes", "Consider additional coaching", "Reassess strategy"]
        else:
            return ["Focus on consistency", "Identify areas for breakthrough improvement"]

    def _is_relevant_to_industry(self, practice: Dict[str, Any], industry: str) -> bool:
        """Check if a best practice is relevant to a specific industry"""
        # Simple relevance check - in real implementation would be more sophisticated
        industry_keywords = {
            "technology": ["features", "innovation", "scalability"],
            "healthcare": ["compliance", "security", "patient_care"],
            "finance": ["security", "compliance", "risk_management"]
        }

        practice_text = practice.get("description", "").lower()
        relevant_keywords = industry_keywords.get(industry.lower(), [])

        return any(keyword in practice_text for keyword in relevant_keywords)