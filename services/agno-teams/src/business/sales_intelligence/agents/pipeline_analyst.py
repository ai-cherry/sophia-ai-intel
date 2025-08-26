"""
Pipeline Analyst Agent - Analyzes sales pipeline health and identifies opportunities
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import statistics
import logging

from agno import Agent
from agno.tools import tool

# Configure logging
logger = logging.getLogger(__name__)

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
        self.crm_config = crm_config
        self.salesforce_url = crm_config["salesforce"]["url"]
        self.hubspot_url = crm_config["hubspot"]["url"]

        # Cache for performance
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes

    def _create_tools(self) -> List[Any]:
        """Create tools for pipeline analysis"""
        return [
            self.fetch_pipeline_data,
            self.analyze_pipeline_health,
            self.identify_bottlenecks,
            self.calculate_pipeline_coverage,
            self.analyze_stage_conversions,
            self.detect_anomalies
        ]

    @tool("fetch_pipeline_data")
    async def fetch_pipeline_data(
        self,
        time_period: str = "current_quarter",
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fetch comprehensive pipeline data from all CRM sources"""
        # Check cache first
        cache_key = f"pipeline_{time_period}_{str(filters)}"
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            if (datetime.now() - cached_data["timestamp"]).seconds < self._cache_timeout:
                return cached_data["data"]

        # Determine date range
        date_range = self._calculate_date_range(time_period)

        try:
            # Fetch from multiple sources in parallel
            sf_task = self._fetch_salesforce_data(date_range, filters)
            hs_task = self._fetch_hubspot_data(date_range, filters)

            sf_data, hs_data = await asyncio.gather(sf_task, hs_task)

            # Merge and normalize data
            merged_pipeline = self._merge_pipeline_data(sf_data, hs_data)

            # Calculate key metrics
            metrics = self._calculate_pipeline_metrics(merged_pipeline)

            result = {
                "deals": merged_pipeline,
                "metrics": metrics,
                "date_range": date_range,
                "total_value": sum(d["amount"] for d in merged_pipeline),
                "deal_count": len(merged_pipeline)
            }

            # Cache the result
            self._cache[cache_key] = {
                "data": result,
                "timestamp": datetime.now()
            }

            return result

        except Exception as e:
            logger.error(f"Error fetching pipeline data: {e}")
            return {
                "deals": [],
                "metrics": {},
                "date_range": date_range,
                "total_value": 0,
                "deal_count": 0,
                "error": str(e)
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
        coverage = await self.calculate_pipeline_coverage(
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

    @tool("calculate_pipeline_coverage")
    async def calculate_pipeline_coverage(
        self,
        total_value: float
    ) -> Dict[str, Any]:
        """Calculate pipeline coverage against quota"""
        try:
            # Fetch quota data (this would come from CRM or separate system)
            quota = await self._fetch_quota_data()

            if quota <= 0:
                return {
                    "score": 50,
                    "status": "unknown",
                    "ratio": 0,
                    "message": "Unable to determine quota"
                }

            ratio = total_value / quota

            if ratio >= 3.0:  # 3x coverage is excellent
                score = 100
                status = "excellent"
            elif ratio >= 2.0:  # 2x coverage is good
                score = 80
                status = "good"
            elif ratio >= 1.5:  # 1.5x coverage is adequate
                score = 60
                status = "adequate"
            elif ratio >= 1.0:  # 1x coverage is minimum
                score = 40
                status = "minimum"
            else:  # Less than 1x coverage is critical
                score = 20
                status = "critical"

            return {
                "score": score,
                "status": status,
                "ratio": ratio,
                "total_value": total_value,
                "quota": quota
            }

        except Exception as e:
            logger.error(f"Error calculating pipeline coverage: {e}")
            return {
                "score": 50,
                "status": "unknown",
                "ratio": 0,
                "message": f"Error: {str(e)}"
            }

    @tool("analyze_stage_conversions")
    async def analyze_stage_conversions(
        self,
        deals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze conversion rates between stages"""
        stage_order = [
            "prospect", "qualification", "discovery", "demo",
            "proposal", "negotiation", "closing", "closed_won"
        ]

        stage_counts = {}
        for deal in deals:
            stage = deal.get("stage", "unknown")
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

        conversions = {}
        for i, stage in enumerate(stage_order[:-1]):
            current_count = stage_counts.get(stage, 0)
            next_count = stage_counts.get(stage_order[i + 1], 0)

            if current_count > 0:
                conversion_rate = next_count / current_count
            else:
                conversion_rate = 0

            # Calculate stuck deals (deals in stage > 30 days)
            stuck_count = sum(1 for deal in deals
                            if deal.get("stage") == stage
                            and self._days_in_stage(deal) > 30)

            conversions[stage] = {
                "conversion_rate": conversion_rate,
                "current_count": current_count,
                "next_count": next_count,
                "stuck_count": stuck_count,
                "avg_days": self._calculate_avg_days_in_stage(deals, stage)
            }

        return conversions

    @tool("detect_anomalies")
    async def detect_anomalies(
        self,
        pipeline_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in pipeline data"""
        deals = pipeline_data["deals"]
        anomalies = []

        # Check for unusually large deals
        amounts = [d["amount"] for d in deals if "amount" in d]
        if amounts:
            q75, q25 = statistics.quantiles(amounts, n=4)[2], statistics.quantiles(amounts, n=4)[0]
            iqr = q75 - q25
            upper_bound = q75 + (1.5 * iqr)

            large_deals = [d for d in deals if d.get("amount", 0) > upper_bound]
            if large_deals:
                anomalies.append({
                    "type": "large_deals",
                    "severity": "medium",
                    "description": f"Found {len(large_deals)} unusually large deals",
                    "deals": large_deals,
                    "recommendation": "Review large deals for accuracy and risk"
                })

        # Check for deals stuck too long
        very_stuck_deals = [d for d in deals if self._days_in_stage(d) > 90]
        if very_stuck_deals:
            anomalies.append({
                "type": "very_stuck_deals",
                "severity": "high",
                "description": f"Found {len(very_stuck_deals)} deals stuck >90 days",
                "deals": very_stuck_deals,
                "recommendation": "Urgently review and either advance or disqualify"
            })

        # Check for sudden drops in pipeline value
        # This would compare with historical data

        return anomalies

    def _calculate_date_range(self, time_period: str) -> Dict[str, str]:
        """Calculate date range for the given time period"""
        now = datetime.now()

        if time_period == "current_quarter":
            quarter = ((now.month - 1) // 3) + 1
            year = now.year
            start_month = (quarter - 1) * 3 + 1
            start_date = datetime(year, start_month, 1)
            end_date = datetime(year, start_month + 2, 31) if start_month + 2 <= 12 else datetime(year + 1, (start_month + 2) % 12, 31)
        elif time_period == "last_quarter":
            quarter = ((now.month - 1) // 3) + 1
            year = now.year if quarter > 1 else now.year - 1
            quarter = quarter - 1 if quarter > 1 else 4
            start_month = (quarter - 1) * 3 + 1
            start_date = datetime(year, start_month, 1)
            end_date = datetime(year, start_month + 2, 31) if start_month + 2 <= 12 else datetime(year + 1, (start_month + 2) % 12, 31)
        elif time_period == "current_year":
            start_date = datetime(now.year, 1, 1)
            end_date = datetime(now.year, 12, 31)
        else:  # last_30_days
            start_date = now - timedelta(days=30)
            end_date = now

        return {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d")
        }

    async def _fetch_salesforce_data(
        self,
        date_range: Dict[str, str],
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch data from Salesforce"""
        # This would make actual API calls to Salesforce
        # For now, return mock data
        return [
            {
                "id": "SF001",
                "name": "Acme Corp Deal",
                "amount": 50000,
                "stage": "negotiation",
                "created_date": "2024-01-15",
                "last_modified": "2024-02-01",
                "owner": "John Doe",
                "probability": 75
            }
        ]

    async def _fetch_hubspot_data(
        self,
        date_range: Dict[str, str],
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch data from HubSpot"""
        # This would make actual API calls to HubSpot
        # For now, return mock data
        return [
            {
                "id": "HS001",
                "name": "Tech Startup Deal",
                "amount": 25000,
                "stage": "demo",
                "created_date": "2024-01-20",
                "last_modified": "2024-02-05",
                "owner": "Jane Smith",
                "probability": 60
            }
        ]

    def _merge_pipeline_data(
        self,
        sf_data: List[Dict[str, Any]],
        hs_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Merge and normalize data from different CRM sources"""
        merged = []

        # Add source identifier and normalize field names
        for deal in sf_data:
            normalized = {
                "id": deal["id"],
                "name": deal["name"],
                "amount": deal["amount"],
                "stage": deal["stage"],
                "created_date": deal["created_date"],
                "last_modified": deal["last_modified"],
                "owner": deal["owner"],
                "probability": deal.get("probability", 0),
                "source": "salesforce"
            }
            merged.append(normalized)

        for deal in hs_data:
            normalized = {
                "id": deal["id"],
                "name": deal["name"],
                "amount": deal["amount"],
                "stage": deal["stage"],
                "created_date": deal["created_date"],
                "last_modified": deal["last_modified"],
                "owner": deal["owner"],
                "probability": deal.get("probability", 0),
                "source": "hubspot"
            }
            merged.append(normalized)

        return merged

    def _calculate_pipeline_metrics(self, deals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate key pipeline metrics"""
        if not deals:
            return {}

        amounts = [d["amount"] for d in deals if "amount" in d]
        probabilities = [d.get("probability", 0) for d in deals]

        return {
            "total_deals": len(deals),
            "total_value": sum(amounts),
            "avg_deal_size": statistics.mean(amounts) if amounts else 0,
            "median_deal_size": statistics.median(amounts) if amounts else 0,
            "weighted_value": sum(a * p / 100 for a, p in zip(amounts, probabilities)),
            "avg_probability": statistics.mean(probabilities) if probabilities else 0
        }

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
            if stage in ["prospect", "qualification", "discovery", "demo"]
        )
        late_stage = sum(
            count for stage, count in stage_counts.items()
            if stage in ["proposal", "negotiation", "closing"]
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

    def _calculate_deal_velocity(self, deals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate average deal velocity"""
        if not deals:
            return {"score": 0, "status": "unknown", "days": 0}

        days_in_pipeline = [self._days_in_stage(deal) for deal in deals]
        avg_days = statistics.mean(days_in_pipeline) if days_in_pipeline else 0

        if avg_days <= 30:  # Fast velocity
            score = 100
            status = "excellent"
        elif avg_days <= 60:  # Good velocity
            score = 80
            status = "good"
        elif avg_days <= 90:  # Moderate velocity
            score = 60
            status = "moderate"
        else:  # Slow velocity
            score = 30
            status = "slow"

        return {
            "score": score,
            "status": status,
            "days": avg_days
        }

    async def _analyze_win_rate_trend(self) -> Dict[str, Any]:
        """Analyze win rate trends"""
        # This would fetch historical win rate data
        # For now, return mock analysis
        return {
            "score": 75,
            "status": "stable",
            "message": "Win rate stable at 45%",
            "trend": "stable",
            "current_rate": 0.45,
            "previous_rate": 0.42
        }

    def _find_stuck_deals(self, deals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find deals that have been stuck in the same stage for too long"""
        stuck_deals = []

        for deal in deals:
            days = self._days_in_stage(deal)
            if days > 60:  # Stuck for more than 60 days
                stuck_deals.append({
                    **deal,
                    "days_stuck": days
                })

        return sorted(stuck_deals, key=lambda x: x["days_stuck"], reverse=True)

    def _analyze_rep_performance(self, deals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance by sales rep"""
        rep_stats = {}

        for deal in deals:
            rep = deal.get("owner", "unknown")
            if rep not in rep_stats:
                rep_stats[rep] = {
                    "deal_count": 0,
                    "total_value": 0,
                    "weighted_value": 0,
                    "avg_probability": 0
                }

            rep_stats[rep]["deal_count"] += 1
            rep_stats[rep]["total_value"] += deal.get("amount", 0)
            rep_stats[rep]["weighted_value"] += deal.get("amount", 0) * deal.get("probability", 0) / 100

        # Calculate performance index
        for rep, stats in rep_stats.items():
            if stats["deal_count"] > 0:
                stats["avg_deal_size"] = stats["total_value"] / stats["deal_count"]
                stats["performance_index"] = min(stats["weighted_value"] / 100000, 1.0)  # Normalize to quota

        return rep_stats

    def _days_in_stage(self, deal: Dict[str, Any]) -> int:
        """Calculate days a deal has been in current stage"""
        last_modified = deal.get("last_modified", deal.get("created_date"))
        if not last_modified:
            return 0

        try:
            modified_date = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
            return (datetime.now() - modified_date).days
        except:
            return 0

    def _calculate_avg_days_in_stage(
        self,
        deals: List[Dict[str, Any]],
        stage: str
    ) -> float:
        """Calculate average days deals have been in a specific stage"""
        stage_deals = [d for d in deals if d.get("stage") == stage]
        if not stage_deals:
            return 0

        days = [self._days_in_stage(deal) for deal in stage_deals]
        return statistics.mean(days) if days else 0

    def _get_health_status(self, score: float) -> str:
        """Convert health score to status"""
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "warning"
        else:
            return "critical"

    def _generate_health_recommendations(
        self,
        health_factors: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on health factors"""
        recommendations = []

        for factor in health_factors:
            if factor["status"] == "critical":
                if factor["factor"] == "pipeline_coverage":
                    recommendations.append("Increase pipeline coverage by adding more qualified opportunities")
                elif factor["factor"] == "stage_distribution":
                    recommendations.append("Balance pipeline by focusing on lead generation and qualification")
                elif factor["factor"] == "deal_velocity":
                    recommendations.append("Improve deal velocity by streamlining sales process")
                elif factor["factor"] == "win_rate_trend":
                    recommendations.append("Address declining win rate through improved qualification")

        if not recommendations:
            recommendations.append("Maintain current strong pipeline performance")

        return recommendations

    async def _fetch_quota_data(self) -> float:
        """Fetch quota data from CRM or external system"""
        # This would make API calls to get quota data
        # For now, return a mock quota
        return 1000000.0  # $1M annual quota