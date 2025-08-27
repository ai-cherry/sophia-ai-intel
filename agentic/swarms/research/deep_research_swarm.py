# Sophia AI Deep Research Swarm
# ================================
# Enhanced multi-connector research swarm with advanced web scraping capabilities

import logging
from typing import Dict, List, Optional, Any, Union
from agno.agent import Agent
from agno.models.gemini import Gemini
from agno.team import Team
from agno.tools.tavily import TavilyTools
from agno.tools.youtube import YouTubeTools
from agno.tools.finance import FinanceTools
from agno.storage.redis import RedisMemory
from agno.storage.qdrant import QdrantMemory
from agno.memory import AgentMemory

from ...core.config import get_config, get_model_catalog
from ...core.base_agent import SophiaAgentFactory
from ...core.utils import SophiaAgentTools

logger = logging.getLogger(__name__)


class DeepResearchSwarm:
    """Enhanced deep research swarm with multi-connector tools for comprehensive information gathering"""

    def __init__(self):
        self.config = get_config()
        self.factory = SophiaAgentFactory()
        self._research_team = None
        self._tools_created = False

    def _create_research_tools(self) -> List[Any]:
        """Create and configure all available research tools with proper API integration"""

        research_tools = []
        tools_config = self.config

        # 1. Tavily AI Search Tool (AI-powered search and summarization)
        if hasattr(tools_config, 'tavily_api_key') and tools_config.tavily_api_key:
            tavily_tools = TavilyTools(api_key=tools_config.tavily_api_key)
            research_tools.append(tavily_tools)

        # 2. Perplexity AI Search Tool (Competitive intelligence and analysis)
        if hasattr(tools_config, 'perplexity_api_key') and tools_config.perplexity_api_key:
            perplexity_tools = SophiaAgentTools.PerplexitySearch(api_key=tools_config.perplexity_api_key)
            research_tools.append(perplexity_tools)

        # 3. Serper.dev Tool (Google Custom Search with structured results)
        if hasattr(tools_config, 'serper_api_key') and tools_config.serper_api_key:
            serper_tools = SophiaAgentTools.GoogleCustomSearch(api_key=tools_config.serper_api_key)
            research_tools.append(serper_tools)

        # 4. Apify Tools (Web scraping and data extraction)
        if hasattr(tools_config, 'apify_api_token') and tools_config.apify_api_token:
            apify_tools = SophiaAgentTools.ApifyScraping(api_token=tools_config.apify_api_token)
            research_tools.append(apify_tools)

        # 5. ZenRows Tool (Advanced web scraping with anti-detection)
        if hasattr(tools_config, 'zenrows_api_key') and tools_config.zenrows_api_key:
            zenrows_tools = SophiaAgentTools.ZenRowsScraping(api_key=tools_config.zenrows_api_key)
            research_tools.append(zenrows_tools)

        # 6. BrightData Tools (Enterprise scraping with global proxy networks)
        if hasattr(tools_config, 'brightdata_api_key') and tools_config.brightdata_api_key:
            brightdata_tools = SophiaAgentTools.BrightDataScraping(api_key=tools_config.brightdata_api_key)
            research_tools.append(brightdata_tools)

        # 7. Exa AI Tools (Search with memory and context)
        if hasattr(tools_config, 'exa_api_key') and tools_config.exa_api_key:
            exa_tools = SophiaAgentTools.ExaAISearch(api_key=tools_config.exa_api_key)
            research_tools.append(exa_tools)

        # 8. Finance Tools (Market data integration)
        finance_tools = FinanceTools()
        research_tools.append(finance_tools)

        # 9. YouTube Analysis Tools (Media and content analysis)
        youtube_tools = YouTubeTools()
        research_tools.append(youtube_tools)

        # 10. Custom Research Tools (Document processing, sentiment analysis)
        custom_research_tools = SophiaAgentTools.CustomResearchTools()
        research_tools.append(custom_research_tools)

        logger.info(f"Created {len(research_tools)} research tools for deep research swarm")
        return research_tools

    def _create_research_team(self) -> Team:
        """Create and configure the deep research team with specialized agents"""

        # Configuration for the research team
        tool_instructions = [
            "Use all available search and scraping tools to gather comprehensive information",
            "Verify information across multiple sources when possible",
            "Provide structured outputs with clear citations and sources",
            "Identify and extract key insights, trends, and patterns from gathered data",
            "Synthesize information into actionable intelligence",
            "Always include confidence levels for key findings and note any limitations"
        ]

        # Create WebScraper Agent (Primary research gatherer)
        web_scraper = self.factory.create_agent(
            agent_type="research",
            name="WebScraper",
            role="Senior Web Scraper and Content Extractor specializing in comprehensive information gathering",
            instructions=[
                "You are the primary information gatherer for the research swarm.",
                "Use web scraping tools to extract comprehensive data from target websites.",
                "Handle dynamic content and JavaScript-heavy sites using appropriate tools.",
                "Extract structured information and present it clearly.",
                "Always verify data quality and note any scraping limitations encountered."
            ] + tool_instructions
        )

        # Create AcademicMiner Agent (Scholarly research)
        academic_miner = self.factory.create_agent(
            agent_type="research",
            name="AcademicMiner",
            role="Academic Research Specialist focused on scholarly papers and academic sources",
            instructions=[
                "You are responsible for academic and scholarly research.",
                "Search academic databases, arXiv, and scholarly journals.",
                "Identify key researchers, studies, and academic trends.",
                "Summarize complex academic findings for non-technical audiences.",
                "Provide citations and reference academic sources properly."
            ] + tool_instructions
        )

        # Create PatentHunter Agent (Patent and IP research)
        patent_hunter = self.factory.create_agent(
            agent_type="research",
            name="PatentHunter",
            role="Patent Research Specialist focused on intellectual property and innovations",
            instructions=[
                "You specialize in patent research and intellectual property analysis.",
                "Search patent databases for relevant inventions and innovations.",
                "Analyze patent landscapes and identify competitive developments.",
                "Extract technical details and assess innovation trends.",
                "Consider both defensive and offensive IP strategies."
            ] + tool_instructions
        )

        # Create MarketSentimentCrawler (Market analysis and sentiment)
        sentiment_crawler = self.factory.create_agent(
            agent_type="research",
            name="MarketSentimentCrawler",
            role="Market Sentiment and Social Media Analysis Specialist",
            instructions=[
                "You analyze market sentiment and social media signals.",
                "Monitor social media platforms, news outlets, and financial forums.",
                "Track trending topics and sentiment shifts.",
                "Correlate social signals with market movements.",
                "Provide timely intelligence on market psychology."
            ] + tool_instructions
        )

        # Create BrowserAutomator Agent (Advanced web automation)
        browser_automator = self.factory.create_agent(
            agent_type="research",
            name="BrowserAutomator",
            role="Web Automation Specialist for dynamic content and complex sites",
            instructions=[
                "You specialize in automating complex web interactions.",
                "Interact with dynamic web applications and forms.",
                "Handle login-protected content and multi-step processes.",
                "Extract data from interactive dashboards and reports.",
                "Navigate complex website structures efficiently."
            ] + tool_instructions
        )

        # Create Coordinator Agent (Research synthesis and orchestration)
        coordinator = self.factory.create_agent(
            agent_type="research",
            name="ResearchCoordinator",
            role="Research Coordination Director responsible for orchestrating the deep research process",
            instructions=[
                "You are the senior director overseeing the entire deep research process.",
                "Coordinate between different research agents and ensure comprehensive analysis.",
                "Synthesize findings from multiple sources into cohesive intelligence.",
                "Identify knowledge gaps and direct additional research as needed.",
                "Produce final reports with executive summaries and actionable recommendations.",
                "Track research quality and ensure all aspects are thoroughly covered."
            ] + tool_instructions
        )

        # Create the research team with coordinated workflow
        research_team = Team(
            name="DeepResearchSwarm",
            mode="automatic",
            add_datetime_to_instructions=True,
            show_tool_calls=True,
            markdown=True,
            debug=self.config.debug,
            agents=[web_scraper, academic_miner, patent_hunter, sentiment_crawler, browser_automator, coordinator],
            model=self.factory._get_model_instance(
                get_model_catalog().get_model_config("research").primary_model
            ),
            instructions=[
                "This is a sophisticated deep research team capable of comprehensive information gathering.",
                "Each agent has specialized tools and expertise for different research domains.",
                "Work together to provide complete intelligence covering web, academic, patent, and sentiment analysis.",
                "Coordinate efforts to avoid duplication and ensure all aspects are covered.",
                "Provide structured, actionable intelligence with clear sourcing and confidence levels.",
                "Deliver analysis in multiple formats: executive summaries, detailed reports, and actionable recommendations."
            ]
        )

        logger.info("Created DeepResearchSwarm team with 6 specialized agents")
        return research_team

    def run_deep_research(self,
                          research_topic: str,
                          research_scope: str = "comprehensive",
                          include_sources: bool = True,
                          output_format: str = "comprehensive") -> Dict[str, Any]:
        """
        Execute deep research on a given topic using all available tools

        Args:
            research_topic: The main topic to research
            research_scope: Scope of research ('comprehensive', 'industry', 'company', 'academic')
            include_sources: Whether to include detailed source citations
            output_format: Output format ('comprehensive', 'brief', 'technical', 'business')

        Returns:
            Dictionary containing research results and metadata
        """

        # Create research tools if not already created
        if not self._tools_created:
            research_tools = self._create_research_tools()
            self._tools_created = True

        # Create research team if not already created
        if self._research_team is None:
            self._research_team = self._create_research_team()

        # Prepare research prompt based on scope and format
        research_prompt = self._prepare_research_prompt(
            topic=research_topic,
            scope=research_scope,
            include_sources=include_sources,
            output_format=output_format
        )

        logger.info(f"Starting deep research on: {research_topic}")

        try:
            # Run the research through the team
            result = self._research_team.run(research_prompt)

            # Process and structure the results
            processed_results = self._process_research_results(result, output_format)

            return {
                "topic": research_topic,
                "scope": research_scope,
                "results": processed_results,
                "metadata": {
                    "created_at": self.factory.config.redis_url  # Use UTC time
                    "agents_used": ["WebScraper", "AcademicMiner", "PatentHunter",
                                   "MarketSentimentCrawler", "BrowserAutomator", "ResearchCoordinator"],
                    "tools_used": self._get_used_tools_list(),
                    "confidence_score": self._calculate_research_confidence(processed_results)
                },
                "sources": self._extract_sources(processed_results) if include_sources else []
            }

        except Exception as e:
            logger.error(f"Error during deep research: {str(e)}")
            raise

    def _prepare_research_prompt(self,
                                topic: str,
                                scope: str,
                                include_sources: bool,
                                output_format: str) -> str:
        """Prepare a structured research prompt based on parameters"""

        scope_instructions = {
            "comprehensive": "Conduct thorough research covering all aspects including technical, business, competitive, and market analysis",
            "industry": "Focus on industry trends, market dynamics, and sector analysis",
            "company": "Focus on company-specific analysis including financials, strategy, and competitive position",
            "academic": "Focus on academic research, scholarly papers, and theoretical foundations"
        }

        format_instructions = {
            "comprehensive": "Provide detailed analysis with executive summary, methodology, findings, and recommendations",
            "brief": "Provide concise summary with key findings and recommendations only",
            "technical": "Focus on technical analysis with detailed specifications and technical insights",
            "business": "Focus on business implications, market opportunities, and strategic recommendations"
        }

        prefix = "You are conducting advanced research using multiple sophisticated tools. "
        topic_context = f"Research Topic: {topic}"
        scope_context = f"Scope: {scope_instructions[scope]}"
        format_context = f"Output Format: {format_instructions[output_format]}"

        source_instruction = " Include detailed source citations and verification notes" if include_sources else ""

        research_instructions = """
        1. Use all available research tools to gather comprehensive information
        2. Verify information across multiple sources to ensure accuracy
        3. Identify key patterns, trends, and insights from the data
        4. Consider both qualitative and quantitative aspects
        5. Provide confidence levels where appropriate
        6. Structure your findings clearly with sections and subsections
        7. Include actionable recommendations based on your findings

        The research swarm has specialized agents:
        - WebScraper: Primary information gathering from websites
        - AcademicMiner: Scholarly research and academic papers
        - PatentHunter: Patent and IP analysis
        - MarketSentimentCrawler: Social media and market sentiment analysis
        - BrowserAutomator: Automation for complex web interactions
        - ResearchCoordinator: Overall coordination and synthesis
        """

        final_prompt = f"{prefix} {topic_context}. {scope_context}. {format_context}.{source_instruction} {research_instructions}"

        return final_prompt

    def _process_research_results(self, result: Any, output_format: str) -> Dict[str, Any]:
        """Process and structure research results"""

        if hasattr(result, 'content'):
            content = result.content
        elif hasattr(result, 'response'):
            content = result.response
        else:
            content = str(result)

        # Structure the results based on format
        if output_format == "brief":
            processed = self._format_brief_results(content)
        elif output_format == "technical":
            processed = self._format_technical_results(content)
        elif output_format == "business":
            processed = self._format_business_results(content)
        else:  # comprehensive
            processed = self._format_comprehensive_results(content)

        return processed

    def _format_comprehensive_results(self, content: str) -> Dict[str, Any]:
        """Format results into comprehensive structure"""
        return {
            "executive_summary": self._extract_section(content, "Executive Summary", "Key Findings"),
            "methodology": self._extract_section(content, "Methodology", "Findings"),
            "findings": self._extract_section(content, "Findings", "Analysis"),
            "analysis": self._extract_section(content, "Analysis", "Recommendations"),
            "recommendations": self._extract_section(content, "Recommendations", "Conclusion"),
            "conclusion": self._extract_section(content, "Conclusion", ""),
            "raw_content": content
        }

    def _format_brief_results(self, content: str) -> Dict[str, Any]:
        """Format results into brief structure"""
        return {
            "key_findings": self._extract_section(content, "Key Findings", "Recommendations"),
            "recommendations": self._extract_section(content, "Recommendations", ""),
            "raw_content": content
        }

    def _format_technical_results(self, content: str) -> Dict[str, Any]:
        """Format results into technical structure"""
        return {
            "technical_specifications": self._extract_section(content, "Technical Specifications", "Implementation"),
            "implementation_details": self._extract_section(content, "Implementation", "Technical Recommendations"),
            "technical_recommendations": self._extract_section(content, "Technical Recommendations", ""),
            "raw_content": content
        }

    def _format_business_results(self, content: str) -> Dict[str, Any]:
        """Format results into business structure"""
        return {
            "market_analysis": self._extract_section(content, "Market Analysis", "Competitive Landscape"),
            "competitive_landscape": self._extract_section(content, "Competitive Landscape", "Strategic Opportunities"),
            "strategic_opportunities": self._extract_section(content, "Strategic Opportunities", "Business Recommendations"),
            "business_recommendations": self._extract_section(content, "Business Recommendations", ""),
            "raw_content": content
        }

    def _extract_section(self, content: str, start_marker: str, end_marker: str) -> str:
        """Extract a section from the content based on markers"""
        try:
            start_idx = content.lower().find(start_marker.lower())
            if start_idx == -1:
                return "Section not found"

            content_from_start = content[start_idx:]

            if end_marker:
                end_idx = content_from_start.lower().find(end_marker.lower())
                if end_idx != -1:
                    return content_from_start[:end_idx].strip()

            return content_from_start.strip()
        except Exception:
            return "Error extracting section"

    def _get_used_tools_list(self) -> List[str]:
        """Get list of tools that were available for use in the research"""
        tools_list = []
        tools_config = self.config

        if hasattr(tools_config, 'tavily_api_key') and tools_config.tavily_api_key:
            tools_list.append("Tavily AI Search")
        if hasattr(tools_config, 'perplexity_api_key') and tools_config.perplexity_api_key:
            tools_list.append("Perplexity AI Search")
        if hasattr(tools_config, 'serper_api_key') and tools_config.serper_api_key:
            tools_list.append("Google Custom Search (Serper)")
        if hasattr(tools_config, 'apify_api_token') and tools_config.apify_api_token:
            tools_list.append("Apify Web Scraping")
        if hasattr(tools_config, 'zenrows_api_key') and tools_config.zenrows_api_key:
            tools_list.append("ZenRows Advanced Scraping")
        if hasattr(tools_config, 'brightdata_api_key') and tools_config.brightdata_api_key:
            tools_list.append("BrightData Enterprise Scraping")
        if hasattr(tools_config, 'exa_api_key') and tools_config.exa_api_key:
            tools_list.append("Exa AI Search")
        tools_list.extend(["Finance Tools", "YouTube Tools", "Custom Research Tools"])

        return tools_list

    def _calculate_research_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate overall confidence score for research results"""
        confidence_indicators = [
            len(results.get("findings", "")) > 100,
            len(results.get("analysis", "")) > 100,
            len(results.get("recommendations", "")) > 100,
            "sources" in results,
            "metadata" in results
        ]

        confidence_score = sum(confidence_indicators) / len(confidence_indicators)
        return round(confidence_score * 100, 2)  # Return as percentage

    def _extract_sources(self, results: Dict[str, Any]) -> List[str]:
        """Extract sources and citations from research results"""
        sources = []
        content = results.get("raw_content", "")

        # Look for common source patterns
        source_patterns = [
            r'https?://[^\s<>"\]]+',
            r'\[\d*\]\s*[^\[\n]*',
            r'References?:\s*[^\n]*',
            r'Sources?:\s*[^\n]*'
        ]

        import re
        for pattern in source_patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            sources.extend(matches)

        return list(set(sources))  # Remove duplicates


# Convenience function for external usage
def create_deep_research_swarm() -> DeepResearchSwarm:
    """Create and return a new deep research swarm instance"""
    return DeepResearchSwarm()


def run_research(query: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to run deep research quickly

    Args:
        query: Research topic or query
        **kwargs: Additional parameters for run_deep_research method
    """
    swarm = create_deep_research_swarm()
    return swarm.run_deep_research(research_topic=query, **kwargs)
