#!/usr/bin/env python3
"""
Sophia AI MCP Development Integration
Connect with running MCP servers for AI-assisted development
"""

import requests
import json
import sys

class SophiaMCPClient:
    def __init__(self):
        self.services = {
            'qdrant': 'http://localhost:6333',
            'postgres': 'localhost:5432', 
            'redis': 'localhost:6380',
            'adminer': 'http://localhost:8080',
            'prometheus': 'http://localhost:9090'
        }
    
    def check_services(self):
        """Check status of running MCP services"""
        print("Sophia AI MCP Services Status:")
        print("=" * 40)
        
        # Check Qdrant
        try:
            response = requests.get(f"{self.services['qdrant']}/health", timeout=2)
            status = "✅ HEALTHY" if response.status_code == 200 else "⚠️ ISSUES"
            print(f"Qdrant Vector DB:  {status}")
        except:
            print("Qdrant Vector DB:  ❌ DOWN")
            
        # Check Prometheus
        try:
            response = requests.get(f"{self.services['prometheus']}/-/healthy", timeout=2)
            status = "✅ HEALTHY" if response.status_code == 200 else "⚠️ ISSUES"
            print(f"Prometheus:        {status}")
        except:
            print("Prometheus:        ❌ DOWN")
            
        print("\n🔗 MCP Context Available:")
        print("  • Vector embeddings via Qdrant")
        print("  • Metrics and monitoring via Prometheus") 
        print("  • Database access via Adminer")
        print("  • Redis cache management")
    
    def vector_search(self, query, collection="sophia-ai"):
        """Search vector database via Qdrant"""
        try:
            url = f"{self.services['qdrant']}/collections/{collection}/points/search"
            payload = {
                "vector": [0.1] * 384,  # Placeholder vector
                "limit": 5,
                "with_payload": True
            }
            response = requests.post(url, json=payload, timeout=5)
            return response.json() if response.status_code == 200 else None
        except:
            return None

if __name__ == "__main__":
    client = SophiaMCPClient()
    
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        client.check_services()
    elif len(sys.argv) > 1 and sys.argv[1] == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else "test"
        result = client.vector_search(query)
        print(f"Vector search results for '{query}':")
        print(json.dumps(result, indent=2) if result else "No results")
    else:
        print("Sophia AI MCP Integration")
        print("Usage:")
        print("  python3 mcp-dev-integration.py status   # Check service status") 
        print("  python3 mcp-dev-integration.py search <query>  # Vector search")
