"""
Usage Analyst Agent - Analyzes client product usage patterns and engagement
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from agno import Agent
from agno.tools import tool

logger = logging.getLogger(__name__)

class UsageAnalystAgent(Agent):
    """Analyzes client product usage patterns and engagement metrics"""

    def __init__(self, name: str, integrations: Dict[str, str]):
        super().__init__(
            name=name,
            role="""I am a Usage Analyst responsible for:
            - Analyzing client product usage patterns
            - Tracking feature adoption and engagement metrics
            - Identifying usage trends and anomalies
            - Providing insights on product utilization
            - Recommending usage optimization strategies
            """,
            tools=self._create_tools()
        )

        self.integrations = integrations
        self.usage_metrics_url = integrations.get("usage_metrics", "http://mcp-usage:8080")

    def _create_tools(self) -> List[Any]:
        """Create tools for usage analysis"""
        return [
            self.analyze_usage,
            self.track_feature_adoption,
            self.identify_usage_patterns,
            self.detect_usage_anomalies,
            self.generate_usage_insights
        ]

    @tool("analyze_usage")
    async def analyze_usage(
        self,
        client_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Analyze comprehensive usage data for a client"""
        try:
            # Fetch usage data from multiple sources
            usage_data = await self._fetch_usage_data(client_id, days)

            if not usage_data:
                return {"error": f"No usage data found for client {client_id}"}

            # Calculate key usage metrics
            metrics = self._calculate_usage_metrics(usage_data)

            # Analyze usage trends
            trends = self._analyze_usage_trends(usage_data)

            # Assess feature adoption
            adoption = self._assess_feature_adoption(usage_data)

            # Determine usage health score
            health_score = self._calculate_usage_health_score(metrics, trends, adoption)

            return {
                "client_id": client_id,
                "analysis_period_days": days,
                "metrics": metrics,
                "trends": trends,
                "feature_adoption": adoption,
                "health_score": health_score,
                "recommendations": self._generate_usage_recommendations(
                    metrics, trends, adoption, health_score
                ),
                "data_points": len(usage_data)
            }

        except Exception as e:
            logger.error(f"Error analyzing usage for client {client_id}: {e}")
            return {"error": str(e)}

    @tool("track_feature_adoption")
    async def track_feature_adoption(
        self,
        client_id: str,
        feature_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Track adoption of specific features or feature categories"""
        try:
            # Get all available features
            all_features = await self._get_available_features()

            # Get client's feature usage
            client_usage = await self._get_client_feature_usage(client_id)

            # Calculate adoption rates
            adoption_rates = {}
            for feature in all_features:
                feature_name = feature["name"]
                category = feature.get("category", "other")

                if feature_categories and category not in feature_categories:
                    continue

                usage_count = client_usage.get(feature_name, 0)
                adoption_rate = min(usage_count / feature.get("max_usage", 1), 1.0)

                adoption_rates[feature_name] = {
                    "category": category,
                    "usage_count": usage_count,
                    "adoption_rate": adoption_rate,
                    "last_used": client_usage.get(f"{feature_name}_last_used"),
                    "usage_frequency": client_usage.get(f"{feature_name}_frequency", "never")
                }

            # Group by category
            category_summary = {}
            for feature_name, data in adoption_rates.items():
                category = data["category"]
                if category not in category_summary:
                    category_summary[category] = {
                        "total_features": 0,
                        "adopted_features": 0,
                        "avg_adoption_rate": 0.0,
                        "features": []
                    }

                category_summary[category]["total_features"] += 1
                category_summary[category]["features"].append({
                    "name": feature_name,
                    "adoption_rate": data["adoption_rate"],
                    "usage_frequency": data["usage_frequency"]
                })

                if data["adoption_rate"] > 0.1:  # Consider adopted if used more than 10%
                    category_summary[category]["adopted_features"] += 1

            # Calculate averages
            for category, summary in category_summary.items():
                if summary["total_features"] > 0:
                    summary["avg_adoption_rate"] = (
                        sum(f["adoption_rate"] for f in summary["features"]) /
                        summary["total_features"]
                    )

            return {
                "client_id": client_id,
                "overall_adoption_rate": self._calculate_overall_adoption(adoption_rates),
                "category_summary": category_summary,
                "feature_details": adoption_rates,
                "recommendations": self._generate_adoption_recommendations(category_summary)
            }

        except Exception as e:
            logger.error(f"Error tracking feature adoption for client {client_id}: {e}")
            return {"error": str(e)}

    @tool("identify_usage_patterns")
    async def identify_usage_patterns(
        self,
        client_id: str,
        pattern_type: str = "all"
    ) -> Dict[str, Any]:
        """Identify usage patterns and behaviors"""
        try:
            usage_data = await self._fetch_usage_data(client_id, 90)  # 90 days for patterns

            patterns = {}

            if pattern_type in ["login", "all"]:
                patterns["login_patterns"] = self._analyze_login_patterns(usage_data)

            if pattern_type in ["feature", "all"]:
                patterns["feature_patterns"] = self._analyze_feature_patterns(usage_data)

            if pattern_type in ["engagement", "all"]:
                patterns["engagement_patterns"] = self._analyze_engagement_patterns(usage_data)

            if pattern_type in ["seasonal", "all"]:
                patterns["seasonal_patterns"] = self._analyze_seasonal_patterns(usage_data)

            return {
                "client_id": client_id,
                "patterns": patterns,
                "insights": self._generate_pattern_insights(patterns),
                "recommendations": self._generate_pattern_recommendations(patterns)
            }

        except Exception as e:
            logger.error(f"Error identifying usage patterns for client {client_id}: {e}")
            return {"error": str(e)}

    @tool("detect_usage_anomalies")
    async def detect_usage_anomalies(
        self,
        client_id: str,
        sensitivity: str = "medium"
    ) -> Dict[str, Any]:
        """Detect unusual usage patterns that may indicate issues"""
        try:
            # Get recent usage data
            recent_data = await self._fetch_usage_data(client_id, 30)
            historical_data = await self._fetch_usage_data(client_id, 90)

            anomalies = []

            # Check for sudden drops in usage
            usage_drop = self._detect_usage_drop(recent_data, historical_data)
            if usage_drop["is_anomaly"]:
                anomalies.append({
                    "type": "usage_drop",
                    "severity": usage_drop["severity"],
                    "description": usage_drop["description"],
                    "impact": usage_drop["impact"],
                    "recommendation": "Investigate recent changes or issues"
                })

            # Check for unusual feature usage
            feature_anomalies = self._detect_feature_anomalies(recent_data)
            anomalies.extend(feature_anomalies)

            # Check for login pattern changes
            login_anomalies = self._detect_login_anomalies(recent_data, historical_data)
            if login_anomalies:
                anomalies.append(login_anomalies)

            # Check for data quality issues
            data_quality_issues = self._detect_data_quality_issues(recent_data)
            if data_quality_issues:
                anomalies.append(data_quality_issues)

            return {
                "client_id": client_id,
                "anomalies_detected": len(anomalies),
                "anomalies": anomalies,
                "severity_summary": self._summarize_anomaly_severity(anomalies),
                "recommendations": self._generate_anomaly_recommendations(anomalies)
            }

        except Exception as e:
            logger.error(f"Error detecting usage anomalies for client {client_id}: {e}")
            return {"error": str(e)}

    @tool("generate_usage_insights")
    async def generate_usage_insights(
        self,
        client_id: str,
        insight_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Generate actionable insights from usage data"""
        try:
            # Gather all relevant data
            usage_analysis = await self.analyze_usage(client_id)
            feature_adoption = await self.track_feature_adoption(client_id)
            patterns = await self.identify_usage_patterns(client_id)
            anomalies = await self.detect_usage_anomalies(client_id)

            insights = []

            # Generate insights based on type
            if insight_type in ["comprehensive", "health"]:
                health_insights = self._generate_health_insights(usage_analysis)
                insights.extend(health_insights)

            if insight_type in ["comprehensive", "adoption"]:
                adoption_insights = self._generate_adoption_insights(feature_adoption)
                insights.extend(adoption_insights)

            if insight_type in ["comprehensive", "behavior"]:
                behavior_insights = self._generate_behavior_insights(patterns)
                insights.extend(behavior_insights)

            if insight_type in ["comprehensive", "risk"]:
                risk_insights = self._generate_risk_insights(anomalies)
                insights.extend(risk_insights)

            # Sort insights by priority
            insights.sort(key=lambda x: self._get_insight_priority(x), reverse=True)

            return {
                "client_id": client_id,
                "total_insights": len(insights),
                "insights": insights,
                "summary": self._generate_insight_summary(insights),
                "action_items": self._extract_action_items(insights)
            }

        except Exception as e:
            logger.error(f"Error generating usage insights for client {client_id}: {e}")
            return {"error": str(e)}

    async def _fetch_usage_data(self, client_id: str, days: int) -> List[Dict[str, Any]]:
        """Fetch usage data from the usage metrics service"""
        # Mock implementation - would make actual API calls
        return [
            {
                "date": "2024-01-15",
                "logins": 12,
                "features_used": ["dashboard", "reports", "analytics"],
                "session_duration": 45,
                "actions_performed": 25
            },
            {
                "date": "2024-01-16",
                "logins": 8,
                "features_used": ["dashboard", "reports"],
                "session_duration": 32,
                "actions_performed": 18
            }
        ]

    def _calculate_usage_metrics(self, usage_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate key usage metrics"""
        if not usage_data:
            return {}

        total_logins = sum(d.get("logins", 0) for d in usage_data)
        total_sessions = len(usage_data)
        avg_session_duration = sum(d.get("session_duration", 0) for d in usage_data) / max(total_sessions, 1)
        total_actions = sum(d.get("actions_performed", 0) for d in usage_data)

        # Calculate engagement score
        engagement_score = min(total_actions / (total_sessions * 20), 1.0)  # Normalize to 0-1

        return {
            "total_logins": total_logins,
            "total_sessions": total_sessions,
            "avg_daily_logins": total_logins / max(len(usage_data), 1),
            "avg_session_duration": avg_session_duration,
            "total_actions": total_actions,
            "avg_actions_per_session": total_actions / max(total_sessions, 1),
            "engagement_score": engagement_score,
            "login_frequency": self._calculate_login_frequency(usage_data)
        }

    def _analyze_usage_trends(self, usage_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze usage trends over time"""
        if len(usage_data) < 2:
            return {"trend": "insufficient_data"}

        # Sort by date
        usage_data.sort(key=lambda x: x.get("date", ""))

        # Calculate trend in key metrics
        recent_logins = sum(d.get("logins", 0) for d in usage_data[-7:])  # Last 7 days
        earlier_logins = sum(d.get("logins", 0) for d in usage_data[:-7])  # Earlier days

        if len(usage_data) > 7:
            recent_avg = recent_logins / 7
            earlier_avg = earlier_logins / max(len(usage_data) - 7, 1)

            if recent_avg > earlier_avg * 1.1:
                trend = "increasing"
                change_percent = ((recent_avg - earlier_avg) / earlier_avg) * 100
            elif recent_avg < earlier_avg * 0.9:
                trend = "decreasing"
                change_percent = ((earlier_avg - recent_avg) / earlier_avg) * 100
            else:
                trend = "stable"
                change_percent = 0
        else:
            trend = "stable"
            change_percent = 0

        return {
            "trend": trend,
            "change_percent": change_percent,
            "recent_avg_logins": recent_logins / min(7, len(usage_data)),
            "consistency_score": self._calculate_consistency_score(usage_data)
        }

    def _assess_feature_adoption(self, usage_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess feature adoption across all usage sessions"""
        all_features = set()
        feature_usage = {}

        for session in usage_data:
            features = session.get("features_used", [])
            for feature in features:
                all_features.add(feature)
                feature_usage[feature] = feature_usage.get(feature, 0) + 1

        total_sessions = len(usage_data)
        adoption_rates = {}

        for feature in all_features:
            usage_count = feature_usage.get(feature, 0)
            adoption_rate = usage_count / total_sessions
            adoption_rates[feature] = {
                "usage_count": usage_count,
                "adoption_rate": adoption_rate,
                "usage_frequency": "high" if adoption_rate > 0.5 else "medium" if adoption_rate > 0.2 else "low"
            }

        return {
            "total_features_available": len(all_features),
            "features_used": len(feature_usage),
            "adoption_rate": len(feature_usage) / max(len(all_features), 1),
            "feature_breakdown": adoption_rates,
            "most_used_features": sorted(adoption_rates.items(), key=lambda x: x[1]["usage_count"], reverse=True)[:5],
            "least_used_features": sorted(adoption_rates.items(), key=lambda x: x[1]["usage_count"])[:5]
        }

    def _calculate_usage_health_score(
        self,
        metrics: Dict[str, Any],
        trends: Dict[str, Any],
        adoption: Dict[str, Any]
    ) -> float:
        """Calculate overall usage health score"""
        score = 0.0

        # Login frequency (30% weight)
        login_score = min(metrics.get("avg_daily_logins", 0) / 5, 1.0)  # 5+ logins is healthy
        score += login_score * 0.3

        # Feature adoption (40% weight)
        adoption_score = adoption.get("adoption_rate", 0)
        score += adoption_score * 0.4

        # Engagement (20% weight)
        engagement_score = metrics.get("engagement_score", 0)
        score += engagement_score * 0.2

        # Trend bonus/penalty (10% weight)
        trend_multiplier = 1.0
        if trends.get("trend") == "increasing":
            trend_multiplier = 1.1
        elif trends.get("trend") == "decreasing":
            trend_multiplier = 0.9

        score = min(score * trend_multiplier, 1.0)

        return score

    def _generate_usage_recommendations(
        self,
        metrics: Dict[str, Any],
        trends: Dict[str, Any],
        adoption: Dict[str, Any],
        health_score: float
    ) -> List[str]:
        """Generate recommendations based on usage analysis"""
        recommendations = []

        if health_score < 0.6:
            recommendations.append("Schedule product adoption review and training session")

        if metrics.get("avg_daily_logins", 0) < 3:
            recommendations.append("Implement re-engagement campaign to increase login frequency")

        if adoption.get("adoption_rate", 0) < 0.5:
            recommendations.append("Create personalized feature adoption plan")

        if trends.get("trend") == "decreasing":
            recommendations.append("Investigate reasons for declining usage and address concerns")

        if not recommendations:
            recommendations.append("Continue current usage patterns and monitor for optimization opportunities")

        return recommendations

    async def _get_available_features(self) -> List[Dict[str, Any]]:
        """Get list of all available features"""
        # Mock implementation
        return [
            {"name": "dashboard", "category": "analytics", "max_usage": 10},
            {"name": "reports", "category": "analytics", "max_usage": 5},
            {"name": "user_management", "category": "admin", "max_usage": 3},
            {"name": "integrations", "category": "connectivity", "max_usage": 8}
        ]

    async def _get_client_feature_usage(self, client_id: str) -> Dict[str, Any]:
        """Get client's feature usage data"""
        # Mock implementation
        return {
            "dashboard": 15,
            "dashboard_last_used": "2024-01-20",
            "dashboard_frequency": "daily",
            "reports": 8,
            "reports_last_used": "2024-01-18",
            "reports_frequency": "weekly",
            "user_management": 2,
            "user_management_last_used": "2024-01-10",
            "user_management_frequency": "monthly"
        }

    def _calculate_overall_adoption(self, adoption_rates: Dict[str, Any]) -> float:
        """Calculate overall feature adoption rate"""
        if not adoption_rates:
            return 0.0

        total_adoption = sum(data["adoption_rate"] for data in adoption_rates.values())
        return total_adoption / len(adoption_rates)

    def _generate_adoption_recommendations(self, category_summary: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on feature adoption analysis"""
        recommendations = []

        for category, summary in category_summary.items():
            adoption_rate = summary.get("avg_adoption_rate", 0)
            if adoption_rate < 0.3:
                recommendations.append(f"Focus on improving adoption of {category} features")
            elif adoption_rate > 0.8:
                recommendations.append(f"Consider advanced training for {category} features")

        return recommendations

    def _analyze_login_patterns(self, usage_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze login patterns"""
        logins = [d.get("logins", 0) for d in usage_data]

        return {
            "avg_daily_logins": sum(logins) / max(len(logins), 1),
            "login_consistency": self._calculate_consistency_score(usage_data),
            "peak_usage_days": self._identify_peak_days(usage_data),
            "login_trend": "increasing" if logins[-1] > logins[0] else "stable"
        }

    def _analyze_feature_patterns(self, usage_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze feature usage patterns"""
        feature_usage = {}
        for session in usage_data:
            for feature in session.get("features_used", []):
                feature_usage[feature] = feature_usage.get(feature, 0) + 1

        return {
            "most_used_features": sorted(feature_usage.items(), key=lambda x: x[1], reverse=True)[:3],
            "feature_diversity": len(feature_usage) / max(len(usage_data), 1),
            "usage_patterns": "diverse" if len(feature_usage) > 5 else "focused"
        }

    def _analyze_engagement_patterns(self, usage_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze engagement patterns"""
        durations = [d.get("session_duration", 0) for d in usage_data]
        actions = [d.get("actions_performed", 0) for d in usage_data]

        return {
            "avg_session_duration": sum(durations) / max(len(durations), 1),
            "avg_actions_per_session": sum(actions) / max(len(actions), 1),
            "engagement_level": "high" if sum(actions) > 20 * len(actions) else "moderate",
            "consistency": self._calculate_consistency_score(usage_data)
        }

    def _analyze_seasonal_patterns(self, usage_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze seasonal usage patterns"""
        # Simple day-of-week analysis
        weekday_usage = {}
        for session in usage_data:
            # Mock weekday analysis
            weekday = "monday"  # Would extract from date
            weekday_usage[weekday] = weekday_usage.get(weekday, 0) + 1

        return {
            "peak_day": max(weekday_usage.items(), key=lambda x: x[1])[0] if weekday_usage else "unknown",
            "seasonal_variation": "moderate",
            "recommendations": ["Schedule key activities on peak usage days"]
        }

    def _generate_pattern_insights(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate insights from usage patterns"""
        insights = []

        login_patterns = patterns.get("login_patterns", {})
        if login_patterns.get("login_trend") == "increasing":
            insights.append("Login frequency is increasing - positive engagement trend")

        feature_patterns = patterns.get("feature_patterns", {})
        if feature_patterns.get("usage_patterns") == "focused":
            insights.append("User focuses on specific features - opportunity for broader adoption")

        return insights

    def _generate_pattern_recommendations(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on usage patterns"""
        recommendations = []

        engagement_patterns = patterns.get("engagement_patterns", {})
        if engagement_patterns.get("engagement_level") == "moderate":
            recommendations.append("Implement strategies to increase session engagement")

        return recommendations

    def _detect_usage_drop(self, recent_data: List[Dict[str, Any]], historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect significant drops in usage"""
        if len(recent_data) < 7 or len(historical_data) < 14:
            return {"is_anomaly": False}

        recent_avg = sum(d.get("logins", 0) for d in recent_data) / len(recent_data)
        historical_avg = sum(d.get("logins", 0) for d in historical_data[:-7]) / max(len(historical_data) - 7, 1)

        if historical_avg == 0:
            return {"is_anomaly": False}

        drop_percentage = (historical_avg - recent_avg) / historical_avg

        if drop_percentage > 0.5:
            return {
                "is_anomaly": True,
                "severity": "high",
                "description": f"Usage dropped by {drop_percentage:.1%}",
                "impact": "critical"
            }
        elif drop_percentage > 0.3:
            return {
                "is_anomaly": True,
                "severity": "medium",
                "description": f"Usage dropped by {drop_percentage:.1%}",
                "impact": "moderate"
            }

        return {"is_anomaly": False}

    def _detect_feature_anomalies(self, recent_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in feature usage"""
        anomalies = []

        # Check for sudden feature abandonment
        feature_usage = {}
        for session in recent_data:
            for feature in session.get("features_used", []):
                feature_usage[feature] = feature_usage.get(feature, 0) + 1

        # Mock anomaly detection
        for feature, count in feature_usage.items():
            if count == 0:  # Feature not used in recent period
                anomalies.append({
                    "type": "feature_abandonment",
                    "severity": "medium",
                    "description": f"Feature '{feature}' not used recently",
                    "impact": "low",
                    "recommendation": "Check if feature is still needed or if there are issues"
                })

        return anomalies

    def _detect_login_anomalies(self, recent_data: List[Dict[str, Any]], historical_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Detect anomalies in login patterns"""
        # Mock implementation
        return None

    def _detect_data_quality_issues(self, recent_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Detect data quality issues"""
        # Mock implementation
        return None

    def _summarize_anomaly_severity(self, anomalies: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize anomaly severities"""
        summary = {"high": 0, "medium": 0, "low": 0}

        for anomaly in anomalies:
            severity = anomaly.get("severity", "low")
            summary[severity] = summary.get(severity, 0) + 1

        return summary

    def _generate_anomaly_recommendations(self, anomalies: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on detected anomalies"""
        recommendations = []

        for anomaly in anomalies:
            if anomaly.get("type") == "usage_drop":
                recommendations.append("Investigate recent changes that may have caused usage drop")
            elif anomaly.get("type") == "feature_abandonment":
                recommendations.append("Review feature relevance and user feedback")

        return recommendations

    def _generate_health_insights(self, usage_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate health-related insights"""
        insights = []

        health_score = usage_analysis.get("health_score", 0)
        if health_score < 0.6:
            insights.append({
                "type": "health",
                "priority": "high",
                "title": "Low Usage Health Score",
                "description": f"Usage health score is {health_score:.1%}, indicating potential engagement issues",
                "recommendation": "Schedule usage review and identify barriers to adoption"
            })

        return insights

    def _generate_adoption_insights(self, feature_adoption: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate adoption-related insights"""
        insights = []

        overall_rate = feature_adoption.get("overall_adoption_rate", 0)
        if overall_rate < 0.5:
            insights.append({
                "type": "adoption",
                "priority": "medium",
                "title": "Low Feature Adoption",
                "description": f"Only {overall_rate:.1%} of available features are being used",
                "recommendation": "Create feature adoption plan and provide targeted training"
            })

        return insights

    def _generate_behavior_insights(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate behavior-related insights"""
        insights = []

        # Add pattern-based insights
        pattern_insights = patterns.get("insights", [])
        for insight in pattern_insights:
            insights.append({
                "type": "behavior",
                "priority": "low",
                "title": "Usage Pattern Insight",
                "description": insight,
                "recommendation": "Monitor and optimize based on identified patterns"
            })

        return insights

    def _generate_risk_insights(self, anomalies: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate risk-related insights"""
        insights = []

        anomaly_count = anomalies.get("anomalies_detected", 0)
        if anomaly_count > 0:
            insights.append({
                "type": "risk",
                "priority": "high",
                "title": "Usage Anomalies Detected",
                "description": f"Found {anomaly_count} usage anomalies that require attention",
                "recommendation": "Review anomalies and take corrective action"
            })

        return insights

    def _get_insight_priority(self, insight: Dict[str, Any]) -> int:
        """Get priority score for insight sorting"""
        priority_map = {"high": 3, "medium": 2, "low": 1}
        return priority_map.get(insight.get("priority", "low"), 1)

    def _generate_insight_summary(self, insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of all insights"""
        summary = {
            "total_insights": len(insights),
            "by_priority": {"high": 0, "medium": 0, "low": 0},
            "by_type": {}
        }

        for insight in insights:
            priority = insight.get("priority", "low")
            summary["by_priority"][priority] += 1

            insight_type = insight.get("type", "other")
            summary["by_type"][insight_type] = summary["by_type"].get(insight_type, 0) + 1

        return summary

    def _extract_action_items(self, insights: List[Dict[str, Any]]) -> List[str]:
        """Extract action items from insights"""
        action_items = []

        for insight in insights:
            recommendation = insight.get("recommendation", "")
            if recommendation:
                action_items.append(recommendation)

        return list(set(action_items))  # Remove duplicates

    def _calculate_login_frequency(self, usage_data: List[Dict[str, Any]]) -> str:
        """Calculate login frequency description"""
        if not usage_data:
            return "no_data"

        avg_logins = sum(d.get("logins", 0) for d in usage_data) / len(usage_data)

        if avg_logins >= 5:
            return "daily"
        elif avg_logins >= 3:
            return "frequent"
        elif avg_logins >= 1:
            return "regular"
        else:
            return "infrequent"

    def _calculate_consistency_score(self, usage_data: List[Dict[str, Any]]) -> float:
        """Calculate consistency score for usage patterns"""
        if len(usage_data) < 2:
            return 0.5

        # Simple consistency based on login variance
        logins = [d.get("logins", 0) for d in usage_data]

        if len(set(logins)) == 1:
            return 1.0  # Perfect consistency

        # Calculate coefficient of variation
        mean_logins = sum(logins) / len(logins)
        if mean_logins == 0:
            return 0.0

        variance = sum((x - mean_logins) ** 2 for x in logins) / len(logins)
        std_dev = variance ** 0.5
        cv = std_dev / mean_logins

        # Lower coefficient of variation = higher consistency
        return max(0, 1 - cv)

    def _identify_peak_days(self, usage_data: List[Dict[str, Any]]) -> List[str]:
        """Identify peak usage days"""
        # Mock implementation
        return ["monday", "wednesday", "friday"]