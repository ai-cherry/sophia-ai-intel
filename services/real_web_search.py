"""
Real Web Search Integration - Actually searches the web!
Supports multiple search providers: Tavily, Perplexity, SerpAPI
"""

import os
import httpx
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

class RealWebSearch:
    """Real web search using multiple providers"""
    
    def __init__(self):
        # API Keys from environment
        self.tavily_api_key = os.getenv("TAVILY_API_KEY", "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")  # Adding real key
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY", "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")
        self.serpapi_key = os.getenv("SERPAPI_KEY")
        
        # Check which services are available
        self.available_services = []
        if self.tavily_api_key:
            self.available_services.append("tavily")
            print("✓ Tavily API available")
        if self.perplexity_api_key:
            self.available_services.append("perplexity")
            print("✓ Perplexity API available")
        if self.serpapi_key:
            self.available_services.append("serpapi")
            print("✓ SerpAPI available")
            
        if not self.available_services:
            print("⚠️  No search APIs configured - using mock data")
    
    async def search_tavily(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search using Tavily API - optimized for AI agents"""
        if not self.tavily_api_key:
            return []
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.tavily_api_key,
                        "query": query,
                        "search_depth": "advanced",
                        "include_answer": True,
                        "include_raw_content": False,
                        "max_results": max_results,
                        "include_domains": [],
                        "exclude_domains": []
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    # Include the AI-generated answer if available
                    if data.get("answer"):
                        results.append({
                            "source": "tavily_answer",
                            "title": "AI Summary",
                            "content": data["answer"],
                            "url": "tavily:answer",
                            "score": 1.0
                        })
                    
                    # Add search results
                    for result in data.get("results", []):
                        results.append({
                            "source": "tavily",
                            "title": result.get("title", ""),
                            "content": result.get("content", ""),
                            "url": result.get("url", ""),
                            "score": result.get("score", 0.5)
                        })
                    
                    return results
                    
        except Exception as e:
            print(f"Tavily search error: {e}")
            
        return []
    
    async def search_perplexity(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search using Perplexity API"""
        if not self.perplexity_api_key:
            return []
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.perplexity_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "pplx-7b-online",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful research assistant. Provide detailed, factual information with sources."
                            },
                            {
                                "role": "user",
                                "content": f"Research this topic and provide sources: {query}"
                            }
                        ],
                        "temperature": 0.2,
                        "return_citations": True
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    return [{
                        "source": "perplexity",
                        "title": f"Perplexity Research: {query[:50]}",
                        "content": content,
                        "url": "perplexity:research",
                        "score": 0.9
                    }]
                    
        except Exception as e:
            print(f"Perplexity search error: {e}")
            
        return []
    
    async def search_serpapi(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search using SerpAPI (Google results)"""
        if not self.serpapi_key:
            return []
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "api_key": self.serpapi_key,
                        "q": query,
                        "engine": "google",
                        "num": max_results
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for result in data.get("organic_results", []):
                        results.append({
                            "source": "google",
                            "title": result.get("title", ""),
                            "content": result.get("snippet", ""),
                            "url": result.get("link", ""),
                            "score": 0.7
                        })
                    
                    return results
                    
        except Exception as e:
            print(f"SerpAPI search error: {e}")
            
        return []
    
    async def search_all(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Search across all available providers"""
        results = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "sources_used": [],
            "results": []
        }
        
        # If no APIs available, return mock data
        if not self.available_services:
            results["sources_used"] = ["mock"]
            results["results"] = self.get_mock_results(query)
            return results
        
        # Search with all available services
        tasks = []
        if "tavily" in self.available_services:
            tasks.append(self.search_tavily(query, max_results))
            results["sources_used"].append("tavily")
            
        if "perplexity" in self.available_services:
            tasks.append(self.search_perplexity(query, max_results))
            results["sources_used"].append("perplexity")
            
        if "serpapi" in self.available_services:
            tasks.append(self.search_serpapi(query, max_results))
            results["sources_used"].append("serpapi")
        
        # Execute all searches in parallel
        if tasks:
            search_results = await asyncio.gather(*tasks)
            for result_set in search_results:
                results["results"].extend(result_set)
        
        # Sort by relevance score
        results["results"].sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # Limit to max_results
        results["results"] = results["results"][:max_results]
        
        return results
    
    def get_mock_results(self, query: str) -> List[Dict]:
        """Fallback mock results when no API is available"""
        return [
            {
                "source": "mock",
                "title": f"Mock Result 1 for: {query}",
                "content": f"This is a simulated search result for '{query}'. In production, this would be real web content.",
                "url": "https://example.com/1",
                "score": 0.8
            },
            {
                "source": "mock",
                "title": f"Mock Result 2 for: {query}",
                "content": f"Another simulated result about '{query}'. Configure API keys for real search.",
                "url": "https://example.com/2",
                "score": 0.6
            }
        ]

# Global search instance
web_search = RealWebSearch()

async def search_web(query: str, sources: List[str] = None, limit: int = 10) -> Dict:
    """Main entry point for web search"""
    
    print(f"🔍 Searching web for: {query}")
    
    # Perform search
    results = await web_search.search_all(query, limit)
    
    # Filter by requested sources if specified
    if sources:
        filtered = []
        for result in results["results"]:
            if any(s in result["source"] for s in sources):
                filtered.append(result)
        results["results"] = filtered
    
    print(f"✓ Found {len(results['results'])} results from {', '.join(results['sources_used'])}")
    
    return results

# Test function
async def test_search():
    """Test the search functionality"""
    results = await search_web("latest AI developments 2024", limit=5)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(test_search())