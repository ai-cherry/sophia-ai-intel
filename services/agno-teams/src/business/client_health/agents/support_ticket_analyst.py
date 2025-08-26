"""
Support Ticket Analyst Agent - Analyzes support tickets and identifies client health issues
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from agno import Agent
from agno.tools import tool

logger = logging.getLogger(__name__)

class SupportTicketAnalystAgent(Agent):
    """Analyzes support tickets to identify client health issues and patterns"""

    def __init__(self, name: str, integrations: Dict[str, str]):
        super().__init__(
            name=name,
            role="""I am a Support Ticket Analyst responsible for:
            - Analyzing support ticket patterns and trends
            - Identifying recurring issues and root causes
            - Assessing client satisfaction and support needs
            - Providing insights on product issues and improvements
            - Recommending proactive support strategies
            """,
            tools=self._create_tools()
        )

        self.integrations = integrations
        self.support_url = integrations.get("support_system", "http://mcp-support:8080")

    def _create_tools(self) -> List[Any]:
        """Create tools for support ticket analysis"""
        return [
            self.analyze_support_tickets,
            self.identify_recurring_issues,
            self.assess_client_satisfaction,
            self.detect_support_trends,
            self.generate_support_insights
        ]

    @tool("analyze_support_tickets")
    async def analyze_support_tickets(
        self,
        client_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Analyze comprehensive support ticket data for a client"""
        try:
            # Fetch support tickets from the support system
            tickets = await self._fetch_support_tickets(client_id, days)

            if not tickets:
                return {"error": f"No support tickets found for client {client_id}"}

            # Calculate key support metrics
            metrics = self._calculate_support_metrics(tickets)

            # Analyze ticket trends
            trends = self._analyze_ticket_trends(tickets)

            # Assess issue categories
            categories = self._assess_issue_categories(tickets)

            # Calculate support health score
            health_score = self._calculate_support_health_score(metrics, trends, categories)

            return {
                "client_id": client_id,
                "analysis_period_days": days,
                "metrics": metrics,
                "trends": trends,
                "issue_categories": categories,
                "health_score": health_score,
                "recommendations": self._generate_support_recommendations(
                    metrics, trends, categories, health_score
                ),
                "ticket_count": len(tickets)
            }

        except Exception as e:
            logger.error(f"Error analyzing support tickets for client {client_id}: {e}")
            return {"error": str(e)}

    @tool("identify_recurring_issues")
    async def identify_recurring_issues(
        self,
        client_id: str,
        min_occurrences: int = 2
    ) -> Dict[str, Any]:
        """Identify recurring issues and patterns in support tickets"""
        try:
            # Get tickets from longer period to identify patterns
            tickets = await self._fetch_support_tickets(client_id, 90)

            # Group tickets by issue type and description
            issue_groups = self._group_tickets_by_issue(tickets)

            # Identify recurring issues
            recurring_issues = []
            for issue_key, issue_tickets in issue_groups.items():
                if len(issue_tickets) >= min_occurrences:
                    recurring_issues.append({
                        "issue_key": issue_key,
                        "occurrences": len(issue_tickets),
                        "first_occurrence": min(t.get("created_date") for t in issue_tickets),
                        "last_occurrence": max(t.get("created_date") for t in issue_tickets),
                        "avg_resolution_time": self._calculate_avg_resolution_time(issue_tickets),
                        "severity_distribution": self._calculate_severity_distribution(issue_tickets),
                        "status_distribution": self._calculate_status_distribution(issue_tickets),
                        "sample_tickets": issue_tickets[:3]  # Include first 3 for context
                    })

            # Sort by frequency and recency
            recurring_issues.sort(key=lambda x: (x["occurrences"], x["last_occurrence"]), reverse=True)

            # Calculate recurrence metrics
            recurrence_metrics = self._calculate_recurrence_metrics(recurring_issues, len(tickets))

            return {
                "client_id": client_id,
                "total_tickets": len(tickets),
                "recurring_issues_count": len(recurring_issues),
                "recurring_issues": recurring_issues,
                "recurrence_metrics": recurrence_metrics,
                "insights": self._generate_recurrence_insights(recurring_issues, recurrence_metrics),
                "recommendations": self._generate_recurrence_recommendations(recurring_issues)
            }

        except Exception as e:
            logger.error(f"Error identifying recurring issues for client {client_id}: {e}")
            return {"error": str(e)}

    @tool("assess_client_satisfaction")
    async def assess_client_satisfaction(
        self,
        client_id: str,
        include_feedback: bool = True
    ) -> Dict[str, Any]:
        """Assess client satisfaction based on support interactions"""
        try:
            tickets = await self._fetch_support_tickets(client_id, 60)  # 60 days for satisfaction analysis

            # Calculate satisfaction metrics
            satisfaction_metrics = self._calculate_satisfaction_metrics(tickets)

            # Analyze response times impact on satisfaction
            response_time_impact = self._analyze_response_time_impact(tickets)

            # Assess resolution effectiveness
            resolution_effectiveness = self._assess_resolution_effectiveness(tickets)

            # Calculate overall satisfaction score
            satisfaction_score = self._calculate_satisfaction_score(
                satisfaction_metrics, response_time_impact, resolution_effectiveness
            )

            # Generate satisfaction insights
            insights = self._generate_satisfaction_insights(
                satisfaction_score, satisfaction_metrics, response_time_impact, resolution_effectiveness
            )

            return {
                "client_id": client_id,
                "satisfaction_score": satisfaction_score,
                "satisfaction_metrics": satisfaction_metrics,
                "response_time_impact": response_time_impact,
                "resolution_effectiveness": resolution_effectiveness,
                "insights": insights,
                "recommendations": self._generate_satisfaction_recommendations(satisfaction_score, insights)
            }

        except Exception as e:
            logger.error(f"Error assessing client satisfaction for client {client_id}: {e}")
            return {"error": str(e)}

    @tool("detect_support_trends")
    async def detect_support_trends(
        self,
        client_id: str,
        trend_period: str = "quarterly"
    ) -> Dict[str, Any]:
        """Detect trends in support ticket volume and types"""
        try:
            # Determine analysis period based on trend_period
            if trend_period == "quarterly":
                days = 90
            elif trend_period == "monthly":
                days = 30
            else:  # weekly
                days = 7

            tickets = await self._fetch_support_tickets(client_id, days * 4)  # Get 4x period for trend analysis

            # Analyze volume trends
            volume_trends = self._analyze_volume_trends(tickets, trend_period)

            # Analyze category trends
            category_trends = self._analyze_category_trends(tickets, trend_period)

            # Analyze severity trends
            severity_trends = self._analyze_severity_trends(tickets, trend_period)

            # Analyze resolution time trends
            resolution_trends = self._analyze_resolution_trends(tickets, trend_period)

            # Identify emerging issues
            emerging_issues = self._identify_emerging_issues(tickets, trend_period)

            return {
                "client_id": client_id,
                "trend_period": trend_period,
                "analysis_period_days": days * 4,
                "volume_trends": volume_trends,
                "category_trends": category_trends,
                "severity_trends": severity_trends,
                "resolution_trends": resolution_trends,
                "emerging_issues": emerging_issues,
                "overall_trend": self._determine_overall_trend(volume_trends, severity_trends),
                "insights": self._generate_trend_insights(volume_trends, category_trends, severity_trends),
                "recommendations": self._generate_trend_recommendations(volume_trends, emerging_issues)
            }

        except Exception as e:
            logger.error(f"Error detecting support trends for client {client_id}: {e}")
            return {"error": str(e)}

    @tool("generate_support_insights")
    async def generate_support_insights(
        self,
        client_id: str,
        insight_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Generate actionable insights from support ticket analysis"""
        try:
            # Gather all relevant data
            ticket_analysis = await self.analyze_support_tickets(client_id)
            recurring_issues = await self.identify_recurring_issues(client_id)
            satisfaction = await self.assess_client_satisfaction(client_id)
            trends = await self.detect_support_trends(client_id)

            insights = []

            # Generate insights based on type
            if insight_type in ["comprehensive", "health"]:
                health_insights = self._generate_health_insights(ticket_analysis)
                insights.extend(health_insights)

            if insight_type in ["comprehensive", "recurrence"]:
                recurrence_insights = self._generate_recurrence_insights(recurring_issues)
                insights.extend(recurrence_insights)

            if insight_type in ["comprehensive", "satisfaction"]:
                satisfaction_insights = self._generate_satisfaction_insights(satisfaction)
                insights.extend(satisfaction_insights)

            if insight_type in ["comprehensive", "trends"]:
                trend_insights = self._generate_trend_insights(trends)
                insights.extend(trend_insights)

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
            logger.error(f"Error generating support insights for client {client_id}: {e}")
            return {"error": str(e)}

    async def _fetch_support_tickets(self, client_id: str, days: int) -> List[Dict[str, Any]]:
        """Fetch support tickets from the support system"""
        # Mock implementation - would make actual API calls
        return [
            {
                "id": "TICKET-001",
                "client_id": client_id,
                "subject": "Login issues",
                "description": "Unable to login to dashboard",
                "category": "authentication",
                "severity": "high",
                "status": "resolved",
                "created_date": "2024-01-15",
                "resolved_date": "2024-01-16",
                "resolution_time_hours": 4,
                "satisfaction_rating": 4,
                "assigned_agent": "support_agent_1"
            },
            {
                "id": "TICKET-002",
                "client_id": client_id,
                "subject": "Report generation failed",
                "description": "Weekly report not generating",
                "category": "reporting",
                "severity": "medium",
                "status": "resolved",
                "created_date": "2024-01-18",
                "resolved_date": "2024-01-19",
                "resolution_time_hours": 8,
                "satisfaction_rating": 3,
                "assigned_agent": "support_agent_2"
            }
        ]

    def _calculate_support_metrics(self, tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate key support metrics"""
        if not tickets:
            return {}

        total_tickets = len(tickets)
        resolved_tickets = len([t for t in tickets if t.get("status") == "resolved"])
        resolution_rate = resolved_tickets / total_tickets if total_tickets > 0 else 0

        # Calculate average resolution time
        resolution_times = [t.get("resolution_time_hours", 0) for t in tickets if t.get("resolution_time_hours")]
        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0

        # Calculate tickets by severity
        severity_counts = {}
        for ticket in tickets:
            severity = ticket.get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Calculate tickets by category
        category_counts = {}
        for ticket in tickets:
            category = ticket.get("category", "unknown")
            category_counts[category] = category_counts.get(category, 0) + 1

        return {
            "total_tickets": total_tickets,
            "resolved_tickets": resolved_tickets,
            "resolution_rate": resolution_rate,
            "avg_resolution_time_hours": avg_resolution_time,
            "tickets_per_day": total_tickets / max(len(set(t.get("created_date") for t in tickets)), 1),
            "severity_distribution": severity_counts,
            "category_distribution": category_counts,
            "most_common_category": max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else "none"
        }

    def _analyze_ticket_trends(self, tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze ticket trends over time"""
        if len(tickets) < 2:
            return {"trend": "insufficient_data"}

        # Sort by date
        tickets.sort(key=lambda x: x.get("created_date", ""))

        # Calculate trend in ticket volume
        recent_tickets = len([t for t in tickets if t.get("created_date", "") > tickets[len(tickets)//2].get("created_date", "")])
        earlier_tickets = len(tickets) - recent_tickets

        if len(tickets) > 1:
            recent_avg = recent_tickets / (len(tickets) // 2)
            earlier_avg = earlier_tickets / (len(tickets) - len(tickets) // 2)

            if recent_avg > earlier_avg * 1.2:
                trend = "increasing"
                change_percent = ((recent_avg - earlier_avg) / earlier_avg) * 100
            elif recent_avg < earlier_avg * 0.8:
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
            "recent_volume": recent_tickets,
            "earlier_volume": earlier_tickets,
            "volatility": self._calculate_ticket_volatility(tickets)
        }

    def _assess_issue_categories(self, tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess issue categories and their impact"""
        category_stats = {}

        for ticket in tickets:
            category = ticket.get("category", "unknown")
            if category not in category_stats:
                category_stats[category] = {
                    "count": 0,
                    "avg_severity": 0,
                    "avg_resolution_time": 0,
                    "resolution_rate": 0
                }

            category_stats[category]["count"] += 1

            # Map severity to numeric value
            severity_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            severity = severity_map.get(ticket.get("severity", "medium"), 2)
            category_stats[category]["avg_severity"] += severity

            resolution_time = ticket.get("resolution_time_hours", 0)
            category_stats[category]["avg_resolution_time"] += resolution_time

            if ticket.get("status") == "resolved":
                category_stats[category]["resolution_rate"] += 1

        # Calculate averages
        for category, stats in category_stats.items():
            count = stats["count"]
            stats["avg_severity"] = stats["avg_severity"] / count
            stats["avg_resolution_time"] = stats["avg_resolution_time"] / count
            stats["resolution_rate"] = stats["resolution_rate"] / count

        # Sort by frequency
        sorted_categories = sorted(category_stats.items(), key=lambda x: x[1]["count"], reverse=True)

        return {
            "category_stats": category_stats,
            "most_common_category": sorted_categories[0][0] if sorted_categories else "none",
            "highest_severity_category": max(category_stats.items(), key=lambda x: x[1]["avg_severity"])[0] if category_stats else "none",
            "slowest_resolution_category": max(category_stats.items(), key=lambda x: x[1]["avg_resolution_time"])[0] if category_stats else "none",
            "category_count": len(category_stats)
        }

    def _calculate_support_health_score(
        self,
        metrics: Dict[str, Any],
        trends: Dict[str, Any],
        categories: Dict[str, Any]
    ) -> float:
        """Calculate overall support health score"""
        score = 0.0

        # Resolution rate (40% weight)
        resolution_score = metrics.get("resolution_rate", 0)
        score += resolution_score * 0.4

        # Average resolution time (30% weight) - lower is better
        avg_time = metrics.get("avg_resolution_time_hours", 24)
        time_score = max(0, 1 - (avg_time / 48))  # 48 hours is very poor
        score += time_score * 0.3

        # Ticket volume trend (20% weight) - stable or decreasing is better
        trend_multiplier = 1.0
        if trends.get("trend") == "increasing":
            trend_multiplier = 0.8
        elif trends.get("trend") == "decreasing":
            trend_multiplier = 1.1

        score = min(score * trend_multiplier, 1.0)

        # Category diversity bonus (10% weight) - more diverse categories suggest fewer recurring issues
        category_count = categories.get("category_count", 1)
        diversity_score = min(category_count / 10, 1.0)  # Cap at 10 categories
        score += diversity_score * 0.1

        return score

    def _generate_support_recommendations(
        self,
        metrics: Dict[str, Any],
        trends: Dict[str, Any],
        categories: Dict[str, Any],
        health_score: float
    ) -> List[str]:
        """Generate recommendations based on support analysis"""
        recommendations = []

        if health_score < 0.6:
            recommendations.append("Review support processes and identify bottlenecks")

        if metrics.get("resolution_rate", 0) < 0.8:
            recommendations.append("Improve ticket resolution processes and agent training")

        if metrics.get("avg_resolution_time_hours", 0) > 24:
            recommendations.append("Implement strategies to reduce average resolution time")

        if trends.get("trend") == "increasing":
            recommendations.append("Investigate causes of increasing ticket volume")

        if categories.get("category_count", 0) < 3:
            recommendations.append("Address recurring issues in dominant categories")

        return recommendations

    def _group_tickets_by_issue(self, tickets: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group tickets by issue type and description"""
        issue_groups = {}

        for ticket in tickets:
            # Create issue key from category and subject keywords
            category = ticket.get("category", "unknown")
            subject = ticket.get("subject", "").lower()

            # Extract key terms from subject
            key_terms = self._extract_key_terms(subject)
            issue_key = f"{category}:{','.join(key_terms)}"

            if issue_key not in issue_groups:
                issue_groups[issue_key] = []

            issue_groups[issue_key].append(ticket)

        return issue_groups

    def _extract_key_terms(self, subject: str) -> List[str]:
        """Extract key terms from ticket subject"""
        # Simple keyword extraction - could be enhanced with NLP
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "not", "is", "are", "was", "were"}
        words = subject.split()
        key_terms = [word for word in words if word not in common_words and len(word) > 2]
        return key_terms[:3]  # Limit to 3 key terms

    def _calculate_avg_resolution_time(self, tickets: List[Dict[str, Any]]) -> float:
        """Calculate average resolution time for a group of tickets"""
        resolution_times = [t.get("resolution_time_hours", 0) for t in tickets if t.get("resolution_time_hours")]
        return sum(resolution_times) / len(resolution_times) if resolution_times else 0

    def _calculate_severity_distribution(self, tickets: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate severity distribution for tickets"""
        severity_counts = {}
        for ticket in tickets:
            severity = ticket.get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        return severity_counts

    def _calculate_status_distribution(self, tickets: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate status distribution for tickets"""
        status_counts = {}
        for ticket in tickets:
            status = ticket.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        return status_counts

    def _calculate_recurrence_metrics(
        self,
        recurring_issues: List[Dict[str, Any]],
        total_tickets: int
    ) -> Dict[str, Any]:
        """Calculate metrics related to recurring issues"""
        if not recurring_issues:
            return {"recurrence_rate": 0, "avg_occurrences": 0, "most_frequent_category": "none"}

        total_recurring_tickets = sum(issue["occurrences"] for issue in recurring_issues)
        recurrence_rate = total_recurring_tickets / total_tickets if total_tickets > 0 else 0

        avg_occurrences = total_recurring_tickets / len(recurring_issues)

        # Find most frequent category
        category_counts = {}
        for issue in recurring_issues:
            category = issue["issue_key"].split(":")[0]
            category_counts[category] = category_counts.get(category, 0) + issue["occurrences"]

        most_frequent_category = max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else "none"

        return {
            "recurrence_rate": recurrence_rate,
            "avg_occurrences": avg_occurrences,
            "most_frequent_category": most_frequent_category,
            "unique_recurring_issues": len(recurring_issues),
            "recurring_tickets": total_recurring_tickets
        }

    def _generate_recurrence_insights(
        self,
        recurring_issues: List[Dict[str, Any]],
        metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate insights about recurring issues"""
        insights = []

        if metrics.get("recurrence_rate", 0) > 0.3:
            insights.append(f"High recurrence rate ({metrics['recurrence_rate']:.1%}) indicates systemic issues")

        if metrics.get("avg_occurrences", 0) > 5:
            insights.append("Some issues recur frequently - consider permanent fixes")

        if len(recurring_issues) > 0:
            insights.append(f"Found {len(recurring_issues)} recurring issue patterns")

        return insights

    def _generate_recurrence_recommendations(self, recurring_issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for recurring issues"""
        recommendations = []

        if not recurring_issues:
            return ["Monitor for emerging recurring issues"]

        # Sort by impact (occurrences * severity)
        high_impact_issues = []
        for issue in recurring_issues:
            severity_score = sum(self._severity_to_score(sev) * count
                               for sev, count in issue.get("severity_distribution", {}).items())
            impact = issue["occurrences"] * severity_score
            high_impact_issues.append((issue, impact))

        high_impact_issues.sort(key=lambda x: x[1], reverse=True)

        for issue, impact in high_impact_issues[:3]:  # Top 3
            recommendations.append(f"Address recurring issue: {issue['issue_key']} ({issue['occurrences']} occurrences)")

        return recommendations

    def _severity_to_score(self, severity: str) -> float:
        """Convert severity to numeric score"""
        severity_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return severity_map.get(severity, 2)

    def _calculate_satisfaction_metrics(self, tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate satisfaction metrics from tickets"""
        satisfaction_ratings = [t.get("satisfaction_rating") for t in tickets if t.get("satisfaction_rating")]

        if not satisfaction_ratings:
            return {"avg_rating": 0, "rating_count": 0, "rating_distribution": {}}

        avg_rating = sum(satisfaction_ratings) / len(satisfaction_ratings)

        # Calculate distribution
        distribution = {}
        for rating in satisfaction_ratings:
            distribution[rating] = distribution.get(rating, 0) + 1

        return {
            "avg_rating": avg_rating,
            "rating_count": len(satisfaction_ratings),
            "rating_distribution": distribution,
            "satisfaction_rate": len([r for r in satisfaction_ratings if r >= 4]) / len(satisfaction_ratings)
        }

    def _analyze_response_time_impact(self, tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how response time affects satisfaction"""
        # Group tickets by response time buckets
        response_buckets = {
            "fast": [],  # < 4 hours
            "medium": [],  # 4-24 hours
            "slow": []  # > 24 hours
        }

        for ticket in tickets:
            resolution_time = ticket.get("resolution_time_hours", 0)
            rating = ticket.get("satisfaction_rating")

            if rating is None:
                continue

            if resolution_time < 4:
                response_buckets["fast"].append(rating)
            elif resolution_time < 24:
                response_buckets["medium"].append(rating)
            else:
                response_buckets["slow"].append(rating)

        # Calculate average satisfaction by bucket
        bucket_averages = {}
        for bucket, ratings in response_buckets.items():
            if ratings:
                bucket_averages[bucket] = sum(ratings) / len(ratings)
            else:
                bucket_averages[bucket] = 0

        return {
            "bucket_averages": bucket_averages,
            "correlation": self._calculate_time_satisfaction_correlation(response_buckets),
            "fast_resolution_rate": len(response_buckets["fast"]) / max(len(tickets), 1)
        }

    def _calculate_time_satisfaction_correlation(self, response_buckets: Dict[str, List[float]]) -> float:
        """Calculate correlation between response time and satisfaction"""
        # Simple correlation calculation
        all_times = []
        all_ratings = []

        time_map = {"fast": 1, "medium": 2, "slow": 3}

        for bucket, ratings in response_buckets.items():
            time_value = time_map[bucket]
            for rating in ratings:
                all_times.append(time_value)
                all_ratings.append(rating)

        if len(all_times) < 2:
            return 0

        # Calculate Pearson correlation coefficient
        n = len(all_times)
        sum_x = sum(all_times)
        sum_y = sum(all_ratings)
        sum_xy = sum(x * y for x, y in zip(all_times, all_ratings))
        sum_x2 = sum(x * x for x in all_times)
        sum_y2 = sum(y * y for y in all_ratings)

        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5

        return numerator / denominator if denominator != 0 else 0

    def _assess_resolution_effectiveness(self, tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess how effectively issues are resolved"""
        resolved_tickets = [t for t in tickets if t.get("status") == "resolved"]
        unresolved_tickets = [t for t in tickets if t.get("status") != "resolved"]

        if not resolved_tickets:
            return {"effectiveness_score": 0, "first_contact_resolution": 0}

        # Calculate first contact resolution rate (mock)
        first_contact_resolution = len([t for t in resolved_tickets if t.get("resolution_time_hours", 0) < 1]) / len(resolved_tickets)

        # Calculate effectiveness based on resolution rate and time
        resolution_rate = len(resolved_tickets) / len(tickets)
        avg_resolution_time = sum(t.get("resolution_time_hours", 0) for t in resolved_tickets) / len(resolved_tickets)

        # Effectiveness score combines resolution rate and speed
        time_score = max(0, 1 - (avg_resolution_time / 48))  # Normalize to 0-1
        effectiveness_score = (resolution_rate * 0.7) + (time_score * 0.3)

        return {
            "effectiveness_score": effectiveness_score,
            "first_contact_resolution": first_contact_resolution,
            "resolution_rate": resolution_rate,
            "avg_resolution_time": avg_resolution_time,
            "unresolved_count": len(unresolved_tickets)
        }

    def _calculate_satisfaction_score(
        self,
        metrics: Dict[str, Any],
        response_time_impact: Dict[str, Any],
        resolution_effectiveness: Dict[str, Any]
    ) -> float:
        """Calculate overall satisfaction score"""
        score = 0.0

        # Direct satisfaction rating (50% weight)
        rating_score = metrics.get("avg_rating", 0) / 5  # Normalize to 0-1
        score += rating_score * 0.5

        # Resolution effectiveness (30% weight)
        effectiveness_score = resolution_effectiveness.get("effectiveness_score", 0)
        score += effectiveness_score * 0.3

        # Response time impact (20% weight) - inverse correlation is good
        correlation = response_time_impact.get("correlation", 0)
        time_score = max(0, 1 - abs(correlation))  # Lower correlation is better
        score += time_score * 0.2

        return score

    def _generate_satisfaction_insights(
        self,
        satisfaction_score: float,
        metrics: Dict[str, Any],
        response_time_impact: Dict[str, Any],
        resolution_effectiveness: Dict[str, Any]
    ) -> List[str]:
        """Generate insights about client satisfaction"""
        insights = []

        if satisfaction_score < 0.6:
            insights.append(f"Low satisfaction score ({satisfaction_score:.1%}) requires immediate attention")

        if metrics.get("avg_rating", 0) < 3.5:
            insights.append("Average satisfaction rating below acceptable threshold")

        if resolution_effectiveness.get("first_contact_resolution", 0) < 0.5:
            insights.append("Low first-contact resolution rate indicates process inefficiencies")

        correlation = response_time_impact.get("correlation", 0)
        if correlation > 0.5:
            insights.append("Strong negative correlation between response time and satisfaction")

        return insights

    def _generate_satisfaction_recommendations(
        self,
        satisfaction_score: float,
        insights: List[str]
    ) -> List[str]:
        """Generate recommendations to improve satisfaction"""
        recommendations = []

        if satisfaction_score < 0.6:
            recommendations.append("Implement customer satisfaction improvement program")

        if "Low satisfaction rating" in str(insights):
            recommendations.append("Review and improve support agent training and processes")

        if "first-contact resolution" in str(insights):
            recommendations.append("Focus on resolving issues on first contact")

        if "response time" in str(insights):
            recommendations.append("Improve response times and set clear SLAs")

        return recommendations

    def _analyze_volume_trends(self, tickets: List[Dict[str, Any]], period: str) -> Dict[str, Any]:
        """Analyze ticket volume trends"""
        # Group tickets by time period
        period_groups = self._group_tickets_by_period(tickets, period)

        volumes = [len(group) for group in period_groups.values()]

        if len(volumes) < 2:
            return {"trend": "insufficient_data", "volumes": volumes}

        # Calculate trend
        recent_avg = sum(volumes[-2:]) / 2
        earlier_avg = sum(volumes[:-2]) / max(len(volumes) - 2, 1)

        if recent_avg > earlier_avg * 1.1:
            trend = "increasing"
        elif recent_avg < earlier_avg * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "volumes": volumes,
            "periods": list(period_groups.keys()),
            "avg_volume": sum(volumes) / len(volumes),
            "volatility": self._calculate_volume_volatility(volumes)
        }

    def _analyze_category_trends(self, tickets: List[Dict[str, Any]], period: str) -> Dict[str, Any]:
        """Analyze category trends over time"""
        period_groups = self._group_tickets_by_period(tickets, period)

        category_trends = {}
        for period_key, period_tickets in period_groups.items():
            category_counts = {}
            for ticket in period_tickets:
                category = ticket.get("category", "unknown")
                category_counts[category] = category_counts.get(category, 0) + 1

            category_trends[period_key] = category_counts

        return {
            "category_trends": category_trends,
            "emerging_categories": self._identify_emerging_categories(category_trends),
            "declining_categories": self._identify_declining_categories(category_trends)
        }

    def _analyze_severity_trends(self, tickets: List[Dict[str, Any]], period: str) -> Dict[str, Any]:
        """Analyze severity trends over time"""
        period_groups = self._group_tickets_by_period(tickets, period)

        severity_trends = {}
        for period_key, period_tickets in period_groups.items():
            severity_counts = {}
            for ticket in period_tickets:
                severity = ticket.get("severity", "unknown")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

            severity_trends[period_key] = severity_counts

        return {
            "severity_trends": severity_trends,
            "severity_trend": self._calculate_severity_trend(severity_trends)
        }

    def _analyze_resolution_trends(self, tickets: List[Dict[str, Any]], period: str) -> Dict[str, Any]:
        """Analyze resolution time trends"""
        period_groups = self._group_tickets_by_period(tickets, period)

        resolution_trends = {}
        for period_key, period_tickets in period_groups.items():
            resolution_times = [t.get("resolution_time_hours", 0) for t in period_tickets if t.get("resolution_time_hours")]
            if resolution_times:
                resolution_trends[period_key] = sum(resolution_times) / len(resolution_times)
            else:
                resolution_trends[period_key] = 0

        return {
            "resolution_trends": resolution_trends,
            "resolution_trend": "improving" if resolution_trends and list(resolution_trends.values())[-1] < list(resolution_trends.values())[0] else "worsening"
        }

    def _identify_emerging_issues(self, tickets: List[Dict[str, Any]], period: str) -> List[Dict[str, Any]]:
        """Identify emerging issues based on recent trends"""
        # Simple implementation - look for issues that appear more frequently in recent periods
        period_groups = self._group_tickets_by_period(tickets, period)

        if len(period_groups) < 2:
            return []

        periods = list(period_groups.keys())
        recent_period = periods[-1]
        earlier_periods = periods[:-1]

        recent_issues = self._extract_issue_patterns(period_groups[recent_period])
        earlier_issues = {}
        for period in earlier_periods:
            period_issues = self._extract_issue_patterns(period_groups[period])
            for issue, count in period_issues.items():
                earlier_issues[issue] = earlier_issues.get(issue, 0) + count

        emerging_issues = []
        for issue, recent_count in recent_issues.items():
            earlier_count = earlier_issues.get(issue, 0)
            if recent_count > earlier_count * 2 and recent_count >= 2:  # At least doubled and 2+ occurrences
                emerging_issues.append({
                    "issue": issue,
                    "recent_count": recent_count,
                    "earlier_count": earlier_count,
                    "growth_rate": (recent_count - earlier_count) / max(earlier_count, 1)
                })

        return emerging_issues

    def _group_tickets_by_period(self, tickets: List[Dict[str, Any]], period: str) -> Dict[str, List[Dict[str, Any]]]:
        """Group tickets by time period"""
        # Mock implementation - would parse actual dates
        return {"period_1": tickets[:len(tickets)//2], "period_2": tickets[len(tickets)//2:]}

    def _calculate_volume_volatility(self, volumes: List[int]) -> float:
        """Calculate volume volatility"""
        if len(volumes) < 2:
            return 0

        mean = sum(volumes) / len(volumes)
        variance = sum((v - mean) ** 2 for v in volumes) / len(volumes)
        return (variance ** 0.5) / max(mean, 1)

    def _identify_emerging_categories(self, category_trends: Dict[str, Dict[str, int]]) -> List[str]:
        """Identify categories that are emerging"""
        # Simple implementation
        return []

    def _identify_declining_categories(self, category_trends: Dict[str, Dict[str, int]]) -> List[str]:
        """Identify categories that are declining"""
        # Simple implementation
        return []

    def _calculate_severity_trend(self, severity_trends: Dict[str, Dict[str, int]]) -> str:
        """Calculate overall severity trend"""
        return "stable"  # Mock implementation

    def _extract_issue_patterns(self, tickets: List[Dict[str, Any]]) -> Dict[str, int]:
        """Extract issue patterns from tickets"""
        patterns = {}
        for ticket in tickets:
            issue = f"{ticket.get('category', 'unknown')}:{ticket.get('subject', 'unknown')}"
            patterns[issue] = patterns.get(issue, 0) + 1
        return patterns

    def _determine_overall_trend(self, volume_trends: Dict[str, Any], severity_trends: Dict[str, Any]) -> str:
        """Determine overall support trend"""
        volume_trend = volume_trends.get("trend", "stable")
        severity_trend = severity_trends.get("severity_trend", "stable")

        if volume_trend == "increasing" and severity_trend in ["stable", "worsening"]:
            return "worsening"
        elif volume_trend == "decreasing" and severity_trend in ["stable", "improving"]:
            return "improving"
        else:
            return "stable"

    def _generate_trend_insights(self, volume_trends: Dict[str, Any], category_trends: Dict[str, Any], severity_trends: Dict[str, Any]) -> List[str]:
        """Generate insights from trend analysis"""
        insights = []

        if volume_trends.get("trend") == "increasing":
            insights.append("Support ticket volume is increasing - investigate causes")

        if volume_trends.get("volatility", 0) > 0.5:
            insights.append("High ticket volume volatility indicates inconsistent support needs")

        return insights

    def _generate_trend_recommendations(self, volume_trends: Dict[str, Any], emerging_issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on trends"""
        recommendations = []

        if volume_trends.get("trend") == "increasing":
            recommendations.append("Implement proactive support strategies to reduce ticket volume")

        if emerging_issues:
            recommendations.append(f"Address {len(emerging_issues)} emerging issues promptly")

        return recommendations

    def _calculate_ticket_volatility(self, tickets: List[Dict[str, Any]]) -> float:
        """Calculate ticket volume volatility"""
        # Group by day and calculate daily volumes
        daily_volumes = {}
        for ticket in tickets:
            date = ticket.get("created_date", "unknown")
            daily_volumes[date] = daily_volumes.get(date, 0) + 1

        volumes = list(daily_volumes.values())
        return self._calculate_volume_volatility(volumes)

    def _generate_health_insights(self, ticket_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate health-related insights from ticket analysis"""
        insights = []

        health_score = ticket_analysis.get("health_score", 0)
        if health_score < 0.6:
            insights.append({
                "type": "health",
                "priority": "high",
                "title": "Poor Support Health Score",
                "description": f"Support health score is {health_score:.1%}, indicating significant issues",
                "recommendation": "Review support processes and implement immediate improvements"
            })

        return insights

    def _generate_recurrence_insights(self, recurring_issues: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights about recurring issues"""
        insights = []

        recurrence_rate = recurring_issues.get("recurrence_metrics", {}).get("recurrence_rate", 0)
        if recurrence_rate > 0.3:
            insights.append({
                "type": "recurrence",
                "priority": "high",
                "title": "High Issue Recurrence",
                "description": f"{recurrence_rate:.1%} of tickets are recurring issues",
                "recommendation": "Implement permanent fixes for recurring problems"
            })

        return insights

    def _generate_satisfaction_insights(self, satisfaction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights about client satisfaction"""
        insights = []

        satisfaction_score = satisfaction.get("satisfaction_score", 0)
        if satisfaction_score < 0.6:
            insights.append({
                "type": "satisfaction",
                "priority": "high",
                "title": "Low Client Satisfaction",
                "description": f"Client satisfaction score is {satisfaction_score:.1%}",
                "recommendation": "Implement customer satisfaction improvement initiatives"
            })

        return insights

    def _generate_trend_insights(self, trends: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights from trend analysis"""
        insights = []

        overall_trend = trends.get("overall_trend", "stable")
        if overall_trend == "worsening":
            insights.append({
                "type": "trends",
                "priority": "medium",
                "title": "Worsening Support Trends",
                "description": "Support ticket trends are worsening over time",
                "recommendation": "Investigate root causes and implement corrective measures"
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