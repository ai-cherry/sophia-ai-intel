"""
Vector Search Integration with Weaviate for RAG
"""

import os
import httpx
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import hashlib

class WeaviateVectorSearch:
    """Weaviate vector database integration for semantic search"""
    
    def __init__(self):
        # Weaviate configuration from environment
        self.weaviate_url = os.getenv("WEAVIATE_URL", "https://w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud")
        self.weaviate_api_key = os.getenv("WEAVIATE_API_KEY", "VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        self.headers = {
            "Authorization": f"Bearer {self.weaviate_api_key}",
            "Content-Type": "application/json",
            "X-OpenAI-Api-Key": self.openai_api_key  # For vectorization
        }
        
        # Collection names
        self.collections = {
            "knowledge": "SophiaKnowledge",
            "conversations": "SophiaConversations",
            "code": "SophiaCode",
            "research": "SophiaResearch"
        }
        
        print(f"✓ Weaviate initialized: {self.weaviate_url}")
    
    async def create_collections(self):
        """Create Weaviate collections if they don't exist"""
        for collection_type, collection_name in self.collections.items():
            schema = self._get_collection_schema(collection_type, collection_name)
            
            try:
                async with httpx.AsyncClient() as client:
                    # Check if collection exists
                    response = await client.get(
                        f"{self.weaviate_url}/v1/schema/{collection_name}",
                        headers=self.headers,
                        timeout=10.0
                    )
                    
                    if response.status_code == 404:
                        # Create collection
                        response = await client.post(
                            f"{self.weaviate_url}/v1/schema",
                            headers=self.headers,
                            json=schema,
                            timeout=10.0
                        )
                        if response.status_code == 200:
                            print(f"✓ Created collection: {collection_name}")
                    else:
                        print(f"✓ Collection exists: {collection_name}")
            except Exception as e:
                print(f"Error with collection {collection_name}: {e}")
    
    def _get_collection_schema(self, collection_type: str, collection_name: str) -> Dict:
        """Get schema for a collection type"""
        base_properties = [
            {"name": "content", "dataType": ["text"], "description": "Main content"},
            {"name": "title", "dataType": ["string"], "description": "Title or name"},
            {"name": "source", "dataType": ["string"], "description": "Source of the content"},
            {"name": "timestamp", "dataType": ["date"], "description": "Creation timestamp"},
            {"name": "metadata", "dataType": ["text"], "description": "JSON metadata"},
            {"name": "tags", "dataType": ["string[]"], "description": "Tags for categorization"}
        ]
        
        # Add type-specific properties
        if collection_type == "code":
            base_properties.extend([
                {"name": "language", "dataType": ["string"], "description": "Programming language"},
                {"name": "framework", "dataType": ["string"], "description": "Framework used"}
            ])
        elif collection_type == "research":
            base_properties.extend([
                {"name": "url", "dataType": ["string"], "description": "Source URL"},
                {"name": "relevance_score", "dataType": ["number"], "description": "Relevance score"}
            ])
        elif collection_type == "conversations":
            base_properties.extend([
                {"name": "user_id", "dataType": ["string"], "description": "User identifier"},
                {"name": "agent_id", "dataType": ["string"], "description": "Agent identifier"}
            ])
        
        return {
            "class": collection_name,
            "description": f"Sophia AI {collection_type} collection",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                    "model": "text-embedding-ada-002",
                    "type": "text"
                }
            },
            "properties": base_properties
        }
    
    async def add_document(self, collection_type: str, document: Dict) -> Optional[str]:
        """Add a document to Weaviate"""
        collection_name = self.collections.get(collection_type, "SophiaKnowledge")
        
        # Generate ID from content hash
        content_hash = hashlib.md5(
            json.dumps(document, sort_keys=True).encode()
        ).hexdigest()
        
        # Prepare document
        weaviate_doc = {
            "id": content_hash,
            "class": collection_name,
            "properties": {
                "content": document.get("content", ""),
                "title": document.get("title", ""),
                "source": document.get("source", "unknown"),
                "timestamp": document.get("timestamp", datetime.now().isoformat()),
                "metadata": json.dumps(document.get("metadata", {})),
                "tags": document.get("tags", [])
            }
        }
        
        # Add type-specific fields
        if collection_type == "code":
            weaviate_doc["properties"]["language"] = document.get("language", "python")
            weaviate_doc["properties"]["framework"] = document.get("framework", "")
        elif collection_type == "research":
            weaviate_doc["properties"]["url"] = document.get("url", "")
            weaviate_doc["properties"]["relevance_score"] = document.get("relevance_score", 0.5)
        elif collection_type == "conversations":
            weaviate_doc["properties"]["user_id"] = document.get("user_id", "")
            weaviate_doc["properties"]["agent_id"] = document.get("agent_id", "")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.weaviate_url}/v1/objects",
                    headers=self.headers,
                    json=weaviate_doc,
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    print(f"✓ Added document to {collection_name}: {content_hash[:8]}...")
                    return result.get("id", content_hash)
                else:
                    print(f"Failed to add document: {response.status_code}")
                    
        except Exception as e:
            print(f"Error adding document: {e}")
        
        return None
    
    async def search(self, query: str, collection_type: str = "knowledge", 
                     limit: int = 10, min_score: float = 0.7) -> List[Dict]:
        """Perform semantic search in Weaviate"""
        collection_name = self.collections.get(collection_type, "SophiaKnowledge")
        
        # GraphQL query for semantic search
        graphql_query = {
            "query": f"""
            {{
                Get {{
                    {collection_name}(
                        nearText: {{
                            concepts: ["{query}"]
                            distance: {1 - min_score}
                        }}
                        limit: {limit}
                    ) {{
                        content
                        title
                        source
                        timestamp
                        metadata
                        tags
                        _additional {{
                            id
                            distance
                            certainty
                        }}
                    }}
                }}
            }}
            """
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.weaviate_url}/v1/graphql",
                    headers=self.headers,
                    json=graphql_query,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("data", {}).get("Get", {}).get(collection_name, [])
                    
                    # Format results
                    formatted_results = []
                    for result in results:
                        formatted_results.append({
                            "content": result.get("content", ""),
                            "title": result.get("title", ""),
                            "source": result.get("source", ""),
                            "timestamp": result.get("timestamp", ""),
                            "metadata": json.loads(result.get("metadata", "{}")),
                            "tags": result.get("tags", []),
                            "score": result.get("_additional", {}).get("certainty", 0),
                            "id": result.get("_additional", {}).get("id", "")
                        })
                    
                    print(f"✓ Found {len(formatted_results)} results for: {query[:50]}...")
                    return formatted_results
                    
        except Exception as e:
            print(f"Search error: {e}")
        
        return []
    
    async def hybrid_search(self, query: str, keywords: List[str] = None,
                           collection_type: str = "knowledge", limit: int = 10) -> List[Dict]:
        """Perform hybrid search (semantic + keyword)"""
        collection_name = self.collections.get(collection_type, "SophiaKnowledge")
        
        # Build where filter for keywords
        where_filter = ""
        if keywords:
            keyword_conditions = " OR ".join([
                f'{{path: ["content"], operator: Like, valueText: "*{kw}*"}}'
                for kw in keywords
            ])
            where_filter = f"where: {{operator: Or, operands: [{keyword_conditions}]}}"
        
        # GraphQL query for hybrid search
        graphql_query = {
            "query": f"""
            {{
                Get {{
                    {collection_name}(
                        hybrid: {{
                            query: "{query}"
                            alpha: 0.75
                        }}
                        {where_filter}
                        limit: {limit}
                    ) {{
                        content
                        title
                        source
                        timestamp
                        metadata
                        tags
                        _additional {{
                            id
                            score
                            explainScore
                        }}
                    }}
                }}
            }}
            """
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.weaviate_url}/v1/graphql",
                    headers=self.headers,
                    json=graphql_query,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("data", {}).get("Get", {}).get(collection_name, [])
                    
                    # Format results
                    formatted_results = []
                    for result in results:
                        formatted_results.append({
                            "content": result.get("content", ""),
                            "title": result.get("title", ""),
                            "source": result.get("source", ""),
                            "timestamp": result.get("timestamp", ""),
                            "metadata": json.loads(result.get("metadata", "{}")),
                            "tags": result.get("tags", []),
                            "score": float(result.get("_additional", {}).get("score", 0)),
                            "id": result.get("_additional", {}).get("id", "")
                        })
                    
                    print(f"✓ Hybrid search found {len(formatted_results)} results")
                    return formatted_results
                    
        except Exception as e:
            print(f"Hybrid search error: {e}")
        
        return []
    
    async def delete_document(self, document_id: str, collection_type: str = "knowledge") -> bool:
        """Delete a document from Weaviate"""
        collection_name = self.collections.get(collection_type, "SophiaKnowledge")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.weaviate_url}/v1/objects/{collection_name}/{document_id}",
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 204:
                    print(f"✓ Deleted document: {document_id[:8]}...")
                    return True
                    
        except Exception as e:
            print(f"Delete error: {e}")
        
        return False
    
    async def update_document(self, document_id: str, updates: Dict, 
                            collection_type: str = "knowledge") -> bool:
        """Update a document in Weaviate"""
        collection_name = self.collections.get(collection_type, "SophiaKnowledge")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.weaviate_url}/v1/objects/{collection_name}/{document_id}",
                    headers=self.headers,
                    json={"properties": updates},
                    timeout=10.0
                )
                
                if response.status_code == 204:
                    print(f"✓ Updated document: {document_id[:8]}...")
                    return True
                    
        except Exception as e:
            print(f"Update error: {e}")
        
        return False

# Global instance
vector_search = WeaviateVectorSearch()

async def index_research_results(results: List[Dict]) -> int:
    """Index research results into Weaviate"""
    indexed = 0
    
    for result in results:
        doc = {
            "title": result.get("title", ""),
            "content": result.get("content", ""),
            "source": result.get("source", ""),
            "url": result.get("url", ""),
            "relevance_score": result.get("score", 0.5),
            "tags": ["research", result.get("source", "unknown")],
            "metadata": {
                "indexed_at": datetime.now().isoformat(),
                "result_type": "research"
            }
        }
        
        doc_id = await vector_search.add_document("research", doc)
        if doc_id:
            indexed += 1
    
    print(f"✓ Indexed {indexed}/{len(results)} research results")
    return indexed

async def index_code_snippet(code: str, title: str, language: str = "python", 
                            tags: List[str] = None) -> Optional[str]:
    """Index code snippet into Weaviate"""
    doc = {
        "title": title,
        "content": code,
        "source": "generated",
        "language": language,
        "tags": tags or ["code", language],
        "metadata": {
            "indexed_at": datetime.now().isoformat(),
            "lines": len(code.split("\n"))
        }
    }
    
    return await vector_search.add_document("code", doc)

async def search_knowledge_base(query: str, search_type: str = "hybrid", 
                               collection: str = "knowledge", limit: int = 10) -> List[Dict]:
    """Search the knowledge base"""
    
    if search_type == "hybrid":
        # Extract potential keywords from query
        keywords = [word for word in query.split() if len(word) > 3][:3]
        return await vector_search.hybrid_search(query, keywords, collection, limit)
    else:
        return await vector_search.search(query, collection, limit)

# Test function
async def test_vector_search():
    """Test vector search functionality"""
    
    # Create collections
    await vector_search.create_collections()
    
    # Add test document
    test_doc = {
        "title": "Test Document",
        "content": "This is a test document about AI agents and swarm intelligence.",
        "source": "test",
        "tags": ["test", "ai", "agents"]
    }
    
    doc_id = await vector_search.add_document("knowledge", test_doc)
    print(f"Added test document: {doc_id}")
    
    # Search for it
    results = await vector_search.search("AI agents", "knowledge", limit=5)
    print(f"Search results: {len(results)}")
    
    for result in results:
        print(f"  - {result['title']}: {result['score']}")

if __name__ == "__main__":
    asyncio.run(test_vector_search())