#!/usr/bin/env python3
"""
Example: How to Direct AI Agent Swarms in Sophia AI
"""

import asyncio
import httpx
import json
from typing import Dict, Any

class SophiaSwarmClient:
    """Client for interacting with Sophia AI swarms"""
    
    def __init__(self, base_url: str = "http://localhost:8088"):
        self.base_url = base_url
        self.websocket_url = "http://localhost:8096"
    
    async def execute_swarm(self, swarm_type: str, task: str, context: Dict = None) -> Dict:
        """Execute a swarm task"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/swarm/execute",
                json={
                    "swarm_type": swarm_type,
                    "task": task,
                    "context": context or {}
                },
                timeout=60.0
            )
            return response.json()
    
    async def planning_swarm(self, task: str) -> Dict:
        """Execute planning swarm (Three-Planner System)"""
        print(f"🎯 Planning: {task}")
        result = await self.execute_swarm("planning", task, {
            "enable_websocket": True
        })
        
        # Display the three perspectives
        if "plans" in result:
            plans = result["plans"]
            print("\n📊 PLANNING RESULTS:")
            print("\n1️⃣ CUTTING-EDGE APPROACH:")
            print(f"   Risk: {plans['cutting_edge']['risk']}")
            for step in plans['cutting_edge']['steps']:
                print(f"   • {step}")
            
            print("\n2️⃣ CONSERVATIVE APPROACH:")
            print(f"   Risk: {plans['conservative']['risk']}")
            for step in plans['conservative']['steps']:
                print(f"   • {step}")
            
            print("\n3️⃣ SYNTHESIS APPROACH (Recommended):")
            print(f"   Risk: {plans['synthesis']['risk']}")
            for step in plans['synthesis']['steps']:
                print(f"   • {step}")
        
        return result
    
    async def coding_swarm(self, task: str, push_to_github: bool = False) -> Dict:
        """Execute coding swarm"""
        print(f"💻 Coding: {task}")
        result = await self.execute_swarm("coding", task, {
            "push_to_github": push_to_github,
            "enable_websocket": True
        })
        
        if "code" in result:
            print("\n📝 GENERATED CODE:")
            print("=" * 50)
            print(result["code"][:500] + "..." if len(result["code"]) > 500 else result["code"])
            print("=" * 50)
            
            if result.get("github_pr"):
                print(f"\n✅ GitHub PR: {result['github_pr']}")
        
        return result
    
    async def research_swarm(self, query: str) -> Dict:
        """Execute research swarm with RAG"""
        print(f"🔍 Researching: {query}")
        result = await self.execute_swarm("research", query, {
            "enable_websocket": True,
            "limit": 10
        })
        
        if "results" in result:
            print(f"\n📚 RESEARCH RESULTS ({result.get('total_results', 0)} total):")
            print(f"Sources: {', '.join(result.get('sources_used', []))}")
            
            for i, res in enumerate(result["results"][:5], 1):
                print(f"\n{i}. {res.get('title', 'Untitled')}")
                print(f"   Source: {res.get('source')} | Score: {res.get('score', 0):.2f}")
                print(f"   {res.get('content', '')[:200]}...")
        
        return result
    
    async def analysis_swarm(self, task: str) -> Dict:
        """Execute analysis swarm"""
        print(f"📈 Analyzing: {task}")
        result = await self.execute_swarm("analysis", task, {
            "enable_websocket": True
        })
        
        if "analysis" in result:
            analysis = result["analysis"]
            print("\n🔬 ANALYSIS RESULTS:")
            print(f"Task: {analysis.get('task', '')}")
            print("\nInsights:")
            for insight in analysis.get("insights", []):
                print(f"  • {insight}")
            
            metrics = analysis.get("metrics", {})
            print(f"\nConfidence: {metrics.get('confidence', 0) * 100:.0f}%")
            print(f"Data Points: {metrics.get('data_points', 0)}")
        
        return result

async def main():
    """Example usage of Sophia AI swarms"""
    client = SophiaSwarmClient()
    
    print("=" * 60)
    print("SOPHIA AI - SWARM ORCHESTRATION EXAMPLES")
    print("=" * 60)
    
    # Example 1: Planning Swarm
    print("\n📋 EXAMPLE 1: PLANNING SWARM")
    print("-" * 40)
    await client.planning_swarm(
        "Design a scalable real-time analytics platform for IoT devices"
    )
    
    # Example 2: Coding Swarm
    print("\n\n📋 EXAMPLE 2: CODING SWARM")
    print("-" * 40)
    await client.coding_swarm(
        "Create a Python class for managing WebSocket connections with auto-reconnect",
        push_to_github=False
    )
    
    # Example 3: Research Swarm
    print("\n\n📋 EXAMPLE 3: RESEARCH SWARM")
    print("-" * 40)
    await client.research_swarm(
        "Latest advances in multi-agent reinforcement learning 2024"
    )
    
    # Example 4: Analysis Swarm
    print("\n\n📋 EXAMPLE 4: ANALYSIS SWARM")
    print("-" * 40)
    await client.analysis_swarm(
        "Analyze the performance implications of microservices vs monolithic architecture"
    )
    
    # Example 5: Complex Multi-Swarm Workflow
    print("\n\n📋 EXAMPLE 5: MULTI-SWARM WORKFLOW")
    print("-" * 40)
    print("Executing complex workflow: Research → Plan → Code")
    
    # Step 1: Research
    research = await client.research_swarm("Best practices for GraphQL API design")
    
    # Step 2: Plan based on research
    plan = await client.planning_swarm(
        f"Plan a GraphQL API implementation based on: {research.get('summary', '')[:100]}"
    )
    
    # Step 3: Code based on plan
    if plan.get("recommendation") == "synthesis":
        code = await client.coding_swarm(
            "Implement a GraphQL schema with authentication middleware"
        )
    
    print("\n✅ Multi-swarm workflow completed!")

if __name__ == "__main__":
    asyncio.run(main())