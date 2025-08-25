"""
Sophia AI Enhanced Repository Analyst Agent

Advanced repository analysis agent with embedding-powered intelligence.
Integrates with RAG pipeline for deep codebase understanding and pattern recognition.

Key Features:
- Semantic code analysis using embeddings
- Repository pattern recognition and extraction
- Code quality assessment and recommendations
- Architecture evaluation and optimization suggestions
- Integration with RAG pipeline for contextual analysis
- Dependency mapping and impact analysis

Version: 2.0.0
Author: Sophia AI Intelligence Team
"""

import asyncio
import json
import logging
import re
import ast
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path

from .base_agent import SophiaAgent, AgentRole, AgentTask, TaskPriority, TaskStatus
from .embedding.embedding_engine import EmbeddingEngine, CodeChunk, ChunkType
from .embedding.rag_pipeline import RAGPipeline, RetrievalQuery, ContextType, RetrievalStrategy
from .communication import message_bus

logger = logging.getLogger(__name__)


@dataclass
class RepositoryPattern:
    """Represents a pattern found in the repository"""
    pattern_type: str
    name: str
    description: str
    files_involved: List[str]
    confidence_score: float
    examples: List[str]
    benefits: List[str]
    potential_issues: List[str]
    recommendations: List[str]


@dataclass
class CodeQualityInsight:
    """Represents a code quality insight"""
    insight_type: str
    severity: str  # info, warning, critical
    title: str
    description: str
    affected_files: List[str]
    code_examples: List[str]
    recommendations: List[str]
    confidence: float
    impact_score: float


class EnhancedRepositoryAnalystAgent(SophiaAgent):
    """
    Enhanced Repository Analyst Agent with embedding-powered intelligence
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        llm_config: Dict[str, Any],
        mcp_clients: Dict[str, Any],
        embedding_engine: Optional[EmbeddingEngine] = None,
        rag_pipeline: Optional[RAGPipeline] = None
    ):
        super().__init__(
            agent_id=agent_id,
            role=AgentRole.REPOSITORY_ANALYST,
            name=name,
            llm_config=llm_config,
            mcp_clients=mcp_clients
        )
        
        self.embedding_engine = embedding_engine
        self.rag_pipeline = rag_pipeline
        
        # Analysis cache
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        self.chunk_cache: Dict[str, List[CodeChunk]] = {}

    def _initialize_capabilities(self):
        """Initialize repository analyst capabilities"""
        capabilities = [
            "handle_repository_analysis",
            "handle_pattern_recognition", 
            "handle_dependency_analysis",
            "handle_quality_assessment",
            "handle_code_similarity_analysis"
        ]
        
        for capability in capabilities:
            self.context.add_capability(capability)

    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute repository analysis task"""
        try:
            if task.task_type == "repository_analysis":
                return await self._perform_repository_analysis(task)
            elif task.task_type == "pattern_recognition":
                return await self._analyze_patterns(task)
            elif task.task_type == "quality_assessment":
                return await self._assess_code_quality(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
                
        except Exception as e:
            logger.error(f"Repository analysis task failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_type": "EnhancedRepositoryAnalyst"
            }

    async def _perform_repository_analysis(self, task: AgentTask) -> Dict[str, Any]:
        """Perform comprehensive repository analysis"""
        logger.info("Starting repository analysis")
        
        # Get repository chunks
        chunks = await self._get_repository_chunks()
        
        if not chunks:
            return {
                "success": False,
                "error": "Could not retrieve repository content"
            }
        
        # Analyze structure
        structure_analysis = await self._analyze_structure(chunks)
        
        # Detect patterns
        patterns = await self._detect_patterns(chunks)
        
        # Assess quality
        quality_insights = await self._analyze_quality(chunks)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(chunks, quality_insights)
        
        result = {
            "success": True,
            "analysis": {
                "structure": structure_analysis,
                "patterns": patterns,
                "quality_insights": quality_insights,
                "recommendations": recommendations,
                "chunks_analyzed": len(chunks),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Cache result
        self.analysis_cache[task.id] = result
        
        return result

    async def _get_repository_chunks(self) -> List[CodeChunk]:
        """Get repository chunks from GitHub MCP service"""
        if not self.mcp_clients.get('github'):
            logger.error("GitHub MCP client not available")
            return []
        
        try:
            github_client = self.mcp_clients['github']
            repo_structure = await github_client.get('/repo/tree', params={'path': '', 'ref': 'main'})
            
            if not repo_structure or 'entries' not in repo_structure:
                return []
            
            all_chunks = []
            file_count = 0
            max_files = 50  # Limit for performance
            
            for entry in repo_structure['entries']:
                if entry['type'] == 'file' and file_count < max_files:
                    try:
                        file_response = await github_client.get('/repo/file', params={'path': entry['path']})
                        
                        if file_response and 'content' in file_response:
                            import base64
                            content = base64.b64decode(file_response['content']).decode('utf-8', errors='ignore')
                            language = self._detect_language(entry['name'])
                            
                            if self.embedding_engine:
                                file_chunks = await self.embedding_engine.process_file(
                                    entry['path'], content, language
                                )
                                all_chunks.extend(file_chunks)
                            else:
                                chunk = CodeChunk(
                                    id=f"basic_{entry['path']}",
                                    content=content,
                                    chunk_type=ChunkType.FILE,
                                    language=language,
                                    file_path=entry['path'],
                                    start_line=1,
                                    end_line=len(content.split('\n'))
                                )
                                all_chunks.append(chunk)
                        
                        file_count += 1
                        
                    except Exception as e:
                        logger.warning(f"Failed to process file {entry['path']}: {e}")
                        continue
            
            logger.info(f"Processed {file_count} files into {len(all_chunks)} chunks")
            return all_chunks
            
        except Exception as e:
            logger.error(f"Failed to get repository chunks: {e}")
            return []

    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename"""
        language_map = {
            '.py': 'python',
            '.js': 'javascript', 
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.sql': 'sql',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown'
        }
        
        extension = Path(filename).suffix.lower()
        return language_map.get(extension, 'unknown')

    async def _analyze_structure(self, chunks: List[CodeChunk]) -> Dict[str, Any]:
        """Analyze repository structure"""
        structure = {
            'total_files': 0,
            'total_lines': 0,
            'languages': {},
            'directories': set(),
            'file_types': {}
        }
        
        for chunk in chunks:
            if chunk.chunk_type == ChunkType.FILE:
                structure['total_files'] += 1
                structure['total_lines'] += chunk.end_line - chunk.start_line + 1
                
                lang = chunk.language
                structure['languages'][lang] = structure['languages'].get(lang, 0) + 1
                
                structure['directories'].add(str(Path(chunk.file_path).parent))
                
                extension = Path(chunk.file_path).suffix
                structure['file_types'][extension] = structure['file_types'].get(extension, 0) + 1
        
        # Convert set to list for JSON serialization
        structure['directories'] = list(structure['directories'])
        
        # Determine primary language
        if structure['languages']:
            structure['primary_language'] = max(structure['languages'].items(), key=lambda x: x[1])[0]
        else:
            structure['primary_language'] = 'unknown'
        
        return structure

    async def _detect_patterns(self, chunks: List[CodeChunk]) -> Dict[str, Any]:
        """Detect architectural and design patterns"""
        patterns = {
            'microservices': False,
            'layered_architecture': False,
            'mvc': False,
            'repository_pattern': False
        }
        
        file_paths = [chunk.file_path for chunk in chunks]
        
        # Detect microservices pattern
        service_dirs = [path for path in file_paths if 'service' in path.lower()]
        if len(service_dirs) >= 3:
            patterns['microservices'] = True
        
        # Detect layered architecture
        layers = ['presentation', 'business', 'data', 'layer']
        layer_matches = sum(1 for layer in layers if any(layer in path.lower() for path in file_paths))
        if layer_matches >= 2:
            patterns['layered_architecture'] = True
        
        # Detect MVC pattern
        mvc_components = ['model', 'view', 'controller']
        mvc_matches = sum(1 for comp in mvc_components if any(comp in path.lower() for path in file_paths))
        if mvc_matches >= 2:
            patterns['mvc'] = True
        
        # Detect repository pattern
        repo_files = [path for path in file_paths if 'repository' in path.lower() or 'repo' in path.lower()]
        if len(repo_files) >= 2:
            patterns['repository_pattern'] = True
        
        return patterns

    async def _analyze_quality(self, chunks: List[CodeChunk]) -> List[CodeQualityInsight]:
        """Analyze code quality"""
        insights = []
        
        # Complexity analysis
        high_complexity_count = 0
        for chunk in chunks:
            if chunk.chunk_type in [ChunkType.FUNCTION, ChunkType.METHOD]:
                complexity = self._estimate_complexity(chunk.content)
                if complexity > 0.7:
                    high_complexity_count += 1
        
        if high_complexity_count > 0:
            insights.append(CodeQualityInsight(
                insight_type="complexity",
                severity="warning",
                title="High Complexity Functions Detected",
                description=f"Found {high_complexity_count} functions with high complexity",
                affected_files=[],
                code_examples=[],
                recommendations=["Refactor complex functions", "Add unit tests", "Extract helper methods"],
                confidence=0.8,
                impact_score=min(high_complexity_count / 10, 1.0)
            ))
        
        # Documentation analysis
        documented_functions = 0
        total_functions = 0
        
        for chunk in chunks:
            if chunk.chunk_type in [ChunkType.FUNCTION, ChunkType.METHOD]:
                total_functions += 1
                if self._has_documentation(chunk.content):
                    documented_functions += 1
        
        if total_functions > 0:
            doc_ratio = documented_functions / total_functions
            if doc_ratio < 0.6:
                insights.append(CodeQualityInsight(
                    insight_type="documentation",
                    severity="warning",
                    title="Low Documentation Coverage",
                    description=f"Only {doc_ratio:.1%} of functions are documented",
                    affected_files=[],
                    code_examples=[],
                    recommendations=["Add docstrings", "Include inline comments", "Create README files"],
                    confidence=0.9,
                    impact_score=1.0 - doc_ratio
                ))
        
        return insights

    def _estimate_complexity(self, content: str) -> float:
        """Estimate code complexity"""
        factors = [
            len(re.findall(r'\bif\b', content)) * 0.1,
            len(re.findall(r'\bfor\b|\bwhile\b', content)) * 0.15,
            len(re.findall(r'\btry\b|\bcatch\b', content)) * 0.1,
            len(content.split('\n')) * 0.001
        ]
        return min(sum(factors), 1.0)

    def _has_documentation(self, content: str) -> bool:
        """Check if content has documentation"""
        if '"""' in content or "'''" in content or '/**' in content:
            return True
        
        comment_lines = [line for line in content.split('\n') if line.strip().startswith(('#', '//', '*'))]
        total_lines = len([line for line in content.split('\n') if line.strip()])
        
        if total_lines > 0:
            return len(comment_lines) / total_lines > 0.1
        
        return False

    async def _generate_recommendations(
        self, 
        chunks: List[CodeChunk], 
        quality_insights: List[CodeQualityInsight]
    ) -> Dict[str, List[str]]:
        """Generate recommendations based on analysis"""
        recommendations = {
            'prioritized': [],
            'refactoring': [],
            'optimization': []
        }
        
        # Based on quality insights
        critical_insights = [i for i in quality_insights if i.severity == 'critical']
        warning_insights = [i for i in quality_insights if i.severity == 'warning']
        
        if critical_insights:
            recommendations['prioritized'].append(f"Address {len(critical_insights)} critical issues")
        
        if warning_insights:
            recommendations['prioritized'].append(f"Resolve {len(warning_insights)} warning issues")
        
        # General recommendations
        file_paths = [chunk.file_path for chunk in chunks]
        
        if not any('test' in path.lower() for path in file_paths):
            recommendations['prioritized'].append("Add comprehensive test suite")
        
        recommendations['refactoring'].append("Review code organization and structure")
        recommendations['optimization'].append("Consider performance optimizations")
        
        return recommendations

    async def _analyze_patterns(self, task: AgentTask) -> Dict[str, Any]:
        """Focused pattern analysis"""
        chunks = await self._get_repository_chunks()
        patterns = await self._detect_patterns(chunks)
        
        return {
            "success": True,
            "patterns": patterns,
            "total_patterns": sum(1 for v in patterns.values() if v)
        }

    async def _assess_code_quality(self, task: AgentTask) -> Dict[str, Any]:
        """Focused code quality assessment"""
        chunks = await self._get_repository_chunks()
        quality_insights = await self._analyze_quality(chunks)
        
        return {
            "success": True,
            "quality_insights": [asdict(insight) for insight in quality_insights],
            "total_insights": len(quality_insights)
        }


# Factory function
def create_repository_analyst(
    agent_id: str,
    llm_config: Dict[str, Any],
    mcp_clients: Dict[str, Any],
    embedding_model: str = "all-mpnet-base-v2"
) -> EnhancedRepositoryAnalystAgent:
    """Create an enhanced repository analyst agent"""
    
    embedding_engine = EmbeddingEngine(embedding_model=embedding_model)
    rag_pipeline = RAGPipeline(embedding_engine=embedding_engine, mcp_clients=mcp_clients)
    
    return EnhancedRepositoryAnalystAgent(
        agent_id=agent_id,
        name="Enhanced Repository Analyst",
        llm_config=llm_config,
        mcp_clients=mcp_clients,
        embedding_engine=embedding_engine,
        rag_pipeline=rag_pipeline
    )
