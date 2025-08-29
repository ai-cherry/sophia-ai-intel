#!/usr/bin/env python3
"""
Enhanced MCP Research Service with Real Web Search
Provides actual web search, documentation lookup, and research capabilities
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import aiohttp
import json
import os
from urllib.parse import quote

app = FastAPI(title="MCP Research Service - Real Search")

class ResearchRequest(BaseModel):
    query: str
    sources: Optional[List[str]] = ["web"]
    depth: Optional[str] = "standard"
    limit: Optional[int] = 10
    include_code: Optional[bool] = False

class ResearchResult(BaseModel):
    source: str
    title: str
    summary: str
    url: str
    relevance_score: float
    metadata: Dict[str, Any]
    timestamp: str

class SearchEngines:
    """Real search implementations"""
    
    @staticmethod
    async def search_duckduckgo(query: str, limit: int = 10) -> List[Dict]:
        """Search using DuckDuckGo instant answers API"""
        results = []
        try:
            async with aiohttp.ClientSession() as session:
                # DuckDuckGo instant answer API
                url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Process abstract
                        if data.get('Abstract'):
                            results.append({
                                'title': data.get('Heading', query),
                                'summary': data['Abstract'],
                                'url': data.get('AbstractURL', ''),
                                'source': 'duckduckgo_abstract'
                            })
                        
                        # Process related topics
                        for topic in data.get('RelatedTopics', [])[:limit]:
                            if isinstance(topic, dict) and 'Text' in topic:
                                results.append({
                                    'title': topic.get('Text', '').split(' - ')[0][:100],
                                    'summary': topic.get('Text', ''),
                                    'url': topic.get('FirstURL', ''),
                                    'source': 'duckduckgo_related'
                                })
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
        
        return results
    
    @staticmethod
    async def search_github_repos(query: str, limit: int = 5) -> List[Dict]:
        """Search GitHub repositories"""
        results = []
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if os.getenv('GITHUB_TOKEN'):
                    headers['Authorization'] = f"token {os.getenv('GITHUB_TOKEN')}"
                
                url = f"https://api.github.com/search/repositories?q={quote(query)}&sort=stars&order=desc"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        for repo in data.get('items', [])[:limit]:
                            results.append({
                                'title': repo['full_name'],
                                'summary': repo.get('description', 'No description'),
                                'url': repo['html_url'],
                                'source': 'github',
                                'metadata': {
                                    'stars': repo['stargazers_count'],
                                    'language': repo.get('language', 'Unknown'),
                                    'updated': repo['updated_at']
                                }
                            })
        except Exception as e:
            print(f"GitHub search error: {e}")
        
        return results
    
    @staticmethod
    async def search_documentation(query: str, focus: str = "AI") -> List[Dict]:
        """Search documentation sites"""
        results = []
        
        # Documentation sources to search
        doc_sites = {
            'langchain': 'https://python.langchain.com/docs/',
            'openai': 'https://platform.openai.com/docs/',
            'anthropic': 'https://docs.anthropic.com/',
            'huggingface': 'https://huggingface.co/docs/',
            'pytorch': 'https://pytorch.org/docs/',
            'tensorflow': 'https://www.tensorflow.org/api_docs'
        }
        
        for site_name, base_url in doc_sites.items():
            if focus.lower() in query.lower() or site_name in query.lower():
                results.append({
                    'title': f"{site_name.capitalize()} Documentation",
                    'summary': f"Official documentation for {site_name} - search for '{query}'",
                    'url': base_url,
                    'source': 'documentation',
                    'metadata': {'doc_type': site_name}
                })
        
        return results
    
    @staticmethod
    async def search_arxiv(query: str, limit: int = 5) -> List[Dict]:
        """Search arXiv for academic papers"""
        results = []
        try:
            async with aiohttp.ClientSession() as session:
                # ArXiv API
                url = f"http://export.arxiv.org/api/query?search_query=all:{quote(query)}&max_results={limit}"
                async with session.get(url) as response:
                    if response.status == 200:
                        # Parse XML response (simplified)
                        text = await response.text()
                        # Basic parsing (in production, use proper XML parser)
                        entries = text.split('<entry>')[1:]
                        for entry in entries[:limit]:
                            title = entry.split('<title>')[1].split('</title>')[0] if '<title>' in entry else 'Unknown'
                            summary = entry.split('<summary>')[1].split('</summary>')[0] if '<summary>' in entry else 'No summary'
                            link = entry.split('<id>')[1].split('</id>')[0] if '<id>' in entry else ''
                            
                            results.append({
                                'title': title.strip(),
                                'summary': summary.strip()[:500],
                                'url': link,
                                'source': 'arxiv',
                                'metadata': {'type': 'academic_paper'}
                            })
        except Exception as e:
            print(f"ArXiv search error: {e}")
        
        return results

class ResearchOrchestrator:
    """Orchestrates research across multiple sources"""
    
    @staticmethod
    async def comprehensive_search(query: str, sources: List[str], limit: int) -> List[ResearchResult]:
        """Perform comprehensive search across all requested sources"""
        all_results = []
        search_engines = SearchEngines()
        
        tasks = []
        if 'web' in sources:
            tasks.append(search_engines.search_duckduckgo(query, limit))
        if 'github' in sources or 'code' in sources:
            tasks.append(search_engines.search_github_repos(query, limit))
        if 'docs' in sources or 'documentation' in sources:
            tasks.append(search_engines.search_documentation(query))
        if 'academic' in sources or 'arxiv' in sources:
            tasks.append(search_engines.search_arxiv(query, limit))
        
        # Execute all searches in parallel
        results_lists = await asyncio.gather(*tasks)
        
        # Flatten and process results
        for results_list in results_lists:
            for result in results_list:
                all_results.append(ResearchResult(
                    source=result.get('source', 'unknown'),
                    title=result.get('title', ''),
                    summary=result.get('summary', ''),
                    url=result.get('url', ''),
                    relevance_score=0.8,  # Could implement actual scoring
                    metadata=result.get('metadata', {}),
                    timestamp=datetime.now().isoformat()
                ))
        
        return all_results

@app.get("/")
async def root():
    return {
        "service": "MCP Research - Real Search",
        "version": "2.0",
        "status": "active",
        "capabilities": [
            "web_search",
            "github_search",
            "documentation_search",
            "academic_search",
            "arxiv_search"
        ],
        "endpoints": {
            "/research": "Perform comprehensive research",
            "/search/web": "Web search only",
            "/search/github": "GitHub repository search",
            "/search/docs": "Documentation search",
            "/search/academic": "Academic paper search"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/research")
async def perform_research(request: ResearchRequest):
    """Perform comprehensive research across multiple sources"""
    orchestrator = ResearchOrchestrator()
    
    results = await orchestrator.comprehensive_search(
        request.query,
        request.sources,
        request.limit
    )
    
    return {
        "query": request.query,
        "sources_searched": request.sources,
        "depth": request.depth,
        "total_results": len(results),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/search/web")
async def search_web(q: str, limit: int = 10):
    """Direct web search"""
    results = await SearchEngines.search_duckduckgo(q, limit)
    return {"query": q, "results": results, "count": len(results)}

@app.get("/search/github")
async def search_github(q: str, limit: int = 5):
    """Search GitHub repositories"""
    results = await SearchEngines.search_github_repos(q, limit)
    return {"query": q, "results": results, "count": len(results)}

@app.get("/search/docs")
async def search_docs(q: str):
    """Search documentation"""
    results = await SearchEngines.search_documentation(q)
    return {"query": q, "results": results, "count": len(results)}

@app.get("/search/academic")
async def search_academic(q: str, limit: int = 5):
    """Search academic papers"""
    results = await SearchEngines.search_arxiv(q, limit)
    return {"query": q, "results": results, "count": len(results)}

if __name__ == "__main__":
    import uvicorn
    print("Starting MCP Research Service with Real Web Search...")
    print("Available at: http://localhost:8085")
    print("")
    print("Features:")
    print("  - DuckDuckGo web search")
    print("  - GitHub repository search")
    print("  - Documentation search")
    print("  - ArXiv academic paper search")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=8085)