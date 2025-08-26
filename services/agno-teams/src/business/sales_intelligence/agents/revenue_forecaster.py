"""
Revenue Forecaster Agent - Predicts revenue outcomes and win probabilities
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import statistics

from agno import Agent
from agno.tools import tool

logger = logging.getLogger(__name__)

class RevenueForecastAgent(Agent):
    """Predicts revenue outcomes and provides forecasting insights"""

    def __init__(self, name: str, crm_config: Dict[str, Any]):
        super().__init__(
            name=name,
            role="""I am a Revenue Forecaster responsible for:
            - Predicting deal win probabilities using advanced analytics
            - Forecasting revenue based on pipeline data
            - Analyzing historical trends and patterns
            - Providing confidence intervals for forecasts
            - Identifying factors that influence outcomes
            """,
            tools=self._create_tools()
        )

        self.crm_config = crm_config
        self.forecast_models = {}
        self.historical_data = []

    def _create_tools(self) -> List[Any]:
        """Create tools for revenue forecasting"""
        return [
            self.predict_win_probability,
            self.forecast_pipeline_revenue,
            self.analyze_historical_trends,
            self.calculate_confidence_intervals,
            self.identify_revenue_drivers
        ]

    @tool("predict_win_probability")
    async def predict_win_probability(
        self,
        deal_id: str,
        deal_score: float
    ) -> float:
        """Predict win probability for a specific deal"""
        try:
            # Get deal details
            deal_data = await self._get_deal_details(deal_id)

            if not deal_data:
                # Fallback to score-based prediction
                return self._score_based_prediction(deal_score)

            # Extract features for ML prediction
            features = self._extract_deal_features(deal_data)

            # Use trained model or rule-based prediction
            if deal_id in self.forecast_models:
                probability = self.forecast_models[deal_id].predict([features])[0]
            else:
                probability = self._calculate_ml_probability(features, deal_score)

            # Ensure probability is within reasonable bounds
            probability = max(0.01, min(0.99, probability))

            logger.info(f"Predicted win probability for deal {deal_id}: {probability:.1%}")

            return probability

        except Exception as e:
            logger.error(f"Error predicting win probability for {deal_id}: {e}")
            return self._score_based_prediction(deal_score)

    @tool("forecast_pipeline_revenue")
    async def forecast_pipeline_revenue(
        self,
        pipeline_data: Dict[str, Any],
        time_horizon: int = 90,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """Forecast revenue from pipeline data"""
        try:
            deals = pipeline_data.get("deals", [])

            if not deals:
                return {"error": "No deals in pipeline"}

            # Calculate base forecast
            base_forecast = await self._calculate_base_forecast(deals, time_horizon)

            # Calculate confidence intervals
            confidence_intervals = self._calculate_forecast_confidence(
                base_forecast, confidence_level
            )

            # Generate scenarios
            scenarios = await self._generate_forecast_scenarios(base_forecast)

            # Identify key drivers
            drivers = self._identify_forecast_drivers(deals)

            forecast = {
                "base_forecast": base_forecast,
                "confidence_intervals": confidence_intervals,
                "scenarios": scenarios,
                "key_drivers": drivers,
                "methodology": {
                    "time_horizon": time_horizon,
                    "confidence_level": confidence_level,
                    "deals_analyzed": len(deals),
                    "model_type": "weighted_probability"
                },
                "assumptions": [
                    "Historical conversion rates hold",
                    "No significant market changes",
                    "Current pipeline accurately reflects reality"
                ]
            }

            return forecast

        except Exception as e:
            logger.error(f"Error forecasting pipeline revenue: {e}")
            return {"error": str(e)}

    @tool("analyze_historical_trends")
    async def analyze_historical_trends(
        self,
        metric: str = "win_rate",
        time_period: str = "last_12_months"
    ) -> Dict[str, Any]:
        """Analyze historical trends for forecasting"""
        try:
            # Fetch historical data
            historical_data = await self._fetch_historical_data(metric, time_period)

            if not historical_data:
                return {"error": "No historical data available"}

            # Analyze trends
            trend_analysis = self._analyze_trends(historical_data)

            # Calculate seasonality
            seasonality = self._calculate_seasonality(historical_data)

            # Identify patterns
            patterns = self._identify_patterns(historical_data)

            return {
                "metric": metric,
                "time_period": time_period,
                "trend": trend_analysis,
                "seasonality": seasonality,
                "patterns": patterns,
                "forecast_implications": self._generate_forecast_implications(
                    trend_analysis, seasonality, patterns
                )
            }

        except Exception as e:
            logger.error(f"Error analyzing historical trends: {e}")
            return {"error": str(e)}

    @tool("calculate_confidence_intervals")
    async def calculate_confidence_intervals(
        self,
        forecast: Dict[str, Any],
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """Calculate confidence intervals for forecasts"""
        try:
            base_forecast = forecast.get("base_forecast", 0)

            # Calculate standard deviation based on historical variance
            historical_variance = await self._get_historical_variance()

            # Use normal distribution for confidence intervals
            import math
            z_score = 1.96 if confidence_level == 0.95 else 2.58  # 99% confidence

            margin_of_error = z_score * math.sqrt(historical_variance)

            return {
                "lower_bound": max(0, base_forecast - margin_of_error),
                "upper_bound": base_forecast + margin_of_error,
                "margin_of_error": margin_of_error,
                "confidence_level": confidence_level,
                "methodology": "Normal distribution with historical variance"
            }

        except Exception as e:
            logger.error(f"Error calculating confidence intervals: {e}")
            return {
                "lower_bound": base_forecast * 0.8,
                "upper_bound": base_forecast * 1.2,
                "margin_of_error": base_forecast * 0.2,
                "confidence_level": confidence_level,
                "methodology": "Simple range estimation"
            }

    @tool("identify_revenue_drivers")
    async def identify_revenue_drivers(
        self,
        pipeline_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify key drivers of revenue performance"""
        try:
            deals = pipeline_data.get("deals", [])

            drivers = []

            # Analyze deal size impact
            size_impact = self._analyze_deal_size_impact(deals)
            if size_impact["significance"] > 0.7:
                drivers.append({
                    "driver": "deal_size",
                    "impact": size_impact["correlation"],
                    "description": "Larger deals significantly impact revenue",
                    "recommendation": "Focus on high-value opportunities"
                })

            # Analyze stage conversion impact
            stage_impact = self._analyze_stage_conversion_impact(deals)
            if stage_impact["bottleneck_stages"]:
                drivers.append({
                    "driver": "stage_conversion",
                    "impact": "high",
                    "description": f"Conversion bottlenecks in {', '.join(stage_impact['bottleneck_stages'])}",
                    "recommendation": "Improve conversion rates in identified stages"
                })

            # Analyze rep performance impact
            rep_impact = self._analyze_rep_performance_impact(deals)
            if rep_impact["variance"] > 0.3:
                drivers.append({
                    "driver": "rep_performance",
                    "impact": "high",
                    "description": "Significant variance in rep performance",
                    "recommendation": "Coach underperforming reps and share best practices"
                })

            # Analyze time-to-close impact
            time_impact = self._analyze_time_to_close_impact(deals)
            if time_impact["correlation"] > 0.5:
                drivers.append({
                    "driver": "sales_cycle",
                    "impact": time_impact["correlation"],
                    "description": "Faster sales cycles correlate with higher win rates",
                    "recommendation": "Streamline sales process to reduce cycle time"
                })

            return drivers

        except Exception as e:
            logger.error(f"Error identifying revenue drivers: {e}")
            return []

    async def _get_deal_details(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed deal information"""
        # Mock implementation - would fetch from CRM
        return {
            "id": deal_id,
            "amount": 50000,
            "stage": "negotiation",
            "age": 45,  # days
            "competitors": 1,
            "decision_makers": 2,
            "budget_confirmed": True,
            "relationship_strength": "strong"
        }

    def _score_based_prediction(self, score: float) -> float:
        """Fallback prediction based on deal score"""
        if score >= 0.8:
            return 0.75
        elif score >= 0.6:
            return 0.5
        elif score >= 0.4:
            return 0.25
        else:
            return 0.1

    def _extract_deal_features(self, deal_data: Dict[str, Any]) -> List[float]:
        """Extract features for ML prediction"""
        return [
            deal_data.get("amount", 0) / 100000,  # Normalize amount
            deal_data.get("age", 30) / 90,  # Normalize age
            len(deal_data.get("competitors", [])),  # Number of competitors
            deal_data.get("decision_makers", 1),  # Number of decision makers
            1.0 if deal_data.get("budget_confirmed", False) else 0.0,  # Budget confirmed
            self._relationship_strength_score(deal_data.get("relationship_strength", "medium"))
        ]

    def _relationship_strength_score(self, strength: str) -> float:
        """Convert relationship strength to numerical score"""
        scores = {
            "excellent": 1.0,
            "strong": 0.8,
            "good": 0.6,
            "medium": 0.5,
            "weak": 0.3,
            "poor": 0.1
        }
        return scores.get(strength.lower(), 0.5)

    def _calculate_ml_probability(self, features: List[float], deal_score: float) -> float:
        """Calculate win probability using simplified ML approach"""
        # Simple weighted combination of features
        weights = [0.2, -0.1, -0.2, 0.1, 0.3, 0.2]  # Based on feature importance

        # Calculate weighted sum
        score = sum(w * f for w, f in zip(weights, features))

        # Add deal score influence
        score = score * 0.7 + deal_score * 0.3

        # Apply sigmoid function
        import math
        probability = 1 / (1 + math.exp(-score))

        return probability

    async def _calculate_base_forecast(
        self,
        deals: List[Dict[str, Any]],
        time_horizon: int
    ) -> float:
        """Calculate base revenue forecast"""
        total_forecast = 0.0

        for deal in deals:
            # Get or calculate win probability
            deal_score = deal.get("score", 0.5)
            win_prob = await self.predict_win_probability(deal["id"], deal_score)

            # Apply time decay for longer-term deals
            time_decay = self._calculate_time_decay(deal, time_horizon)

            # Calculate expected revenue
            expected_revenue = deal.get("amount", 0) * win_prob * time_decay
            total_forecast += expected_revenue

        return total_forecast

    def _calculate_time_decay(self, deal: Dict[str, Any], time_horizon: int) -> float:
        """Calculate time-based decay factor"""
        deal_age = deal.get("age", 30)  # days

        if deal_age <= time_horizon:
            return 1.0  # Deal can close within horizon
        elif deal_age <= time_horizon * 1.5:
            return 0.7  # Deal might close within extended horizon
        else:
            return 0.3  # Deal unlikely to close within horizon

    def _calculate_forecast_confidence(
        self,
        base_forecast: float,
        confidence_level: float
    ) -> Dict[str, Any]:
        """Calculate confidence intervals for forecast"""
        # Use historical variance to estimate uncertainty
        variance_factor = 0.2  # 20% variance based on historical data

        margin = base_forecast * variance_factor

        if confidence_level == 0.95:
            z_score = 1.96
        elif confidence_level == 0.99:
            z_score = 2.58
        else:
            z_score = 1.645  # 90% confidence

        margin_of_error = z_score * (base_forecast * variance_factor)

        return {
            "lower_bound": max(0, base_forecast - margin_of_error),
            "upper_bound": base_forecast + margin_of_error,
            "margin_of_error": margin_of_error,
            "confidence_level": confidence_level
        }

    async def _generate_forecast_scenarios(self, base_forecast: float) -> Dict[str, Any]:
        """Generate optimistic, pessimistic, and realistic scenarios"""
        # Base variance factors
        optimistic_factor = 1.3
        pessimistic_factor = 0.7
        realistic_factor = 1.0

        # Adjust based on historical performance
        historical_adjustment = await self._get_historical_adjustment()

        return {
            "optimistic": base_forecast * optimistic_factor * historical_adjustment,
            "realistic": base_forecast * realistic_factor * historical_adjustment,
            "pessimistic": base_forecast * pessimistic_factor * historical_adjustment,
            "methodology": "Scenario analysis with historical adjustment"
        }

    async def _fetch_historical_data(self, metric: str, time_period: str) -> List[float]:
        """Fetch historical data for trend analysis"""
        # Mock historical data
        if metric == "win_rate":
            return [0.25, 0.28, 0.32, 0.35, 0.38, 0.42, 0.39, 0.41, 0.44, 0.46, 0.43, 0.45]
        elif metric == "revenue":
            return [850000, 920000, 880000, 950000, 1020000, 980000, 1050000, 1100000, 1080000, 1120000, 1150000, 1180000]
        else:
            return []

    def _analyze_trends(self, data: List[float]) -> Dict[str, Any]:
        """Analyze trends in historical data"""
        if len(data) < 3:
            return {"trend": "insufficient_data", "slope": 0, "confidence": 0}

        # Calculate linear trend
        n = len(data)
        x = list(range(n))

        # Simple linear regression
        slope = self._calculate_slope(x, data)
        intercept = sum(data)/n - slope * sum(x)/n

        # Determine trend direction
        if slope > 0.01:
            trend = "increasing"
        elif slope < -0.01:
            trend = "decreasing"
        else:
            trend = "stable"

        # Calculate R-squared for confidence
        y_pred = [slope * xi + intercept for xi in x]
        ss_res = sum((yi - ypi)**2 for yi, ypi in zip(data, y_pred))
        ss_tot = sum((yi - sum(data)/n)**2 for yi in data)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        return {
            "trend": trend,
            "slope": slope,
            "confidence": r_squared,
            "description": f"Data shows {trend} trend with {r_squared:.1%} confidence"
        }

    def _calculate_slope(self, x: List[int], y: List[float]) -> float:
        """Calculate slope of linear regression"""
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi**2 for xi in x)

        denominator = n * sum_x2 - sum_x**2
        if denominator == 0:
            return 0

        return (n * sum_xy - sum_x * sum_y) / denominator

    def _calculate_seasonality(self, data: List[float]) -> Dict[str, Any]:
        """Calculate seasonal patterns"""
        if len(data) < 12:
            return {"seasonal": False, "pattern": "insufficient_data"}

        # Simple quarterly seasonality check
        quarters = [data[i:i+3] for i in range(0, len(data), 3)]
        quarter_avgs = [sum(q)/len(q) for q in quarters if q]

        if len(quarter_avgs) >= 4:
            seasonal = max(quarter_avgs) / min(quarter_avgs) > 1.2
            return {
                "seasonal": seasonal,
                "pattern": "quarterly" if seasonal else "none",
                "peak_quarter": quarter_avgs.index(max(quarter_avgs)) + 1 if seasonal else None
            }

        return {"seasonal": False, "pattern": "insufficient_data"}

    def _identify_patterns(self, data: List[float]) -> List[str]:
        """Identify patterns in the data"""
        patterns = []

        # Check for consistent growth
        if len(data) >= 6:
            recent_trend = self._analyze_trends(data[-6:])["trend"]
            if recent_trend == "increasing":
                patterns.append("Recent growth trend")

        # Check for volatility
        if len(data) >= 5:
            volatility = statistics.stdev(data) / statistics.mean(data)
            if volatility > 0.2:
                patterns.append("High volatility")
            elif volatility < 0.05:
                patterns.append("Stable performance")

        return patterns

    def _generate_forecast_implications(
        self,
        trend: Dict[str, Any],
        seasonality: Dict[str, Any],
        patterns: List[str]
    ) -> List[str]:
        """Generate forecast implications from analysis"""
        implications = []

        if trend["trend"] == "increasing":
            implications.append("Positive trend suggests higher future performance")
        elif trend["trend"] == "decreasing":
            implications.append("Negative trend requires attention and corrective action")

        if seasonality["seasonal"]:
            peak_quarter = seasonality.get("peak_quarter")
            if peak_quarter:
                implications.append(f"Seasonal peak in Q{peak_quarter} - plan resources accordingly")

        if "High volatility" in patterns:
            implications.append("High volatility increases forecast uncertainty")

        if "Recent growth trend" in patterns:
            implications.append("Recent growth suggests upward revision to forecasts")

        return implications

    async def _get_historical_variance(self) -> float:
        """Get historical variance for confidence calculations"""
        # Mock implementation
        return 0.15  # 15% historical variance

    async def _get_historical_adjustment(self) -> float:
        """Get historical adjustment factor"""
        # Mock implementation
        return 1.05  # 5% upward adjustment based on recent performance

    def _analyze_deal_size_impact(self, deals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze impact of deal size on revenue"""
        if not deals:
            return {"correlation": 0, "significance": 0}

        amounts = [d.get("amount", 0) for d in deals]
        # Mock correlation analysis
        return {"correlation": 0.8, "significance": 0.9}

    def _analyze_stage_conversion_impact(self, deals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze stage conversion impact"""
        # Mock analysis
        return {"bottleneck_stages": ["negotiation", "proposal"]}

    def _analyze_rep_performance_impact(self, deals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze rep performance impact"""
        # Mock analysis
        return {"variance": 0.4}

    def _analyze_time_to_close_impact(self, deals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze time-to-close impact"""
        # Mock analysis
        return {"correlation": 0.6}