"""
Sophia CodeKraken Planning Agents

Multi-agent planning system with three specialized planners:
- Cutting-Edge Planner: Experimental, bleeding-edge approaches
- Conservative Planner: Stable, proven, production-ready solutions  
- Synthesis Planner: Combines and optimizes approaches from other planners

Key Features:
- Risk-aware planning strategies
- Technology stack evaluation
- Resource requirement estimation
- Implementation complexity analysis
- Integration with repository intelligence

Version: 1.0.0
Author: Sophia AI Intelligence Team
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod

from ..base_agent import SophiaAgent, AgentRole, AgentTask
from ..embedding.rag_pipeline import RAGPipeline, RetrievalQuery, ContextType, RetrievalStrategy

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for planning approaches"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ImplementationComplexity(Enum):
    """Implementation complexity levels"""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class TechnologyMaturity(Enum):
    """Technology maturity levels"""
    EXPERIMENTAL = "experimental"
    ALPHA = "alpha"
    BETA = "beta"
    STABLE = "stable"
    MATURE = "mature"
    LEGACY = "legacy"


@dataclass
class TechnologyChoice:
    """Represents a technology choice in a plan"""
    name: str
    version: Optional[str]
    maturity: TechnologyMaturity
    justification: str
    alternatives: List[str]
    risk_factors: List[str]
    benefits: List[str]
    learning_curve: str  # low, medium, high
    community_support: str  # poor, fair, good, excellent


@dataclass
class ImplementationStep:
    """Individual step in an implementation plan"""
    id: str
    title: str
    description: str
    estimated_effort_hours: float
    complexity: ImplementationComplexity
    dependencies: List[str]
    risks: List[str]
    deliverables: List[str]
    validation_criteria: List[str]
    technologies: List[str]
    code_examples: Optional[str] = None


@dataclass
class PlanningResult:
    """Result from a planning agent"""
    plan_id: str
    planner_type: str
    title: str
    summary: str
    approach_description: str
    overall_risk: RiskLevel
    estimated_total_hours: float
    complexity_score: float
    confidence_score: float
    
    # Detailed components
    technology_stack: List[TechnologyChoice]
    implementation_steps: List[ImplementationStep]
    architecture_decisions: List[str]
    quality_measures: List[str]
    deployment_strategy: str
    maintenance_considerations: List[str]
    
    # Analysis
    pros: List[str]
    cons: List[str]
    success_factors: List[str]
    failure_risks: List[str]
    
    # Metadata
    created_at: datetime
    repository_context_used: bool
    similar_implementations_found: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            **asdict(self),
            'overall_risk': self.overall_risk.value,
            'created_at': self.created_at.isoformat(),
            'technology_stack': [
                {
                    **asdict(tech),
                    'maturity': tech.maturity.value
                } for tech in self.technology_stack
            ],
            'implementation_steps': [
                {
                    **asdict(step),
                    'complexity': step.complexity.value
                } for step in self.implementation_steps
            ]
        }


class BasePlannerAgent(SophiaAgent, ABC):
    """
    Abstract base class for planning agents
    """
    
    def __init__(
        self,
        agent_id: str,
        role: AgentRole,
        name: str,
        llm_config: Dict[str, Any],
        mcp_clients: Dict[str, Any],
        rag_pipeline: Optional[RAGPipeline] = None
    ):
        super().__init__(agent_id, role, name, llm_config, mcp_clients)
        self.rag_pipeline = rag_pipeline
        
        # Planning configuration
        self.technology_preferences = self._get_technology_preferences()
        self.risk_tolerance = self._get_risk_tolerance()
        self.complexity_preference = self._get_complexity_preference()

    @abstractmethod
    def _get_technology_preferences(self) -> Dict[str, Any]:
        """Get technology preferences for this planner type"""
        pass

    @abstractmethod
    def _get_risk_tolerance(self) -> RiskLevel:
        """Get risk tolerance for this planner type"""
        pass

    @abstractmethod
    def _get_complexity_preference(self) -> str:
        """Get complexity preference for this planner type"""
        pass

    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute planning task"""
        try:
            if task.task_type == "task_planning":
                return await self._create_implementation_plan(task)
            elif task.task_type == "plan_analysis":
                return await self._analyze_existing_plan(task)
            elif task.task_type == "plan_comparison":
                return await self._compare_plans(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
                
        except Exception as e:
            logger.error(f"Planning task failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "planner_type": self.__class__.__name__
            }

    async def _create_implementation_plan(self, task: AgentTask) -> Dict[str, Any]:
        """Create implementation plan for the given task"""
        logger.info(f"Creating {self.__class__.__name__} plan for: {task.description}")
        
        # Gather repository context if available
        repository_context = None
        similar_implementations = []
        
        if self.rag_pipeline:
            try:
                retrieval_query = RetrievalQuery(
                    query=task.description,
                    context_types=[
                        ContextType.CODE_IMPLEMENTATION,
                        ContextType.API_USAGE,
                        ContextType.DESIGN_PATTERNS
                    ],
                    strategy=RetrievalStrategy.HYBRID_SEARCH,
                    max_results=10,
                    agent_context={'role': self.role.value}
                )
                
                retrieval_result = await self.rag_pipeline.retrieve_context(retrieval_query)
                repository_context = retrieval_result.augmented_context
                similar_implementations = retrieval_result.chunks
                
                logger.info(f"Found {len(similar_implementations)} similar implementations")
                
            except Exception as e:
                logger.warning(f"Failed to retrieve repository context: {e}")
        
        # Create plan using planner-specific approach
        plan = await self._generate_plan(task, repository_context, similar_implementations)
        
        return {
            "success": True,
            "plan": plan.to_dict(),
            "planner_type": self.__class__.__name__,
            "context_used": repository_context is not None
        }

    @abstractmethod
    async def _generate_plan(
        self,
        task: AgentTask,
        repository_context: Optional[str],
        similar_implementations: List[Any]
    ) -> PlanningResult:
        """Generate the actual plan - implemented by subclasses"""
        pass

    async def _analyze_repository_patterns(self, similar_implementations: List[Any]) -> Dict[str, Any]:
        """Analyze patterns from similar implementations in the repository"""
        if not similar_implementations:
            return {}
        
        patterns = {
            "common_technologies": [],
            "architectural_patterns": [],
            "code_patterns": [],
            "best_practices": [],
            "anti_patterns": []
        }
        
        # Analyze technology usage
        tech_frequency = {}
        for impl in similar_implementations:
            chunk = impl.chunk
            if chunk.language in tech_frequency:
                tech_frequency[chunk.language] += 1
            else:
                tech_frequency[chunk.language] = 1
        
        # Most common technologies
        patterns["common_technologies"] = sorted(
            tech_frequency.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return patterns

    def _estimate_effort(self, steps: List[ImplementationStep]) -> float:
        """Estimate total effort for implementation steps"""
        return sum(step.estimated_effort_hours for step in steps)

    def _calculate_complexity_score(self, steps: List[ImplementationStep]) -> float:
        """Calculate overall complexity score"""
        complexity_weights = {
            ImplementationComplexity.TRIVIAL: 1,
            ImplementationComplexity.SIMPLE: 2,
            ImplementationComplexity.MODERATE: 3,
            ImplementationComplexity.COMPLEX: 4,
            ImplementationComplexity.VERY_COMPLEX: 5
        }
        
        if not steps:
            return 0.0
        
        total_weighted = sum(complexity_weights[step.complexity] for step in steps)
        return total_weighted / (len(steps) * 5)  # Normalize to 0-1

    def _assess_overall_risk(self, technologies: List[TechnologyChoice], steps: List[ImplementationStep]) -> RiskLevel:
        """Assess overall risk level"""
        risk_scores = []
        
        # Technology risk
        tech_risk = 0
        for tech in technologies:
            if tech.maturity == TechnologyMaturity.EXPERIMENTAL:
                tech_risk += 5
            elif tech.maturity == TechnologyMaturity.ALPHA:
                tech_risk += 4
            elif tech.maturity == TechnologyMaturity.BETA:
                tech_risk += 3
            elif tech.maturity == TechnologyMaturity.STABLE:
                tech_risk += 1
            
        if technologies:
            avg_tech_risk = tech_risk / len(technologies)
            risk_scores.append(avg_tech_risk)
        
        # Implementation complexity risk
        complexity_risk = self._calculate_complexity_score(steps) * 5
        risk_scores.append(complexity_risk)
        
        # Overall risk assessment
        if not risk_scores:
            return RiskLevel.MEDIUM
        
        avg_risk = sum(risk_scores) / len(risk_scores)
        
        if avg_risk <= 1:
            return RiskLevel.VERY_LOW
        elif avg_risk <= 2:
            return RiskLevel.LOW
        elif avg_risk <= 3:
            return RiskLevel.MEDIUM
        elif avg_risk <= 4:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH


class CuttingEdgePlannerAgent(BasePlannerAgent):
    """
    Planner focused on experimental, bleeding-edge approaches
    """
    
    def _initialize_capabilities(self):
        """Initialize cutting-edge planner capabilities"""
        capabilities = [
            "handle_task_planning",
            "handle_experimental_tech_evaluation",
            "handle_innovation_assessment",
            "handle_risk_analysis"
        ]
        
        for capability in capabilities:
            self.context.add_capability(capability)

    def _get_technology_preferences(self) -> Dict[str, Any]:
        """Technology preferences for cutting-edge approach"""
        return {
            "prefer_latest_versions": True,
            "accept_experimental": True,
            "prefer_performance": True,
            "accept_complexity": True,
            "value_innovation": True,
            "preferred_tech_maturity": [TechnologyMaturity.EXPERIMENTAL, TechnologyMaturity.ALPHA, TechnologyMaturity.BETA]
        }

    def _get_risk_tolerance(self) -> RiskLevel:
        return RiskLevel.HIGH

    def _get_complexity_preference(self) -> str:
        return "embrace_complexity"

    async def _generate_plan(
        self,
        task: AgentTask,
        repository_context: Optional[str],
        similar_implementations: List[Any]
    ) -> PlanningResult:
        """Generate cutting-edge implementation plan"""
        
        # Analyze repository patterns
        patterns = await self._analyze_repository_patterns(similar_implementations)
        
        # Define cutting-edge technology stack
        technology_stack = await self._select_cutting_edge_technologies(task.description, patterns)
        
        # Create implementation steps
        implementation_steps = await self._create_cutting_edge_steps(task, technology_stack)
        
        # Calculate metrics
        total_effort = self._estimate_effort(implementation_steps)
        complexity_score = self._calculate_complexity_score(implementation_steps)
        overall_risk = self._assess_overall_risk(technology_stack, implementation_steps)
        
        return PlanningResult(
            plan_id=f"cutting_edge_{task.id}_{datetime.now().timestamp()}",
            planner_type="cutting_edge",
            title=f"Cutting-Edge Implementation: {task.title}",
            summary="Innovative approach using latest technologies and experimental patterns",
            approach_description="Leverages bleeding-edge technologies to maximize performance and capabilities, accepting higher risk for potential breakthrough results.",
            overall_risk=overall_risk,
            estimated_total_hours=total_effort,
            complexity_score=complexity_score,
            confidence_score=0.7,  # Lower confidence due to experimental nature
            
            technology_stack=technology_stack,
            implementation_steps=implementation_steps,
            architecture_decisions=[
                "Use microservices architecture for maximum scalability",
                "Implement event-driven patterns with latest frameworks",
                "Apply cutting-edge AI/ML techniques where applicable",
                "Use experimental performance optimization techniques"
            ],
            quality_measures=[
                "Extensive automated testing with latest test frameworks",
                "Performance benchmarking with experimental tools",
                "Code quality analysis with AI-powered tools",
                "Security scanning with next-gen tools"
            ],
            deployment_strategy="Container-native with edge computing deployment",
            maintenance_considerations=[
                "Requires team training on new technologies",
                "May need frequent updates due to experimental nature",
                "Monitoring and observability crucial for debugging",
                "Backup plans needed for technology failures"
            ],
            
            pros=[
                "Maximum performance potential",
                "Leverages latest innovations",
                "Future-proof architecture",
                "Competitive advantage through early adoption"
            ],
            cons=[
                "Higher risk of bugs and issues",
                "Limited community support",
                "Potential for technology abandonment",
                "Higher learning curve for team"
            ],
            success_factors=[
                "Team expertise in new technologies",
                "Strong monitoring and debugging capabilities",
                "Flexible architecture for quick pivots",
                "Adequate time for experimentation"
            ],
            failure_risks=[
                "Experimental technology instability",
                "Lack of documentation and examples",
                "Performance issues in production",
                "Team knowledge gaps"
            ],
            
            created_at=datetime.now(),
            repository_context_used=repository_context is not None,
            similar_implementations_found=len(similar_implementations)
        )

    async def _select_cutting_edge_technologies(self, task_description: str, patterns: Dict[str, Any]) -> List[TechnologyChoice]:
        """Select cutting-edge technologies for the task"""
        technologies = []
        
        # Example cutting-edge technology selections
        if "api" in task_description.lower() or "service" in task_description.lower():
            technologies.append(TechnologyChoice(
                name="Fastify",
                version="latest",
                maturity=TechnologyMaturity.BETA,
                justification="Ultra-fast Node.js web framework with latest performance optimizations",
                alternatives=["Express", "Koa", "Hapi"],
                risk_factors=["Smaller ecosystem", "Less mature"],
                benefits=["Superior performance", "Modern async patterns", "TypeScript-first"],
                learning_curve="medium",
                community_support="good"
            ))
        
        if "database" in task_description.lower() or "data" in task_description.lower():
            technologies.append(TechnologyChoice(
                name="SurrealDB",
                version="latest",
                maturity=TechnologyMaturity.ALPHA,
                justification="Multi-model database with graph capabilities and real-time features",
                alternatives=["PostgreSQL", "MongoDB", "Neo4j"],
                risk_factors=["Very new", "Limited production usage"],
                benefits=["Multi-model flexibility", "Real-time capabilities", "Modern query language"],
                learning_curve="high",
                community_support="fair"
            ))
        
        if "frontend" in task_description.lower() or "ui" in task_description.lower():
            technologies.append(TechnologyChoice(
                name="Solid.js",
                version="latest",
                maturity=TechnologyMaturity.BETA,
                justification="High-performance reactive framework with fine-grained reactivity",
                alternatives=["React", "Vue", "Svelte"],
                risk_factors=["Smaller ecosystem", "Limited component libraries"],
                benefits=["Superior performance", "Small bundle size", "True reactivity"],
                learning_curve="medium",
                community_support="good"
            ))
        
        return technologies

    async def _create_cutting_edge_steps(self, task: AgentTask, technologies: List[TechnologyChoice]) -> List[ImplementationStep]:
        """Create implementation steps for cutting-edge approach"""
        steps = []
        
        # Research and prototyping phase
        steps.append(ImplementationStep(
            id="research_prototype",
            title="Technology Research and Prototyping",
            description="Research cutting-edge technologies and create proof-of-concept prototypes",
            estimated_effort_hours=16,
            complexity=ImplementationComplexity.COMPLEX,
            dependencies=[],
            risks=["Technology may not meet requirements", "Learning curve steeper than expected"],
            deliverables=["Technology evaluation report", "Working prototypes"],
            validation_criteria=["Prototypes demonstrate key capabilities", "Performance meets targets"],
            technologies=[tech.name for tech in technologies]
        ))
        
        # Architecture design
        steps.append(ImplementationStep(
            id="cutting_edge_architecture",
            title="Advanced Architecture Design",
            description="Design architecture leveraging latest patterns and technologies",
            estimated_effort_hours=12,
            complexity=ImplementationComplexity.COMPLEX,
            dependencies=["research_prototype"],
            risks=["Over-engineering", "Architecture too complex for team"],
            deliverables=["Architecture diagrams", "Technology integration plan"],
            validation_criteria=["Architecture supports all requirements", "Scalability validated"],
            technologies=[tech.name for tech in technologies]
        ))
        
        # Implementation with experimental features
        steps.append(ImplementationStep(
            id="experimental_implementation",
            title="Implementation with Experimental Features",
            description="Implement solution using experimental features and optimizations",
            estimated_effort_hours=32,
            complexity=ImplementationComplexity.VERY_COMPLEX,
            dependencies=["cutting_edge_architecture"],
            risks=["Experimental features may be unstable", "Debug complexity high"],
            deliverables=["Working implementation", "Performance benchmarks"],
            validation_criteria=["All features functional", "Performance exceeds baseline"],
            technologies=[tech.name for tech in technologies]
        ))
        
        return steps


class ConservativePlannerAgent(BasePlannerAgent):
    """
    Planner focused on stable, proven, production-ready approaches
    """
    
    def _initialize_capabilities(self):
        """Initialize conservative planner capabilities"""
        capabilities = [
            "handle_task_planning",
            "handle_stability_assessment",
            "handle_production_readiness",
            "handle_risk_mitigation"
        ]
        
        for capability in capabilities:
            self.context.add_capability(capability)

    def _get_technology_preferences(self) -> Dict[str, Any]:
        """Technology preferences for conservative approach"""
        return {
            "prefer_stable_versions": True,
            "avoid_experimental": True,
            "prefer_reliability": True,
            "minimize_complexity": True,
            "value_stability": True,
            "preferred_tech_maturity": [TechnologyMaturity.STABLE, TechnologyMaturity.MATURE]
        }

    def _get_risk_tolerance(self) -> RiskLevel:
        return RiskLevel.LOW

    def _get_complexity_preference(self) -> str:
        return "minimize_complexity"

    async def _generate_plan(
        self,
        task: AgentTask,
        repository_context: Optional[str],
        similar_implementations: List[Any]
    ) -> PlanningResult:
        """Generate conservative implementation plan"""
        
        # Analyze repository patterns for proven approaches
        patterns = await self._analyze_repository_patterns(similar_implementations)
        
        # Define stable technology stack
        technology_stack = await self._select_conservative_technologies(task.description, patterns)
        
        # Create implementation steps
        implementation_steps = await self._create_conservative_steps(task, technology_stack)
        
        # Calculate metrics
        total_effort = self._estimate_effort(implementation_steps)
        complexity_score = self._calculate_complexity_score(implementation_steps)
        overall_risk = self._assess_overall_risk(technology_stack, implementation_steps)
        
        return PlanningResult(
            plan_id=f"conservative_{task.id}_{datetime.now().timestamp()}",
            planner_type="conservative",
            title=f"Production-Ready Implementation: {task.title}",
            summary="Reliable approach using proven technologies and established patterns",
            approach_description="Utilizes battle-tested technologies and well-established patterns to ensure stability and maintainability with minimal risk.",
            overall_risk=overall_risk,
            estimated_total_hours=total_effort,
            complexity_score=complexity_score,
            confidence_score=0.9,  # High confidence in proven approaches
            
            technology_stack=technology_stack,
            implementation_steps=implementation_steps,
            architecture_decisions=[
                "Use monolithic architecture for simplicity",
                "Implement tried-and-true design patterns",
                "Follow established security best practices",
                "Use standard deployment patterns"
            ],
            quality_measures=[
                "Comprehensive test coverage with proven frameworks",
                "Code review process with established guidelines",
                "Static analysis with mature tools",
                "Security audits using standard practices"
            ],
            deployment_strategy="Traditional deployment with proven CI/CD pipeline",
            maintenance_considerations=[
                "Uses technologies with long-term support",
                "Extensive documentation and examples available",
                "Large community for support",
                "Predictable upgrade paths"
            ],
            
            pros=[
                "Low risk of production issues",
                "Extensive community support",
                "Well-documented technologies",
                "Predictable maintenance costs"
            ],
            cons=[
                "May not leverage latest performance improvements",
                "Could be perceived as outdated",
                "Limited innovation potential",
                "May not handle future scale requirements optimally"
            ],
            success_factors=[
                "Team familiar with chosen technologies",
                "Strong testing and QA processes",
                "Good documentation practices",
                "Proper monitoring and alerting"
            ],
            failure_risks=[
                "Requirements change beyond current capabilities",
                "Performance bottlenecks in high-scale scenarios",
                "Technical debt accumulation",
                "Difficulty attracting developers interested in modern tech"
            ],
            
            created_at=datetime.now(),
            repository_context_used=repository_context is not None,
            similar_implementations_found=len(similar_implementations)
        )

    async def _select_conservative_technologies(self, task_description: str, patterns: Dict[str, Any]) -> List[TechnologyChoice]:
        """Select conservative, proven technologies"""
        technologies = []
        
        # Use established, stable technologies
        if "api" in task_description.lower() or "service" in task_description.lower():
            technologies.append(TechnologyChoice(
                name="Express.js",
                version="4.18.x",
                maturity=TechnologyMaturity.MATURE,
                justification="Battle-tested Node.js framework with extensive ecosystem",
                alternatives=["Fastify", "Koa"],
                risk_factors=["Larger attack surface due to middleware ecosystem"],
                benefits=["Huge ecosystem", "Extensive documentation", "Large community"],
                learning_curve="low",
                community_support="excellent"
            ))
        
        if "database" in task_description.lower() or "data" in task_description.lower():
            technologies.append(TechnologyChoice(
                name="PostgreSQL",
                version="14.x",
                maturity=TechnologyMaturity.MATURE,
                justification="Proven relational database with excellent reliability and performance",
                alternatives=["MySQL", "MongoDB"],
                risk_factors=["Requires proper indexing for performance"],
                benefits=["ACID compliance", "Strong consistency", "Rich feature set"],
                learning_curve="low",
                community_support="excellent"
            ))
        
        if "frontend" in task_description.lower() or "ui" in task_description.lower():
            technologies.append(TechnologyChoice(
                name="React",
                version="18.x",
                maturity=TechnologyMaturity.MATURE,
                justification="Most widely adopted frontend framework with proven track record",
                alternatives=["Vue", "Angular"],
                risk_factors=["Bundle size can be large", "Frequent API changes"],
                benefits=["Huge ecosystem", "Excellent tooling", "Strong job market"],
                learning_curve="medium",
                community_support="excellent"
            ))
        
        return technologies

    async def _create_conservative_steps(self, task: AgentTask, technologies: List[TechnologyChoice]) -> List[ImplementationStep]:
        """Create implementation steps for conservative approach"""
        steps = []
        
        # Requirements analysis
        steps.append(ImplementationStep(
            id="requirements_analysis",
            title="Thorough Requirements Analysis",
            description="Comprehensive analysis of requirements and constraints",
            estimated_effort_hours=8,
            complexity=ImplementationComplexity.SIMPLE,
            dependencies=[],
            risks=["Missing requirements discovered late"],
            deliverables=["Requirements document", "Technical specification"],
            validation_criteria=["All stakeholders approve requirements", "Technical feasibility confirmed"],
            technologies=[]
        ))
        
        # Design phase
        steps.append(ImplementationStep(
            id="conservative_design",
            title="Proven Architecture Design",
            description="Design using well-established architectural patterns",
            estimated_effort_hours=12,
            complexity=ImplementationComplexity.MODERATE,
            dependencies=["requirements_analysis"],
            risks=["Over-engineering", "Under-estimating scalability needs"],
            deliverables=["Architecture document", "Database schema", "API specification"],
            validation_criteria=["Design review passed", "Scalability requirements met"],
            technologies=[tech.name for tech in technologies]
        ))
        
        # Implementation
        steps.append(ImplementationStep(
            id="stable_implementation",
            title="Implementation with Proven Patterns",
            description="Implement using established patterns and best practices",
            estimated_effort_hours=24,
            complexity=ImplementationComplexity.MODERATE,
            dependencies=["conservative_design"],
            risks=["Scope creep", "Integration challenges"],
            deliverables=["Working implementation", "Test suite", "Documentation"],
            validation_criteria=["All tests pass", "Code review approved"],
            technologies=[tech.name for tech in technologies]
        ))
        
        return steps


class SynthesisPlannerAgent(BasePlannerAgent):
    """
    Planner that synthesizes and optimizes approaches from other planners
    """
    
    def _initialize_capabilities(self):
        """Initialize synthesis planner capabilities"""
        capabilities = [
            "handle_plan_synthesis",
            "handle_plan_optimization",
            "handle_approach_balancing",
            "handle_trade_off_analysis"
        ]
        
        for capability in capabilities:
            self.context.add_capability(capability)

    def _get_technology_preferences(self) -> Dict[str, Any]:
        """Technology preferences for synthesis approach"""
        return {
            "balance_innovation_stability": True,
            "prefer_pragmatic_choices": True,
            "optimize_for_context": True,
            "minimize_overall_risk": True,
            "value_flexibility": True,
            "preferred_tech_maturity": [TechnologyMaturity.BETA, TechnologyMaturity.STABLE]
        }

    def _get_risk_tolerance(self) -> RiskLevel:
        return RiskLevel.MEDIUM

    def _get_complexity_preference(self) -> str:
        return "balanced_complexity"

    async def _generate_plan(
        self,
        task: AgentTask,
        repository_context: Optional[str],
        similar_implementations: List[Any]
    ) -> PlanningResult:
        """Generate synthesis plan by combining approaches"""
        
        # For synthesis, we need the other plans as context
        cutting_edge_plan = task.context.get('cutting_edge_plan')
        conservative_plan = task.context.get('conservative_plan')
        
        if not cutting_edge_plan or not conservative_plan:
            # If we don't have other plans, create a balanced approach
            return await self._create_balanced_plan(task, repository_context, similar_implementations)
        
        # Synthesize the best elements from both approaches
        return await self._synthesize_plans(task, cutting_edge_plan, conservative_plan, repository_context)

    async def _create_balanced_plan(
        self,
        task: AgentTask,
        repository_context: Optional[str],
        similar_implementations: List[Any]
    ) -> PlanningResult:
        """Create a balanced plan when other plans aren't available"""
        
        patterns = await self._analyze_repository_patterns(similar_implementations)
        technology_stack = await self._select_balanced_technologies(task.description, patterns)
        implementation_steps = await self._create_balanced_steps(task, technology_stack)
        
        total_effort = self._estimate_effort(implementation_steps)
        complexity_score = self._calculate_complexity_score(implementation_steps)
        overall_risk = self._assess_overall_risk(technology_stack, implementation_steps)
        
        return PlanningResult(
            plan_id=f"synthesis_{task.id}_{datetime.now().timestamp()}",
            planner_type="synthesis",
            title=f"Balanced Implementation: {task.title}",
            summary="Pragmatic approach balancing innovation with stability",
            approach_description="Combines proven technologies with selective innovation to optimize for both current needs and future flexibility.",
            overall_risk=overall_risk,
            estimated_total_hours=total_effort,
            complexity_score=complexity_score,
            confidence_score=0.85,
            
            technology_stack=technology_stack,
            implementation_steps=implementation_steps,
            architecture_decisions=[
                "Use modular architecture for flexibility",
                "Apply proven patterns with selective innovation",
                "Implement progressive enhancement strategy",
                "Balance performance with maintainability"
            ],
            quality_measures=[
                "Risk-based testing strategy",
                "Automated testing with proven frameworks",
                "Code review process with clear guidelines",
                "Performance monitoring and alerting"
            ],
            deployment_strategy="Phased deployment with rollback capabilities",
            maintenance_considerations=[
                "Balance of new and established technologies",
                "Documented upgrade paths for all components",
                "Team training on selected new technologies",
                "Monitoring for both stability and performance"
            ],
            
            pros=[
                "Balanced risk/reward profile",
                "Leverages both innovation and stability",
                "Flexible architecture for future changes",
                "Reasonable learning curve for team"
            ],
            cons=[
                "May not maximize either innovation or stability",
                "Requires careful technology evaluation",
                "Complexity of managing mixed technology stack",
                "Potential conflicts between old and new approaches"
            ],
            success_factors=[
                "Clear technology selection criteria",
                "Strong architectural planning",
                "Team buy-in on balanced approach",
                "Good change management processes"
            ],
            failure_risks=[
                "Technology choices don't integrate well",
                "Team split between old and new approaches",
                "Architectural complexity becomes unwieldy",
                "Performance issues from mixed stack"
            ],
            
            created_at=datetime.now(),
            repository_context_used=repository_context is not None,
            similar_implementations_found=len(similar_implementations)
        )

    async def _synthesize_plans(
        self,
        task: AgentTask,
        cutting_edge_plan: Dict[str, Any],
        conservative_plan: Dict[str, Any],
        repository_context: Optional[str]
    ) -> PlanningResult:
        """Synthesize the best elements from cutting-edge and conservative plans"""
        
        # Analyze both plans for synthesis opportunities
        synthesis_analysis = await self._analyze_plans_for_synthesis(cutting_edge_plan, conservative_plan)
        
        # Select optimal technology stack
        synthesized_tech_stack = await self._synthesize_technology_stacks(
            cutting_edge_plan['technology_stack'],
            conservative_plan['technology_stack'],
            synthesis_analysis
        )
        
        # Create optimized implementation steps
        synthesized_steps = await self._synthesize_implementation_steps(
            cutting_edge_plan['implementation_steps'],
            conservative_plan['implementation_steps'],
            synthesis_analysis
        )
        
        # Calculate metrics
        total_effort = self._estimate_effort(synthesized_steps)
        complexity_score = self._calculate_complexity_score(synthesized_steps)
        overall_risk = self._assess_overall_risk(synthesized_tech_stack, synthesized_steps)
        
        return PlanningResult(
            plan_id=f"synthesis_{task.id}_{datetime.now().timestamp()}",
            planner_type="synthesis",
            title=f"Optimized Synthesis: {task.title}",
            summary="Synthesized approach combining the best elements from multiple planning strategies",
            approach_description="Intelligently combines cutting-edge innovations with proven stability, optimized for the specific context and requirements.",
            overall_risk=overall_risk,
            estimated_total_hours=total_effort,
            complexity_score=complexity_score,
            confidence_score=0.88,  # High confidence due to synthesis
            
            technology_stack=synthesized_tech_stack,
            implementation_steps=synthesized_steps,
            architecture_decisions=self._synthesize_architecture_decisions(cutting_edge_plan, conservative_plan),
            quality_measures=self._synthesize_quality_measures(cutting_edge_plan, conservative_plan),
            deployment_strategy=self._synthesize_deployment_strategy(cutting_edge_plan, conservative_plan),
            maintenance_considerations=self._synthesize_maintenance_considerations(cutting_edge_plan, conservative_plan),
            
            pros=self._synthesize_pros(cutting_edge_plan, conservative_plan, synthesis_analysis),
            cons=self._synthesize_cons(cutting_edge_plan, conservative_plan, synthesis_analysis),
            success_factors=self._synthesize_success_factors(cutting_edge_plan, conservative_plan),
            failure_risks=self._synthesize_failure_risks(cutting_edge_plan, conservative_plan),
            
            created_at=datetime.now(),
            repository_context_used=repository_context is not None,
            similar_implementations_found=0  # Plans already have this info
        )

    async def _select_balanced_technologies(self, task_description: str, patterns: Dict[str, Any]) -> List[TechnologyChoice]:
        """Select balanced technologies that optimize for both innovation and stability"""
        technologies = []
        
        # Choose mature but not outdated technologies
        if "api" in task_description.lower() or "service" in task_description.lower():
            technologies.append(TechnologyChoice(
                name="Koa.js",
                version="2.x",
                maturity=TechnologyMaturity.STABLE,
                justification="Modern Node.js framework with async/await support, more modern than Express but proven",
                alternatives=["Express", "Fastify"],
                risk_factors=["Smaller ecosystem than Express"],
                benefits=["Modern async patterns", "Cleaner middleware model", "Good performance"],
                learning_curve="medium",
                community_support="good"
            ))
        
        if "database" in task_description.lower() or "data" in task_description.lower():
            technologies.append(TechnologyChoice(
                name="PostgreSQL",
                version="15.x",
                maturity=TechnologyMaturity.STABLE,
                justification="Latest stable version with new performance features but proven reliability",
                alternatives=["MySQL", "MongoDB"],
                risk_factors=["Requires proper configuration for optimal performance"],
                benefits=["Latest performance improvements", "JSON support", "Strong ACID compliance"],
                learning_curve="low",
                community_support="excellent"
            ))
        
        return technologies

    async def _create_balanced_steps(self, task: AgentTask, technologies: List[TechnologyChoice]) -> List[ImplementationStep]:
        """Create balanced implementation steps"""
        steps = []
        
        # Planning phase
        steps.append(ImplementationStep(
            id="balanced_planning",
            title="Balanced Planning and Design",
            description="Plan architecture with both innovation and stability considerations",
            estimated_effort_hours=10,
            complexity=ImplementationComplexity.MODERATE,
            dependencies=[],
            risks=["Balancing competing requirements", "Technology selection complexity"],
            deliverables=["Balanced architecture plan", "Technology rationale document"],
            validation_criteria=["Architecture supports requirements", "Technology choices justified"],
            technologies=[tech.name for tech in technologies]
        ))
        
        # Incremental implementation
        steps.append(ImplementationStep(
            id="incremental_implementation",
            title="Incremental Implementation with Validation",
            description="Implement in phases with validation at each step",
            estimated_effort_hours=28,
            complexity=ImplementationComplexity.MODERATE,
            dependencies=["balanced_planning"],
            risks=["Integration challenges", "Performance bottlenecks"],
            deliverables=["Working implementation", "Test suite", "Performance benchmarks"],
            validation_criteria=["Each phase validated before next", "Performance meets targets"],
            technologies=[tech.name for tech in technologies]
        ))
        
        return steps

    async def _analyze_plans_for_synthesis(self, cutting_edge_plan: Dict[str, Any], conservative_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze both plans to identify synthesis opportunities"""
        return {
            "technology_overlap": self._find_technology_overlap(cutting_edge_plan, conservative_plan),
            "complementary_strengths": self._identify_complementary_strengths(cutting_edge_plan, conservative_plan),
            "risk_mitigation_opportunities": self._find_risk_mitigation_opportunities(cutting_edge_plan, conservative_plan),
            "effort_optimization": self._analyze_effort_optimization(cutting_edge_plan, conservative_plan)
        }

    async def _synthesize_technology_stacks(
        self, 
        cutting_edge_tech: List[Dict[str, Any]], 
        conservative_tech: List[Dict[str, Any]], 
        analysis: Dict[str, Any]
    ) -> List[TechnologyChoice]:
        """Synthesize optimal technology stack from both approaches"""
        synthesized_tech = []
        
        # For each technology category, choose the best option
        tech_categories = set()
        for tech in cutting_edge_tech + conservative_tech:
            tech_categories.add(tech['name'].split('.')[0].lower())  # Basic categorization
        
        for category in tech_categories:
            cutting_edge_option = next((t for t in cutting_edge_tech if category in t['name'].lower()), None)
            conservative_option = next((t for t in conservative_tech if category in t['name'].lower()), None)
            
            if cutting_edge_option and conservative_option:
                # Choose based on synthesis criteria
                chosen_tech = self._choose_synthesized_technology(cutting_edge_option, conservative_option)
                synthesized_tech.append(TechnologyChoice(**chosen_tech))
            elif cutting_edge_option:
                synthesized_tech.append(TechnologyChoice(**cutting_edge_option))
            elif conservative_option:
                synthesized_tech.append(TechnologyChoice(**conservative_option))
        
        return synthesized_tech

    def _choose_synthesized_technology(self, cutting_edge: Dict[str, Any], conservative: Dict[str, Any]) -> Dict[str, Any]:
        """Choose the best technology based on synthesis criteria"""
        # Simple heuristic: choose conservative for critical infrastructure, cutting-edge for user-facing
        if "database" in cutting_edge['name'].lower() or "storage" in cutting_edge['name'].lower():
            return conservative  # Choose stability for data layer
        elif "ui" in cutting_edge['name'].lower() or "frontend" in cutting_edge['name'].lower():
            return cutting_edge  # Choose innovation for user experience
        else:
            # For APIs and services, choose middle ground
            middle_ground = conservative.copy()
            middle_ground['justification'] = f"Balanced choice: {conservative['justification']} with selective adoption of {cutting_edge['name']} patterns"
            return middle_ground

    async def _synthesize_implementation_steps(
        self,
        cutting_edge_steps: List[Dict[str, Any]],
        conservative_steps: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> List[ImplementationStep]:
        """Synthesize implementation steps from both approaches"""
        synthesized_steps = []
        
        # Combine and optimize steps
        all_step_names = set()
        for step in cutting_edge_steps + conservative_steps:
            all_step_names.add(step['title'])
        
        step_id = 1
        for step_name in sorted(all_step_names):
            cutting_edge_step = next((s for s in cutting_edge_steps if s['title'] == step_name), None)
            conservative_step = next((s for s in conservative_steps if s['title'] == step_name), None)
            
            if cutting_edge_step and conservative_step:
                # Merge the steps
                synthesized_step = self._merge_implementation_steps(cutting_edge_step, conservative_step, step_id)
                synthesized_steps.append(synthesized_step)
            elif cutting_edge_step:
                # Adapt cutting-edge step for synthesis
                adapted_step = self._adapt_step_for_synthesis(cutting_edge_step, step_id, "cutting_edge")
                synthesized_steps.append(adapted_step)
            elif conservative_step:
                # Adapt conservative step for synthesis
                adapted_step = self._adapt_step_for_synthesis(conservative_step, step_id, "conservative")
                synthesized_steps.append(adapted_step)
            
            step_id += 1
        
        return synthesized_steps

    def _merge_implementation_steps(self, cutting_edge_step: Dict[str, Any], conservative_step: Dict[str, Any], step_id: int) -> ImplementationStep:
        """Merge two similar steps into an optimized synthesis step"""
        # Take the average effort and middle complexity
        avg_effort = (cutting_edge_step['estimated_effort_hours'] + conservative_step['estimated_effort_hours']) / 2
        
        # Combine risks and deliverables
        combined_risks = list(set(cutting_edge_step['risks'] + conservative_step['risks']))
        combined_deliverables = list(set(cutting_edge_step['deliverables'] + conservative_step['deliverables']))
        combined_technologies = list(set(cutting_edge_step['technologies'] + conservative_step['technologies']))
        
        return ImplementationStep(
            id=f"synthesis_step_{step_id}",
            title=f"Synthesized: {cutting_edge_step['title']}",
            description=f"Balanced approach combining {cutting_edge_step['description'][:50]}... with proven practices",
            estimated_effort_hours=avg_effort,
            complexity=ImplementationComplexity.MODERATE,  # Default to moderate for synthesis
            dependencies=cutting_edge_step.get('dependencies', []),
            risks=combined_risks[:5],  # Limit to top 5 risks
            deliverables=combined_deliverables[:5],  # Limit to top 5 deliverables
            validation_criteria=conservative_step.get('validation_criteria', []),  # Use conservative validation
            technologies=combined_technologies
        )

    def _adapt_step_for_synthesis(self, step: Dict[str, Any], step_id: int, step_type: str) -> ImplementationStep:
        """Adapt a step from one approach for the synthesis plan"""
        return ImplementationStep(
            id=f"synthesis_step_{step_id}",
            title=f"Adapted: {step['title']}",
            description=f"Synthesis-adapted: {step['description']}",
            estimated_effort_hours=step['estimated_effort_hours'],
            complexity=ImplementationComplexity(step['complexity']) if isinstance(step['complexity'], str) else ImplementationComplexity.MODERATE,
            dependencies=step.get('dependencies', []),
            risks=step.get('risks', []),
            deliverables=step.get('deliverables', []),
            validation_criteria=step.get('validation_criteria', []),
            technologies=step.get('technologies', [])
        )

    # Synthesis helper methods
    def _find_technology_overlap(self, plan1: Dict[str, Any], plan2: Dict[str, Any]) -> List[str]:
        """Find technologies that appear in both plans"""
        tech1 = {t['name'] for t in plan1.get('technology_stack', [])}
        tech2 = {t['name'] for t in plan2.get('technology_stack', [])}
        return list(tech1.intersection(tech2))

    def _identify_complementary_strengths(self, plan1: Dict[str, Any], plan2: Dict[str, Any]) -> Dict[str, List[str]]:
        """Identify complementary strengths between plans"""
        return {
            "cutting_edge_strengths": plan1.get('pros', []),
            "conservative_strengths": plan2.get('pros', []),
            "combined_benefits": ["Balanced innovation-stability profile", "Risk-mitigated advancement"]
        }

    def _find_risk_mitigation_opportunities(self, plan1: Dict[str, Any], plan2: Dict[str, Any]) -> List[str]:
        """Find opportunities to mitigate risks by combining approaches"""
        cutting_edge_risks = set(plan1.get('failure_risks', []))
        conservative_strengths = set(plan2.get('success_factors', []))
        
        # Find where conservative strengths can mitigate cutting-edge risks
        mitigations = []
        for risk in cutting_edge_risks:
            for strength in conservative_strengths:
                if any(word in risk.lower() and word in strength.lower() for word in ['stability', 'reliability', 'testing']):
                    mitigations.append(f"Use {strength} to mitigate {risk}")
        
        return mitigations

    def _analyze_effort_optimization(self, plan1: Dict[str, Any], plan2: Dict[str, Any]) -> Dict[str, float]:
        """Analyze effort optimization opportunities"""
        return {
            "cutting_edge_effort": plan1.get('estimated_total_hours', 0),
            "conservative_effort": plan2.get('estimated_total_hours', 0),
            "synthesis_estimated_savings": 0.15  # 15% savings from optimization
        }

    # Synthesis combination methods
    def _synthesize_architecture_decisions(self, plan1: Dict[str, Any], plan2: Dict[str, Any]) -> List[str]:
        """Synthesize architecture decisions"""
        decisions = []
        decisions.extend(plan2.get('architecture_decisions', [])[:2])  # Take conservative base
        decisions.extend(plan1.get('architecture_decisions', [])[:1])  # Add selective innovation
        decisions.append("Implement hybrid architecture with stability core and innovation edge")
        return decisions

    def _synthesize_quality_measures(self, plan1: Dict[str, Any], plan2: Dict[str, Any]) -> List[str]:
        """Synthesize quality measures"""
        measures = []
        measures.extend(plan2.get('quality_measures', []))  # Conservative quality base
        measures.append("Innovation validation through controlled experiments")
        return measures

    def _synthesize_deployment_strategy(self, plan1: Dict[str, Any], plan2: Dict[str, Any]) -> str:
        """Synthesize deployment strategy"""
        return "Progressive deployment with conservative base and experimental features behind feature flags"

    def _synthesize_maintenance_considerations(self, plan1: Dict[str, Any], plan2: Dict[str, Any]) -> List[str]:
        """Synthesize maintenance considerations"""
        considerations = []
        considerations.extend(plan2.get('maintenance_considerations', [])[:3])  # Conservative base
        considerations.append("Monitoring and rollback plans for experimental features")
        return considerations

    def _synthesize_pros(self, plan1: Dict[str, Any], plan2: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Synthesize pros from both plans"""
        return [
            "Balanced risk-reward profile",
            "Leverages proven practices with selective innovation",
            "Future-ready architecture with stable foundation",
            "Manageable complexity with growth potential"
        ]

    def _synthesize_cons(self, plan1: Dict[str, Any], plan2: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Synthesize cons from both plans"""
        return [
            "Requires careful technology integration",
            "May not maximize either innovation or stability",
            "Complex decision-making for technology choices",
            "Potential for over-engineering in pursuit of balance"
        ]

    def _synthesize_success_factors(self, plan1: Dict[str, Any], plan2: Dict[str, Any]) -> List[str]:
        """Synthesize success factors"""
        return [
            "Clear technology selection criteria",
            "Strong change management processes",
            "Team training on balanced approach",
            "Effective monitoring and rollback capabilities"
        ]

    def _synthesize_failure_risks(self, plan1: Dict[str, Any], plan2: Dict[str, Any]) -> List[str]:
        """Synthesize failure risks"""
        return [
            "Technology integration challenges",
            "Team resistance to hybrid approach",
            "Complexity management failures",
            "Inadequate testing of integrated solution"
        ]


# Factory functions for creating planner agents
def create_cutting_edge_planner(
    agent_id: str,
    llm_config: Dict[str, Any],
    mcp_clients: Dict[str, Any],
    rag_pipeline: Optional[RAGPipeline] = None
) -> CuttingEdgePlannerAgent:
    """Create a cutting-edge planner agent"""
    return CuttingEdgePlannerAgent(
        agent_id=agent_id,
        role=AgentRole.TASK_PLANNER,  # Using existing role enum
        name="Cutting-Edge Planner",
        llm_config=llm_config,
        mcp_clients=mcp_clients,
        rag_pipeline=rag_pipeline
    )


def create_conservative_planner(
    agent_id: str,
    llm_config: Dict[str, Any],
    mcp_clients: Dict[str, Any],
    rag_pipeline: Optional[RAGPipeline] = None
) -> ConservativePlannerAgent:
    """Create a conservative planner agent"""
    return ConservativePlannerAgent(
        agent_id=agent_id,
        role=AgentRole.TASK_PLANNER,
        name="Conservative Planner",
        llm_config=llm_config,
        mcp_clients=mcp_clients,
        rag_pipeline=rag_pipeline
    )


def create_synthesis_planner(
    agent_id: str,
    llm_config: Dict[str, Any],
    mcp_clients: Dict[str, Any],
    rag_pipeline: Optional[RAGPipeline] = None
) -> SynthesisPlannerAgent:
    """Create a synthesis planner agent"""
    return SynthesisPlannerAgent(
        agent_id=agent_id,
        role=AgentRole.TASK_PLANNER,
        name="Synthesis Planner",
        llm_config=llm_config,
        mcp_clients=mcp_clients,
        rag_pipeline=rag_pipeline
    )
