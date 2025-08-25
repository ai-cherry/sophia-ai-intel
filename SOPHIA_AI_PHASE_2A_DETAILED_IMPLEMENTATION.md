# Sophia AI Phase 2A: Research Team Integration - Detailed Implementation Plan

**Date**: August 25, 2025  
**Duration**: 2 Weeks (Weeks 5-6)  
**Priority**: HIGH - Following Phase 1B  
**Goal**: Implement AGNO research team using existing services for collaborative multi-agent research

## Executive Summary

Phase 2A implements the first AGNO agent team, demonstrating the power of collaborative multi-agent systems by creating a Research Team that leverages the wrapped MCP services from Phase 1B. This phase showcases how multiple agents can work together to conduct comprehensive research, analyze data, and synthesize insights.

### Key Objectives
1. Create a functional AGNO Research Team with specialized agents
2. Implement collaborative research workflows and coordination
3. Integrate with wrapped MCP services (context, research, github)
4. Establish performance benchmarks against existing pipeline
5. Enable A/B testing between AGNO teams and legacy systems

## Research Team Architecture

### Team Composition

| Agent Role | Primary Responsibilities | MCP Service Integration |
|------------|-------------------------|------------------------|
| Lead Researcher | Coordinates research, plans strategy | mcp-research, mcp-agents |
| Data Analyst | Analyzes findings, identifies patterns | mcp-context, mcp-business |
| Fact Checker | Verifies claims, validates sources | mcp-research |
| Synthesizer | Combines insights, creates reports | mcp-context |
| Code Analyst | Analyzes technical content | mcp-github |

### Collaboration Modes

1. **Sequential Mode**: Each agent completes their task before passing to the next
2. **Parallel Mode**: Multiple agents work simultaneously on different aspects
3. **Consensus Mode**: Agents collaborate to reach agreement on findings
4. **Hierarchical Mode**: Lead researcher delegates and reviews work

## Week 5: Core Team Implementation

### Day 1-2: Research Team Foundation

#### 5.1 Research Team Base Class
```python
# services/agno-teams/src/base/research_team.py
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import asyncio
from datetime import datetime

from agno import Team, Agent, Context, Memory
from agno.collaboration import CollaborationMode, Message
from agno.utils import logger

from agno_wrappers.agents import (
    ResearchAgent,
    ContextManagerAgent,
    CodeAnalyzerAgent
)

class ResearchPhase(Enum):
    PLANNING = "planning"
    GATHERING = "gathering"
    ANALYSIS = "analysis"
    VERIFICATION = "verification"
    SYNTHESIS = "synthesis"
    REVIEW = "review"

@dataclass
class ResearchRequest:
    """Research request structure"""
    topic: str
    depth: str = "standard"  # quick, standard, deep
    domains: List[str] = None  # web, academic, code, business
    constraints: Dict[str, Any] = None
    deadline: Optional[datetime] = None
    output_format: str = "report"  # report, summary, presentation

@dataclass
class ResearchResult:
    """Research result structure"""
    request_id: str
    topic: str
    findings: List[Dict[str, Any]]
    synthesis: str
    confidence_score: float
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    
class ResearchTeam(Team):
    """AGNO Research Team implementation"""
    
    def __init__(
        self,
        name: str = "SophiaResearchTeam",
        memory: Optional[Memory] = None,
        mcp_services: Optional[Dict[str, str]] = None
    ):
        self.mcp_services = mcp_services or self._default_mcp_services()
        
        # Initialize agents
        self.agents = self._create_agents()
        
        # Initialize base team
        super().__init__(
            name=name,
            agents=list(self.agents.values()),
            mode=CollaborationMode.HIERARCHICAL,
            memory=memory
        )
        
        # Research state
        self.active_research: Dict[str, ResearchRequest] = {}
        self.phase_transitions = self._define_phase_transitions()
        
    def _default_mcp_services(self) -> Dict[str, str]:
        """Default MCP service URLs"""
        return {
            "research": "http://mcp-research:8080",
            "context": "http://mcp-context:8080",
            "github": "http://mcp-github:8080",
            "agents": "http://mcp-agents:8080"
        }
        
    def _create_agents(self) -> Dict[str, Agent]:
        """Create specialized research agents"""
        agents = {}
        
        # Lead Researcher
        agents["lead"] = LeadResearcherAgent(
            name="LeadResearcher",
            mcp_services=self.mcp_services
        )
        
        # Data Analyst
        agents["analyst"] = DataAnalystAgent(
            name="DataAnalyst",
            mcp_services=self.mcp_services
        )
        
        # Fact Checker
        agents["fact_checker"] = FactCheckerAgent(
            name="FactChecker",
            mcp_services=self.mcp_services
        )
        
        # Synthesizer
        agents["synthesizer"] = SynthesizerAgent(
            name="Synthesizer",
            mcp_services=self.mcp_services
        )
        
        # Code Analyst (for technical research)
        agents["code_analyst"] = CodeAnalystAgent(
            name="CodeAnalyst",
            mcp_services=self.mcp_services
        )
        
        return agents
        
    async def research(self, request: ResearchRequest) -> ResearchResult:
        """Execute a research request"""
        request_id = self._generate_request_id()
        self.active_research[request_id] = request
        
        logger.info(f"Starting research: {request.topic} (ID: {request_idservices})")
        
        try:
            # Phase 1: Planning
            plan = await self._execute_phase(
                ResearchPhase.PLANNING,
                request,
                request_id
            )
            
            # Phase 2: Gathering
            raw_data = await self._execute_phase(
                ResearchPhase.GATHERING,
                request,
                request_id,
                context={"plan": plan}
            )
            
            # Phase 3: Analysis
            analysis = await self._execute_phase(
                ResearchPhase.ANALYSIS,
                request,
                request_id,
                context={"raw_data": raw_data}
            )
            
            # Phase 4: Verification
            verified_data = await self._execute_phase(
                ResearchPhase.VERIFICATION,
                request,
                request_id,
                context={"analysis": analysis}
            )
            
            # Phase 5: Synthesis
            synthesis = await self._execute_phase(
                ResearchPhase.SYNTHESIS,
                request,
                request_id,
                context={"verified_data": verified_data}
            )
            
            # Phase 6: Review
            final_result = await self._execute_phase(
                ResearchPhase.REVIEW,
                request,
                request_id,
                context={"synthesis": synthesis}
            )
            
            # Compile final result
            result = ResearchResult(
                request_id=request_id,
                topic=request.topic,
                findings=final_result["findings"],
                synthesis=final_result["synthesis"],
                confidence_score=final_result["confidence"],
                sources=final_result["sources"],
                metadata={
                    "duration": (datetime.now() - self.start_time).total_seconds(),
                    "phases_completed": len(self.phase_transitions),
                    "agents_involved": len(self.agents)
                }
            )
            
            logger.info(f"Research completed: {request_id}")
            return result
            
        except Exception as e:
            logger.error(f"Research failed: {request_id} - {str(e)}")
            raise
        finally:
            del self.active_research[request_id]
            
    async def _execute_phase(
        self,
        phase: ResearchPhase,
        request: ResearchRequest,
        request_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a specific research phase"""
        logger.info(f"Executing phase: {phase.value} for {request_id}")
        
        # Get phase handler
        handler = self.phase_transitions.get(phase)
        if not handler:
            raise ValueError(f"Unknown phase: {phase}")
            
        # Execute phase with appropriate agents
        result = await handler(request, context or {})
        
        # Store phase result in memory
        if self.memory:
            await self.memory.store(
                key=f"{request_id}:{phase.value}",
                value=result,
                metadata={
                    "phase": phase.value,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        return result
        
    def _define_phase_transitions(self) -> Dict[ResearchPhase, Any]:
        """Define phase transition handlers"""
        return {
            ResearchPhase.PLANNING: self._plan_research,
            ResearchPhase.GATHERING: self._gather_data,
            ResearchPhase.ANALYSIS: self._analyze_data,
            ResearchPhase.VERIFICATION: self._verify_findings,
            ResearchPhase.SYNTHESIS: self._synthesize_results,
            ResearchPhase.REVIEW: self._review_output
        }
        
    async def _plan_research(
        self,
        request: ResearchRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Planning phase: Create research strategy"""
        lead = self.agents["lead"]
        
        # Generate research plan
        plan = await lead.create_research_plan(
            topic=request.topic,
            depth=request.depth,
            domains=request.domains or ["web", "academic"],
            constraints=request.constraints
        )
        
        return {
            "strategy": plan["strategy"],
            "sub_topics": plan["sub_topics"],
            "agent_assignments": plan["assignments"],
            "estimated_duration": plan["duration"]
        }
        
    async def _gather_data(
        self,
        request: ResearchRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gathering phase: Collect data from multiple sources"""
        plan = context["plan"]
        
        # Parallel data gathering
        tasks = []
        
        # Research agent handles web/academic sources
        if "web" in request.domains or "academic" in request.domains:
            research_agent = ResearchAgent(self.mcp_services["research"])
            tasks.append(
                research_agent.research_topic(
                    topic=request.topic,
                    depth=request.depth,
                    sources=["web", "academic"],
                    max_results=50
                )
            )
            
        # Code analyst handles technical sources
        if "code" in request.domains:
            code_agent = self.agents["code_analyst"]
            tasks.append(
                code_agent.analyze_repositories(
                    topic=request.topic,
                    languages=request.constraints.get("languages", []),
                    max_repos=20
                )
            )
            
        # Execute parallel gathering
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        gathered_data = {
            "raw_findings": [],
            "sources": [],
            "errors": []
        }
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                gathered_data["errors"].append(str(result))
            else:
                gathered_data["raw_findings"].extend(result.get("findings", []))
                gathered_data["sources"].extend(result.get("sources", []))
                
        return gathered_data
        
    async def _analyze_data(
        self,
        request: ResearchRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analysis phase: Analyze and extract insights"""
        analyst = self.agents["analyst"]
        raw_data = context["raw_data"]
        
        # Perform analysis
        analysis = await analyst.analyze_findings(
            findings=raw_data["raw_findings"],
            topic=request.topic,
            analysis_types=["patterns", "trends", "correlations", "anomalies"]
        )
        
        return {
            "patterns": analysis["patterns"],
            "insights": analysis["insights"],
            "key_findings": analysis["key_findings"],
            "confidence_scores": analysis["confidence_scores"]
        }
        
    async def _verify_findings(
        self,
        request: ResearchRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verification phase: Fact-check and validate findings"""
        fact_checker = self.agents["fact_checker"]
        analysis = context["analysis"]
        
        # Verify key findings
        verification_tasks = []
        for finding in analysis["key_findings"]:
            verification_tasks.append(
                fact_checker.verify_claim(
                    claim=finding["claim"],
                    sources=finding.get("sources", []),
                    context=finding.get("context", "")
                )
            )
            
        verification_results = await asyncio.gather(*verification_tasks)
        
        # Filter verified findings
        verified_findings = []
        for finding, verification in zip(analysis["key_findings"], verification_results):
            if verification["verified"]:
                finding["verification"] = verification
                verified_findings.append(finding)
                
        return {
            "verified_findings": verified_findings,
            "verification_summary": {
                "total_claims": len(analysis["key_findings"]),
                "verified_claims": len(verified_findings),
                "confidence": sum(v["confidence"] for v in verification_results) / len(verification_results)
            }
        }
        
    async def _synthesize_results(
        self,
        request: ResearchRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesis phase: Create coherent narrative"""
        synthesizer = self.agents["synthesizer"]
        verified_data = context["verified_data"]
        
        # Generate synthesis
        synthesis = await synthesizer.synthesize(
            findings=verified_data["verified_findings"],
            format=request.output_format,
            max_length=request.constraints.get("max_length", 5000)
        )
        
        return {
            "synthesis": synthesis["content"],
            "executive_summary": synthesis["summary"],
            "recommendations": synthesis.get("recommendations", []),
            "visualizations": synthesis.get("visualizations", [])
        }
        
    async def _review_output(
        self,
        request: ResearchRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Review phase: Final quality check and formatting"""
        lead = self.agents["lead"]
        synthesis = context["synthesis"]
        
        # Review and finalize
        review = await lead.review_research(
            synthesis=synthesis["synthesis"],
            findings=context.get("verified_data", {}).get("verified_findings", []),
            topic=request.topic,
            requirements=request.constraints
        )
        
        return {
            "findings": review["findings"],
            "synthesis": review["final_synthesis"],
            "confidence": review["confidence_score"],
            "sources": review["cited_sources"],
            "quality_metrics": review["quality_metrics"]
        }
        
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        import uuid
        return f"research_{uuid.uuid4().hex[:8]}"
```

### Day 3: Specialized Agent Implementation

#### 5.2 Lead Researcher Agent
```python
# services/agno-teams/src/agents/lead_researcher.py
from typing import Dict, Any, List, Optional
from datetime import datetime

from agno import Agent, Context
from agno.tools import tool
from agno_wrappers.agents import SwarmManagerAgent

class LeadResearcherAgent(Agent):
    """Lead researcher coordinating research efforts"""
    
    def __init__(self, name: str, mcp_services: Dict[str, str]):
        super().__init__(
            name=name,
            role="""I am the Lead Researcher responsible for:
            - Creating comprehensive research strategies
            - Coordinating team efforts and assignments
            - Reviewing and quality-checking outputs
            - Making decisions on research direction
            - Ensuring research meets requirements
            """,
            tools=self._create_tools()
        )
        
        # Initialize swarm manager for coordination
        self.swarm_manager = SwarmManagerAgent({
            "name": "agents",
            "url": mcp_services["agents"]
        })
        
    @tool("create_research_plan")
    async def create_research_plan(
        self,
        topic: str,
        depth: str,
        domains: List[str],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a comprehensive research plan"""
        # Analyze topic complexity
        complexity = await self._assess_topic_complexity(topic, domains)
        
        # Break down into sub-topics
        sub_topics = await self._identify_sub_topics(topic, complexity)
        
        # Create agent assignments
        assignments = await self._create_assignments(
            sub_topics,
            domains,
            complexity
        )
        
        # Estimate duration
        duration = self._estimate_duration(complexity, depth, len(sub_topics))
        
        return {
            "strategy": {
                "approach": self._determine_approach(complexity, depth),
                "phases": ["planning", "gathering", "analysis", "verification", "synthesis"],
                "priority_areas": self._identify_priorities(topic, constraints)
            },
            "sub_topics": sub_topics,
            "assignments": assignments,
            "duration": duration,
            "complexity": complexity
        }
        
    @tool("review_research")
    async def review_research(
        self,
        synthesis: str,
        findings: List[Dict[str, Any]],
        topic: str,
        requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Review and finalize research output"""
        # Quality assessment
        quality_metrics = await self._assess_quality(
            synthesis,
            findings,
            requirements
        )
        
        # Check completeness
        completeness = await self._check_completeness(
            synthesis,
            topic,
            requirements
        )
        
        # Generate final synthesis with improvements
        final_synthesis = await self._improve_synthesis(
            synthesis,
            quality_metrics,
            completeness
        )
        
        # Extract and validate sources
        cited_sources = await self._extract_sources(findings)
        
        return {
            "findings": self._prioritize_findings(findings),
            "final_synthesis": final_synthesis,
            "confidence_score": self._calculate_confidence(
                quality_metrics,
                completeness
            ),
            "cited_sources": cited_sources,
            "quality_metrics": quality_metrics
        }
        
    async def _assess_topic_complexity(
        self,
        topic: str,
        domains: List[str]
    ) -> str:
        """Assess the complexity of a research topic"""
        # Factors: breadth, technical depth, data availability
        complexity_factors = {
            "breadth": len(topic.split()) > 5,
            "technical": any(d in ["code", "academic"] for d in domains),
            "interdisciplinary": len(domains) > 2,
            "emerging": await self._is_emerging_topic(topic)
        }
        
        complexity_score = sum(complexity_factors.values())
        
        if complexity_score >= 3:
            return "high"
        elif complexity_score >= 1:
            return "medium"
        else:
            return "low"
            
    async def _identify_sub_topics(
        self,
        topic: str,
        complexity: str
    ) -> List[Dict[str, Any]]:
        """Break down topic into researchable sub-topics"""
        # Use NLP or domain knowledge to identify sub-topics
        # Simplified implementation
        sub_topics = []
        
        # Core aspects
        sub_topics.append({
            "name": f"{topic} - Overview",
            "priority": "high",
            "estimated_effort": "medium"
        })
        
        if complexity in ["medium", "high"]:
            sub_topics.extend([
                {
                    "name": f"{topic} - Technical Details",
                    "priority": "high",
                    "estimated_effort": "high"
                },
                {
                    "name": f"{topic} - Current Trends",
                    "priority": "medium",
                    "estimated_effort": "medium"
                }
            ])
            
        if complexity == "high":
            sub_topics.extend([
                {
                    "name": f"{topic} - Future Implications",
                    "priority": "medium",
                    "estimated_effort": "high"
                },
                {
                    "name": f"{topic} - Comparative Analysis",
                    "priority": "low",
                    "estimated_effort": "high"
                }
            ])
            
        return sub_topics
```

#### 5.3 Data Analyst Agent
```python
# services/agno-teams/src/agents/data_analyst.py
from typing import Dict, Any, List, Optional
import statistics
from collections import Counter, defaultdict

from agno import Agent
from agno.tools import tool

class DataAnalystAgent(Agent):
    """Data analyst for pattern recognition and insights"""
    
    def __init__(self, name: str, mcp_services: Dict[str, str]):
        super().__init__(
            name=name,
            role="""I am a Data Analyst responsible for:
            - Identifying patterns and trends in research data
            - Performing statistical analysis
            - Extracting key insights
            - Visualizing findings
            - Correlating data from multiple sources
            """,
            tools=self._create_tools()
        )
        
    @tool("analyze_findings")
    async def analyze_findings(
        self,
        findings: List[Dict[str, Any]],
        topic: str,
        analysis_types: List[str]
    ) -> Dict[str, Any]:
        """Analyze research findings for patterns and insights"""
        results = {
            "patterns": [],
            "insights": [],
            "key_findings": [],
            "confidence_scores": {}
        }
        
        # Pattern detection
        if "patterns" in analysis_types:
            results["patterns"] = await self._detect_patterns(findings)
            
        # Trend analysis
        if "trends" in analysis_types:
            results["trends"] = await self._analyze_trends(findings)
            
        # Correlation analysis
        if "correlations" in analysis_types:
            results["correlations"] = await self._find_correlations(findings)
            
        # Anomaly detection
        if "anomalies" in analysis_types:
            results["anomalies"] = await self._detect_anomalies(findings)
            
        # Extract key insights
        results["insights"] = await self._extract_insights(results)
        
        # Identify key findings with confidence scores
        results["key_findings"] = await self._identify_key_findings(
            findings,
            results["insights"]
        )
        
        # Calculate confidence scores
        results["confidence_scores"] = self._calculate_confidence_scores(results)
        
        return results
        
    async def _detect_patterns(
        self,
        findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect patterns in the findings"""
        patterns = []
        
        # Frequency analysis
        term_frequency = Counter()
        source_frequency = Counter()
        sentiment_distribution = defaultdict(int)
        
        for finding in findings:
            # Extract terms (simplified - would use NLP in production)
            content = finding.get("content", "")
            terms = content.lower().split()
            term_frequency.update(terms)
            
            # Track sources
            source = finding.get("source", "unknown")
            source_frequency[source] += 1
            
            # Track sentiment if available
            sentiment = finding.get("sentiment", "neutral")
            sentiment_distribution[sentiment] += 1
            
        # Identify significant patterns
        total_findings = len(findings)
        
        # Term patterns
        common_terms = [
            {
                "type": "term_frequency",
                "term": term,
                "frequency": count,
                "percentage": (count / total_findings) * 100
            }
            for term, count in term_frequency.most_common(10)
            if count > total_findings * 0.1  # Appears in >10% of findings
        ]
        
        if common_terms:
            patterns.append({
                "pattern_type": "common_terms",
                "description": "Frequently occurring terms",
                "data": common_terms
            })
            
        # Source concentration
        dominant_sources = [
            source for source, count in source_frequency.most_common(3)
            if count > total_findings * 0.2  # >20% from single source
        ]
        
        if dominant_sources:
            patterns.append({
                "pattern_type": "source_concentration",
                "description": "High concentration from specific sources",
                "data": dominant_sources,
                "warning": "Consider source diversity"
            })
            
        # Sentiment patterns
        if len(sentiment_distribution) > 1:
            patterns.append({
                "pattern_type": "sentiment_distribution",
                "description": "Distribution of sentiments",
                "data": dict(sentiment_distribution),
                "dominant": max(sentiment_distribution.items(), key=lambda x: x[1])[0]
            })
            
        return patterns
        
    async def _analyze_trends(
        self,
        findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze temporal trends in findings"""
        trends = []
        
        # Group findings by time period (if timestamps available)
        temporal_groups = defaultdict(list)
        
        for finding in findings:
            timestamp = finding.get("timestamp")
            if timestamp:
                # Simplified - group by day
                date_key = timestamp.split("T")[0] if "T" in timestamp else timestamp
                temporal_groups[date_key].append(finding)
                
        if len(temporal_groups) > 1:
            # Analyze trends over time
            dates = sorted(temporal_groups.keys())
            
            # Volume trend
            volumes = [len(temporal_groups[date]) for date in dates]
            volume_trend = self._calculate_trend(volumes)
            
            trends.append({
                "trend_type": "volume",
                "description": "Finding volume over time",
                "direction": volume_trend,
                "data_points": list(zip(dates, volumes))
            })
            
            # Topic evolution (simplified)
            topic_evolution = []
            for date in dates:
                day_findings = temporal_groups[date]
                # Extract top topics for each day
                day_topics = self._extract_topics(day_findings)
                topic_evolution.append({
                    "date": date,
                    "top_topics": day_topics[:3]
                })
                
            if topic_evolution:
                trends.append({
                    "trend_type": "topic_evolution",
                    "description": "How topics evolved over time",
                    "data": topic_evolution
                })
                
        return trends
        
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "insufficient_data"
            
        # Simple linear trend
        avg_first_half = statistics.mean(values[:len(values)//2])
        avg_second_half = statistics.mean(values[len(values)//2:])
        
        change_percent = ((avg_second_half - avg_first_half) / avg_first_half) * 100
        
        if change_percent > 10:
            return "increasing"
        elif change_percent < -10:
            return "decreasing"
        else:
            return "stable"
```

### Day 4: Integration & Testing

#### 5.4 Team Integration with AGNO Coordinator
```python
# services/agno-coordinator/src/teams/research_integration.py
from typing import Dict, Any, Optional
import asyncio

from agno_teams.research_team import ResearchTeam, ResearchRequest
from ..routing.router import Router
from ..monitoring.metrics import MetricsCollector

class ResearchTeamIntegration:
    """Integration layer between AGNO Coordinator and Research Team"""
    
    def __init__(
        self,
        router: Router,
        metrics: MetricsCollector,
        mcp_services: Dict[str, str]
    ):
        self.router = router
        self.metrics = metrics
        self.research_team = ResearchTeam(
            name="SophiaResearchTeam",
            mcp_services=mcp_services
        )
        
        # Performance tracking
        self.performance_data = {
            "requests_handled": 0,
            "average_duration": 0,
            "success_rate": 0,
            "confidence_scores": []
        }
        
    async def handle_research_request(
        self,
        request: Dict[str, Any],
        use_agno: bool = True
    ) -> Dict[str, Any]:
        """Handle research request with A/B testing capability"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            if use_agno:
                # Use AGNO Research Team
                result = await self._handle_with_agno(request)
                routing = "agno_research_team"
            else:
                # Use legacy pipeline
                result = await self._handle_with_legacy(request)
                routing = "legacy_pipeline"
                
            # Record metrics
            duration = asyncio.get_event_loop().time() - start_time
            self.metrics.recordHistogram(
                "research_request_duration",
                duration * 1000,  # Convert to ms
                {"routing": routing, "success": "true"}
            )
            
            # Update performance data
            self._update_performance(result, duration, success=True)
            
            return {
                "success": True,
                "result": result,
                "routing": routing,
                "duration": duration
            }
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self.metrics.incrementCounter(
                "research_request_errors",
                {"routing": "agno_research_team" if use_agno else "legacy_pipeline"}
            )
            
            self._update_performance(None, duration, success=False)
            
            return {
                "success": False,
                "error": str(e),
                "routing": "agno_research_team" if use_agno else "legacy_pipeline",
                "duration": duration
            }
            
    async def _handle_with_agno(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle request using AGNO Research Team"""
        # Convert to ResearchRequest
        research_request = ResearchRequest(
            topic=request.get("content", ""),
            depth=request.get("depth", "standard"),
            domains=request.get("domains", ["web", "academic"]),
            constraints=request.get("constraints", {}),
            output_format=request.get("format", "report")
        )
