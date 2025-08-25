# Sophia AI Phase 3A: Self-Improvement & Learning - Detailed Implementation Plan

**Date**: August 25, 2025  
**Duration**: 2 Weeks (Weeks 9-10)  
**Priority**: HIGH - Following Phase 2B  
**Goal**: Implement self-improvement capabilities with learning loops, cost optimization, and quality assessment

## Executive Summary

Phase 3A introduces advanced self-improvement capabilities to the Sophia AI system, enabling continuous learning, performance optimization, and cost management. This phase implements reflection engines, automated retraining pipelines, and intelligent resource allocation based on usage patterns and performance metrics.

### Key Objectives
1. Implement Reflection Engine for continuous improvement
2. Create Cost Optimization based on usage patterns
3. Develop Performance Monitoring with automatic scaling
4. Build Quality Assessment and automated retraining systems
5. Enable Self-healing and error recovery mechanisms

## Self-Improvement Architecture

### Core Components

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| Reflection Engine | Analyze past performance | Pattern recognition, success/failure analysis |
| Cost Optimizer | Minimize API and resource costs | Model routing, caching, batch processing |
| Performance Monitor | Track system metrics | Auto-scaling, bottleneck detection |
| Quality Assessor | Evaluate output quality | Automated scoring, retraining triggers |
| Learning Pipeline | Continuous improvement | Feedback loops, model fine-tuning |

### Learning Feedback Loops

1. **User Feedback Loop**: Direct user ratings and corrections
2. **Performance Metrics Loop**: System performance indicators
3. **Cost Efficiency Loop**: Resource usage optimization
4. **Quality Assurance Loop**: Output quality monitoring
5. **Error Recovery Loop**: Failure pattern analysis

## Week 9: Core Learning Infrastructure

### Day 1-2: Reflection Engine

#### 9.1 Reflection Engine Base
```python
# services/learning-engine/src/reflection/reflection_engine.py
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
from collections import defaultdict
import json

from agno import Agent, Memory
from agno.monitoring import MetricsCollector

@dataclass
class ReflectionContext:
    """Context for reflection analysis"""
    request_id: str
    request_type: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    metadata: Dict[str, Any]
    performance_metrics: Dict[str, float]
    user_feedback: Optional[Dict[str, Any]] = None
    error_info: Optional[Dict[str, Any]] = None

@dataclass
class ReflectionInsight:
    """Insight from reflection analysis"""
    insight_type: str  # pattern, anomaly, optimization, error
    description: str
    impact_score: float  # 0-1, importance of insight
    actionable: bool
    recommended_actions: List[str]
    supporting_data: Dict[str, Any]

class ReflectionEngine:
    """Engine for analyzing past interactions and learning patterns"""
    
    def __init__(
        self,
        memory: Memory,
        metrics_collector: MetricsCollector,
        config: Optional[Dict[str, Any]] = None
    ):
        self.memory = memory
        self.metrics = metrics_collector
        self.config = config or self._default_config()
        
        # Pattern storage
        self.success_patterns = defaultdict(list)
        self.failure_patterns = defaultdict(list)
        self.optimization_opportunities = []
        
        # Learning state
        self.reflection_history = []
        self.applied_learnings = []
        
    def _default_config(self) -> Dict[str, Any]:
        """Default reflection configuration"""
        return {
            "batch_size": 100,
            "reflection_interval": 3600,  # 1 hour
            "pattern_threshold": 0.7,
            "min_sample_size": 10,
            "learning_rate": 0.1
        }
        
    async def reflect(
        self,
        time_window: Optional[timedelta] = None
    ) -> List[ReflectionInsight]:
        """Perform reflection on recent interactions"""
        if not time_window:
            time_window = timedelta(seconds=self.config["reflection_interval"])
            
        # Gather recent interactions
        interactions = await self._gather_recent_interactions(time_window)
        
        insights = []
        
        # Analyze success patterns
        success_insights = await self._analyze_success_patterns(interactions)
        insights.extend(success_insights)
        
        # Analyze failure patterns
        failure_insights = await self._analyze_failure_patterns(interactions)
        insights.extend(failure_insights)
        
        # Identify optimization opportunities
        optimization_insights = await self._identify_optimizations(interactions)
        insights.extend(optimization_insights)
        
        # Analyze cost patterns
        cost_insights = await self._analyze_cost_patterns(interactions)
        insights.extend(cost_insights)
        
        # Analyze quality trends
        quality_insights = await self._analyze_quality_trends(interactions)
        insights.extend(quality_insights)
        
        # Store reflection results
        reflection_result = {
            "timestamp": datetime.now(),
            "interactions_analyzed": len(interactions),
            "insights_generated": len(insights),
            "insights": insights
        }
        self.reflection_history.append(reflection_result)
        
        # Apply immediate learnings
        await self._apply_immediate_learnings(insights)
        
        return insights
        
    async def _analyze_success_patterns(
        self,
        interactions: List[ReflectionContext]
    ) -> List[ReflectionInsight]:
        """Identify patterns in successful interactions"""
        insights = []
        
        # Group by request type
        by_type = defaultdict(list)
        for interaction in interactions:
            if not interaction.error_info:  # Success
                by_type[interaction.request_type].append(interaction)
                
        # Analyze each type
        for req_type, successes in by_type.items():
            if len(successes) < self.config["min_sample_size"]:
                continue
                
            # Extract common patterns
            patterns = self._extract_patterns(successes)
            
            for pattern in patterns:
                if pattern["confidence"] > self.config["pattern_threshold"]:
                    insight = ReflectionInsight(
                        insight_type="pattern",
                        description=f"Success pattern identified for {req_type}",
                        impact_score=pattern["confidence"],
                        actionable=True,
                        recommended_actions=[
                            f"Optimize {req_type} requests using pattern",
                            "Update routing rules to leverage pattern",
                            "Create template based on successful approach"
                        ],
                        supporting_data={
                            "pattern": pattern,
                            "sample_size": len(successes),
                            "success_rate": len(successes) / len(interactions)
                        }
                    )
                    insights.append(insight)
                    
                    # Store pattern for future use
                    self.success_patterns[req_type].append(pattern)
                    
        return insights
        
    async def _analyze_failure_patterns(
        self,
        interactions: List[ReflectionContext]
    ) -> List[ReflectionInsight]:
        """Identify patterns in failed interactions"""
        insights = []
        
        # Extract failures
        failures = [i for i in interactions if i.error_info]
        
        if not failures:
            return insights
            
        # Categorize failures
        failure_categories = defaultdict(list)
        for failure in failures:
            error_type = failure.error_info.get("type", "unknown")
            failure_categories[error_type].append(failure)
            
        # Analyze each category
        for error_type, failures_list in failure_categories.items():
            if len(failures_list) >= 3:  # Recurring issue
                # Find common factors
                common_factors = self._find_common_factors(failures_list)
                
                insight = ReflectionInsight(
                    insight_type="error",
                    description=f"Recurring {error_type} errors detected",
                    impact_score=min(len(failures_list) / 10, 1.0),
                    actionable=True,
                    recommended_actions=[
                        f"Implement error handling for {error_type}",
                        "Add validation for common failure conditions",
                        "Consider fallback strategy for this error type"
                    ],
                    supporting_data={
                        "error_type": error_type,
                        "frequency": len(failures_list),
                        "common_factors": common_factors,
                        "examples": [f.error_info for f in failures_list[:3]]
                    }
                )
                insights.append(insight)
                
                # Store pattern for prevention
                self.failure_patterns[error_type].append({
                    "factors": common_factors,
                    "frequency": len(failures_list)
                })
                
        return insights
        
    async def _identify_optimizations(
        self,
        interactions: List[ReflectionContext]
    ) -> List[ReflectionInsight]:
        """Identify optimization opportunities"""
        insights = []
        
        # Performance optimization
        slow_requests = [
            i for i in interactions
            if i.performance_metrics.get("duration", 0) > 5.0  # 5 seconds
        ]
        
        if len(slow_requests) >= 5:
            # Analyze slow request patterns
            slow_patterns = self._analyze_slow_patterns(slow_requests)
            
            for pattern in slow_patterns:
                insight = ReflectionInsight(
                    insight_type="optimization",
                    description=f"Performance optimization opportunity: {pattern['description']}",
                    impact_score=pattern["potential_improvement"],
                    actionable=True,
                    recommended_actions=pattern["recommendations"],
                    supporting_data={
                        "avg_duration": pattern["avg_duration"],
                        "pattern": pattern["pattern"],
                        "affected_requests": pattern["count"]
                    }
                )
                insights.append(insight)
                
        # Resource optimization
        resource_insights = await self._analyze_resource_usage(interactions)
        insights.extend(resource_insights)
        
        return insights
        
    def _extract_patterns(
        self,
        interactions: List[ReflectionContext]
    ) -> List[Dict[str, Any]]:
        """Extract common patterns from interactions"""
        patterns = []
        
        # Input pattern analysis
        input_features = defaultdict(int)
        for interaction in interactions:
            features = self._extract_features(interaction.input_data)
            for feature in features:
                input_features[feature] += 1
                
        # Find frequent features
        total = len(interactions)
        for feature, count in input_features.items():
            frequency = count / total
            if frequency > 0.7:  # Present in 70%+ of successes
                patterns.append({
                    "type": "input_feature",
                    "feature": feature,
                    "frequency": frequency,
                    "confidence": frequency
                })
                
        # Workflow pattern analysis
        workflow_patterns = self._analyze_workflow_patterns(interactions)
        patterns.extend(workflow_patterns)
        
        return patterns
        
    def _extract_features(self, data: Dict[str, Any]) -> List[str]:
        """Extract features from interaction data"""
        features = []
        
        # Basic features
        for key, value in data.items():
            if isinstance(value, str) and len(value) < 50:
                features.append(f"{key}={value}")
            elif isinstance(value, (int, float)):
                features.append(f"{key}_numeric")
            elif isinstance(value, list):
                features.append(f"{key}_list_size_{len(value)}")
                
        return features
        
    async def _apply_immediate_learnings(
        self,
        insights: List[ReflectionInsight]
    ) -> None:
        """Apply learnings that can be immediately actionable"""
        for insight in insights:
            if insight.actionable and insight.impact_score > 0.8:
                # High-impact actionable insights
                try:
                    if insight.insight_type == "pattern":
                        await self._apply_pattern_learning(insight)
                    elif insight.insight_type == "error":
                        await self._apply_error_prevention(insight)
                    elif insight.insight_type == "optimization":
                        await self._apply_optimization(insight)
                        
                    self.applied_learnings.append({
                        "insight": insight,
                        "applied_at": datetime.now(),
                        "status": "success"
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to apply learning: {e}")
                    self.applied_learnings.append({
                        "insight": insight,
                        "applied_at": datetime.now(),
                        "status": "failed",
                        "error": str(e)
                    })
```

### Day 3: Cost Optimization Engine

#### 9.2 Cost Optimizer
```python
# services/learning-engine/src/optimization/cost_optimizer.py
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass

@dataclass
class CostProfile:
    """Cost profile for different operations"""
    model_name: str
    cost_per_token: float
    average_tokens: int
    latency_ms: float
    quality_score: float  # 0-1

@dataclass
class OptimizationStrategy:
    """Cost optimization strategy"""
    strategy_type: str  # cache, batch, model_switch, compression
    estimated_savings: float
    implementation_complexity: str  # low, medium, high
    prerequisites: List[str]
    steps: List[str]

class CostOptimizer:
    """Optimize costs across the system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        
        # Cost tracking
        self.cost_history = []
        self.model_costs = self._initialize_model_costs()
        
        # Optimization state
        self.active_strategies = []
        self.cache_performance = {"hits": 0, "misses": 0}
        
    def _default_config(self) -> Dict[str, Any]:
        """Default cost optimizer configuration"""
        return {
            "optimization_threshold": 0.1,  # 10% savings
            "cache_ttl": 3600,  # 1 hour
            "batch_timeout": 100,  # ms
            "quality_threshold": 0.8
        }
        
    def _initialize_model_costs(self) -> Dict[str, CostProfile]:
        """Initialize model cost profiles"""
        return {
            "gpt-4o": CostProfile(
                model_name="gpt-4o",
                cost_per_token=0.00003,
                average_tokens=1000,
                latency_ms=2000,
                quality_score=0.95
            ),
            "gpt-4o-mini": CostProfile(
                model_name="gpt-4o-mini",
                cost_per_token=0.000001,
                average_tokens=800,
                latency_ms=1000,
                quality_score=0.85
            ),
            "claude-3-sonnet": CostProfile(
                model_name="claude-3-sonnet",
                cost_per_token=0.000015,
                average_tokens=1200,
                latency_ms=1500,
                quality_score=0.92
            ),
            "claude-3-haiku": CostProfile(
                model_name="claude-3-haiku",
                cost_per_token=0.000001,
                average_tokens=800,
                latency_ms=800,
                quality_score=0.80
            )
        }
        
    async def analyze_costs(
        self,
        time_window: timedelta = timedelta(days=7)
    ) -> Dict[str, Any]:
        """Analyze costs over time window"""
        # Gather cost data
        cost_data = await self._gather_cost_data(time_window)
        
        # Calculate metrics
        total_cost = sum(item["cost"] for item in cost_data)
        avg_cost_per_request = total_cost / len(cost_data) if cost_data else 0
        
        # Model usage breakdown
        model_usage = defaultdict(lambda: {"count": 0, "cost": 0})
        for item in cost_data:
            model = item["model"]
            model_usage[model]["count"] += 1
            model_usage[model]["cost"] += item["cost"]
            
        # Identify optimization opportunities
        opportunities = await self._identify_cost_opportunities(cost_data)
        
        return {
            "total_cost": total_cost,
            "avg_cost_per_request": avg_cost_per_request,
            "model_usage": dict(model_usage),
            "optimization_opportunities": opportunities,
            "projected_savings": sum(o.estimated_savings for o in opportunities)
        }
        
    async def _identify_cost_opportunities(
        self,
        cost_data: List[Dict[str, Any]]
    ) -> List[OptimizationStrategy]:
        """Identify cost optimization opportunities"""
        opportunities = []
        
        # Cache optimization
        cache_opportunity = self._analyze_cache_opportunity(cost_data)
        if cache_opportunity:
            opportunities.append(cache_opportunity)
            
        # Model switching optimization
        model_switch_opportunity = self._analyze_model_switching(cost_data)
        if model_switch_opportunity:
            opportunities.append(model_switch_opportunity)
            
        # Batch processing optimization
        batch_opportunity = self._analyze_batching_opportunity(cost_data)
        if batch_opportunity:
            opportunities.append(batch_opportunity)
            
        # Prompt compression optimization
        compression_opportunity = self._analyze_compression_opportunity(cost_data)
        if compression_opportunity:
            opportunities.append(compression_opportunity)
            
        return opportunities
        
    def _analyze_cache_opportunity(
        self,
        cost_data: List[Dict[str, Any]]
    ) -> Optional[OptimizationStrategy]:
        """Analyze caching optimization potential"""
        # Find duplicate requests
        request_hashes = defaultdict(list)
        for item in cost_data:
            req_hash = self._hash_request(item["request"])
            request_hashes[req_hash].append(item)
            
        # Calculate potential savings from caching
        duplicate_cost = 0
        duplicate_count = 0
        for req_hash, items in request_hashes.items():
            if len(items) > 1:
                duplicate_count += len(items) - 1
                duplicate_cost += sum(item["cost"] for item in items[1:])
                
        if duplicate_cost > self.config["optimization_threshold"]:
            cache_hit_rate = duplicate_count / len(cost_data)
            
            return OptimizationStrategy(
                strategy_type="cache",
                estimated_savings=duplicate_cost,
                implementation_complexity="low",
                prerequisites=[
                    "Redis cache available",
                    "Request hashing implemented"
                ],
                steps=[
                    "Implement request hashing function",
                    "Set up Redis cache with TTL",
                    "Add cache check before model calls",
                    "Monitor cache hit rate"
                ]
            )
            
        return None
        
    def _analyze_model_switching(
        self,
        cost_data: List[Dict[str, Any]]
    ) -> Optional[OptimizationStrategy]:
        """Analyze model switching optimization"""
        # Categorize requests by complexity
        simple_requests = []
        complex_requests = []
        
        for item in cost_data:
            complexity = self._assess_complexity(item["request"])
            if complexity == "simple":
                simple_requests.append(item)
            else:
                complex_requests.append(item)
                
        # Calculate potential savings
        current_simple_cost = sum(r["cost"] for r in simple_requests)
        
        # Estimate cost with cheaper model for simple requests
        cheap_model = self.model_costs["gpt-4o-mini"]
        estimated_simple_cost = len(simple_requests) * (
            cheap_model.average_tokens * cheap_model.cost_per_token
        )
        
        potential_savings = current_simple_cost - estimated_simple_cost
        
        if potential_savings > self.config["optimization_threshold"]:
            return OptimizationStrategy(
                strategy_type="model_switch",
                estimated_savings=potential_savings,
                implementation_complexity="medium",
                prerequisites=[
                    "Request complexity analyzer",
                    "Model router implementation",
                    "Quality monitoring"
                ],
                steps=[
                    "Implement complexity scoring",
                    "Create model routing rules",
                    "Set up A/B testing",
                    "Monitor quality metrics",
                    "Adjust thresholds based on results"
                ]
            )
            
        return None
        
    async def optimize_request(
        self,
        request: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Optimize a single request for cost"""
        optimization_result = {
            "original_request": request,
            "optimizations_applied": [],
            "estimated_cost": 0
        }
        
        # Check cache first
        cache_key = self._hash_request(request)
        cached_result = await self._check_cache(cache_key)
        
        if cached_result:
            optimization_result["optimizations_applied"].append("cache_hit")
            optimization_result["cached_result"] = cached_result
            self.cache_performance["hits"] += 1
            return optimization_result
            
        self.cache_performance["misses"] += 1
        
        # Assess complexity and route to appropriate model
        complexity = self._assess_complexity(request)
        selected_model = self._select_model(complexity, context)
        
        optimization_result["selected_model"] = selected_model
        optimization_result["complexity"] = complexity
        
        # Apply prompt compression if beneficial
        compressed_request = self._compress_prompt(request)
        if compressed_request != request:
            optimization_result["optimizations_applied"].append("prompt_compression")
            optimization_result["compressed_request"] = compressed_request
            
        # Estimate cost
        model_profile = self.model_costs[selected_model]
        estimated_tokens = self._estimate_tokens(compressed_request)
        optimization_result["estimated_cost"] = (
            estimated_tokens * model_profile.cost_per_token
        )
        
        return optimization_result
        
    def _assess_complexity(self, request: Dict[str, Any]) -> str:
        """Assess request complexity"""
        # Simple heuristics for complexity
        content = request.get("content", "")
        
        # Length-based
        if len(content) < 100:
            length_score = 0
        elif len(content) < 500:
            length_score = 0.3
        elif len(content) < 1000:
            length_score = 0.6
        else:
            length_score = 1.0
            
        # Task-based
        task_type = request.get("type", "")
        if task_type in ["simple_qa", "translation", "summary"]:
            task_score = 0.2
        elif task_type in ["analysis", "generation"]:
            task_score = 0.6
        else:
            task_score = 1.0
            
        # Domain-based
        if request.get("domain") in ["general", "common"]:
            domain_score = 0.2
        else:
            domain_score = 0.7
            
        # Combined score
        complexity_score = (length_score + task_score + domain_score) / 3
        
        if complexity_score < 0.3:
            return "simple"
        elif complexity_score < 0.7:
            return "medium"
        else:
            return "complex"
```

### Day 4: Performance Monitoring & Auto-scaling

#### 9.3 Performance Monitor
```python
# services/learning-engine/src/monitoring/performance_monitor.py
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
import statistics

@dataclass
class PerformanceMetrics:
    """System performance metrics"""
    timestamp: datetime
    request_rate: float  # requests per second
    avg_latency: float  # milliseconds
    p95_latency: float
    p99_latency: float
    error_rate: float
    cpu_usage: float
    memory_usage: float
    active_connections: int

@dataclass
class ScalingDecision:
    """Auto-scaling decision"""
    action: str  # scale_up, scale_down, no_action
    component: str
    current_replicas: int
    target_replicas: int
    reason: str
    metrics: PerformanceMetrics

class PerformanceMonitor:
    """Monitor and optimize system performance"""
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        config: Optional[Dict[str, Any]] = None
    ):
        self.metrics = metrics_collector
        self.config = config or self._default_config()
        
        # Performance tracking
        self.metrics_history = []
        self.scaling_history = []
        self.bottlenecks = []
        
        # Thresholds
        self.thresholds = self.config["thresholds"]
        
    def _default_config(self) -> Dict[str, Any]:
        """Default performance configuration"""
        return {
            "monitoring_interval": 60,  # seconds
            "history_window": 3600,  # 1 hour
            "thresholds": {
                "latency_p95": 3000,  # 3 seconds
                "latency_p99": 5000,  # 5 seconds
                "error_rate": 0.05,  # 5%
                "cpu_usage": 0.8,  # 80%
                "memory_usage": 0.85,  # 85%
                "request_rate_high": 100,  # per second
                "request_rate_low": 10
            },
            "scaling": {
                "min_replicas": 1,
                "max_replicas": 10,
                "scale_up_threshold": 0.8,
                "scale_down_threshold": 0.3,
                "cooldown_period": 300  # 5 minutes
            }
        }
        
    async def monitor_performance(self) -> PerformanceMetrics:
        """Collect current performance metrics"""
        # Gather metrics from various sources
        latency_data = await self._collect_latency_metrics()
        resource_data = await self._collect_resource_metrics()
        error_data = await self._collect_error_metrics()
        
        # Calculate aggregated metrics
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            request_rate=await self._calculate_request_rate(),
            avg_latency=statistics.mean(latency_data) if latency_data else 0,
            p95_latency=self._percentile(latency_data, 0.95),
            p99_latency=self._percentile(latency_data, 0.99),
            error_rate=error_data["rate"],
            cpu_usage=resource_data["cpu"],
            memory_usage=resource_data["memory"],
            active_connections=resource_data["connections"]
        )
        
        # Store metrics
        self.metrics_history.append(metrics)
        
        # Analyze for issues
        issues = self._analyze_performance_issues(metrics)
        if issues:
            await self._handle_performance_issues(issues)
            
        return metrics
        
    async def auto_scale(self) -> Optional[ScalingDecision]:
        """Make auto-scaling decisions based on metrics"""
        # Get recent metrics
        recent_metrics = self._get_recent_metrics()
        
        if not recent_metrics:
            return None
            
        # Check if in cooldown period
        if self._in_cooldown_period():
            return None
            
        # Analyze each component
        for component in ["agno-coordinator", "mcp-agents", "mcp-context"]:
            decision = await self._evaluate_scaling(component, recent_metrics)
            if decision and decision.action != "no_action":
                # Execute scaling
                await self._execute_scaling(decision)
                return decision
                
        return None
        
    async def _evaluate_scaling(
        self,
        component: str,
        metrics: List[PerformanceMetrics]
    ) -> ScalingDecision:
        """Evaluate if scaling is needed for a component"""
        current_replicas = await self._get_current_replicas(component)
        
        # Calculate average metrics
        avg_cpu = statistics.mean(m.cpu_usage for m in metrics)
        avg_memory = statistics.mean(m.memory_usage for m in metrics)
        avg_latency = statistics.mean(m.avg_latency for m in metrics)
        avg_error_rate = statistics.mean(m.error_rate for m in metrics)
        
        # Determine if scaling is needed
        scale_score = 0
        reasons = []
        
        # CPU pressure
        if avg_cpu > self.thresholds["cpu_usage"]:
            scale_score += 0.3
            reasons.append(f"High CPU usage: {avg_cpu:.1%}")
            
        # Memory pressure
        if avg_memory > self.thresholds["memory_usage"]:
            scale_score += 0.3
            reasons.append(f"High memory usage: {avg_memory:.1%}")
            
        # Latency issues
        if avg_latency > self.thresholds["latency_p95"]:
            scale_score += 0.2
            reasons.append(f"High latency: {avg_latency:.0f}ms")
            
        # Error rate
        if avg_error_rate > self.thresholds["error_rate"]:
            scale_score += 0.2
            reasons.append(f"High error rate: {avg_error_rate:.1%}")
            
        # Make decision
        if scale_score > self.config["scaling"]["scale_up_threshold"]:
            target_replicas = min(
                current_replicas + 1,
                self.config["scaling"]["max_replicas"]
            )
            action = "scale_up" if target_replicas > current_replicas else "no_action"
        elif scale_score < self.config["scaling"]["scale_down_threshold"]:
            target_replicas = max(
                current_replicas - 1,
                self.config["scaling"]["min_replicas"]
            )
            action = "scale_down" if target_replicas < current_replicas else "no_action"
        else:
            target_replicas = current_replicas
            action = "no_action"
            
        return ScalingDecision(
            action=action,
