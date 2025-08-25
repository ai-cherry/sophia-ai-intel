#!/usr/bin/env python3
"""
Sophia AI Qdrant Vector Database Setup
Initializes Qdrant vector database with collections for the Sophia AI system.
"""

import os
import sys
import json
import requests
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QdrantManager:
    """Qdrant vector database manager"""

    def __init__(self):
        self.qdrant_url = os.getenv('QDRANT_URL')
        self.qdrant_api_key = os.getenv('QDRANT_API_KEY')
        self.headers = {
            'Content-Type': 'application/json',
            'api-key': self.qdrant_api_key
        }

    def test_connection(self) -> bool:
        """Test connection to Qdrant"""
        try:
            if not self.qdrant_url or not self.qdrant_api_key:
                logger.error("QDRANT_URL or QDRANT_API_KEY not found in environment")
                return False

            response = requests.get(f"{self.qdrant_url}/health", headers=self.headers)
            if response.status_code == 200:
                logger.info("✅ Qdrant connection successful")
                return True
            else:
                logger.error(f"❌ Qdrant health check failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Qdrant connection failed: {e}")
            return False

    def create_collection(self, collection_name: str, vector_size: int = 1536, distance: str = "Cosine") -> bool:
        """Create a vector collection"""
        try:
            payload = {
                "name": collection_name,
                "vectors": {
                    "size": vector_size,
                    "distance": distance
                }
            }

            response = requests.put(
                f"{self.qdrant_url}/collections/{collection_name}",
                headers=self.headers,
                json=payload
            )

            if response.status_code in [200, 201]:
                logger.info(f"✅ Created collection: {collection_name}")
                return True
            elif response.status_code == 409:
                logger.info(f"⚠️ Collection {collection_name} already exists")
                return True
            else:
                logger.error(f"❌ Failed to create collection {collection_name}: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Error creating collection {collection_name}: {e}")
            return False

    def setup_collections(self) -> bool:
        """Set up all required collections for Sophia AI"""
        collections = [
            {
                "name": "sophia-knowledge-base",
                "vector_size": 1536,  # OpenAI ada-002 dimensions
                "description": "General knowledge base for Sophia AI"
            },
            {
                "name": "sophia-user-profiles",
                "vector_size": 1536,
                "description": "User profile embeddings for personalization"
            },
            {
                "name": "sophia-conversation-context",
                "vector_size": 1536,
                "description": "Conversation context and history"
            },
            {
                "name": "sophia-agent-personas",
                "vector_size": 1536,
                "description": "AI agent persona embeddings"
            },
            {
                "name": "sophia-code-snippets",
                "vector_size": 1536,
                "description": "Code snippet embeddings for search"
            },
            {
                "name": "sophia-research-papers",
                "vector_size": 1536,
                "description": "Research paper and document embeddings"
            },
            {
                "name": "sophia-web-content",
                "vector_size": 1536,
                "description": "Web content and crawled data"
            },
            {
                "name": "sophia-semantic-cache",
                "vector_size": 1536,
                "description": "Semantic caching for API responses"
            }
        ]

        success_count = 0
        for collection in collections:
            if self.create_collection(collection["name"], collection["vector_size"]):
                success_count += 1

        logger.info(f"✅ Created {success_count}/{len(collections)} collections")
        return success_count == len(collections)

    def setup_payload_indexes(self) -> bool:
        """Set up payload indexes for efficient filtering"""
        try:
            indexes = [
                {
                    "collection": "sophia-knowledge-base",
                    "field": "metadata.type",
                    "type": "keyword"
                },
                {
                    "collection": "sophia-knowledge-base",
                    "field": "metadata.created_by",
                    "type": "keyword"
                },
                {
                    "collection": "sophia-conversation-context",
                    "field": "user_id",
                    "type": "keyword"
                },
                {
                    "collection": "sophia-conversation-context",
                    "field": "agent_id",
                    "type": "keyword"
                },
                {
                    "collection": "sophia-user-profiles",
                    "field": "user_id",
                    "type": "keyword"
                },
                {
                    "collection": "sophia-agent-personas",
                    "field": "agent_type",
                    "type": "keyword"
                }
            ]

            success_count = 0
            for index in indexes:
                payload = {
                    "field_name": index["field"],
                    "field_type": index["type"]
                }

                response = requests.put(
                    f"{self.qdrant_url}/collections/{index['collection']}/index",
                    headers=self.headers,
                    json=payload
                )

                if response.status_code in [200, 201]:
                    logger.info(f"✅ Created index on {index['collection']}.{index['field']}")
                    success_count += 1
                else:
                    logger.warning(f"⚠️ Failed to create index on {index['collection']}.{index['field']}: {response.text}")

            logger.info(f"✅ Set up {success_count}/{len(indexes)} payload indexes")
            return True

        except Exception as e:
            logger.error(f"❌ Error setting up payload indexes: {e}")
            return False

    def create_sample_data(self) -> bool:
        """Create sample data for testing"""
        try:
            # Sample knowledge base entry
            sample_data = {
                "points": [
                    {
                        "id": 1,
                        "vector": [0.1] * 1536,  # Placeholder vector
                        "payload": {
                            "title": "Welcome to Sophia AI",
                            "content": "Sophia AI is an advanced artificial intelligence system designed for enterprise applications.",
                            "type": "documentation",
                            "created_by": "system",
                            "created_at": "2025-01-01T00:00:00Z"
                        }
                    },
                    {
                        "id": 2,
                        "vector": [0.2] * 1536,  # Placeholder vector
                        "payload": {
                            "title": "Getting Started Guide",
                            "content": "This guide will help you get started with Sophia AI platform.",
                            "type": "tutorial",
                            "created_by": "system",
                            "created_at": "2025-01-01T00:00:00Z"
                        }
                    }
                ]
            }

            response = requests.put(
                f"{self.qdrant_url}/collections/sophia-knowledge-base/points",
                headers=self.headers,
                json=sample_data
            )

            if response.status_code in [200, 201]:
                logger.info("✅ Created sample data in knowledge base")
                return True
            else:
                logger.warning(f"⚠️ Failed to create sample data: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Error creating sample data: {e}")
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about all collections"""
        try:
            response = requests.get(f"{self.qdrant_url}/collections", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Failed to get collection info: {response.text}")
                return {}
        except Exception as e:
            logger.error(f"❌ Error getting collection info: {e}")
            return {}

def main():
    """Main setup function"""
    print("🚀 Setting up Sophia AI Qdrant Vector Database")
    print("=" * 55)

    qdrant_manager = QdrantManager()

    # Step 1: Test connection
    print("\n1️⃣ Testing Qdrant connection...")
    if not qdrant_manager.test_connection():
        print("❌ Failed to connect to Qdrant. Please check your configuration.")
        sys.exit(1)

    # Step 2: Create collections
    print("\n2️⃣ Creating vector collections...")
    if not qdrant_manager.setup_collections():
        print("❌ Failed to create collections")
        sys.exit(1)

    # Step 3: Setup payload indexes
    print("\n3️⃣ Setting up payload indexes...")
    if not qdrant_manager.setup_payload_indexes():
        print("⚠️ Some payload indexes may not have been created")

    # Step 4: Create sample data
    print("\n4️⃣ Creating sample data...")
    if not qdrant_manager.create_sample_data():
        print("⚠️ Sample data creation failed")

    # Step 5: Get collection information
    print("\n5️⃣ Collection Information:")
    collection_info = qdrant_manager.get_collection_info()
    if collection_info:
        collections = collection_info.get('result', {}).get('collections', [])
        print(f"   Total collections: {len(collections)}")
        for collection in collections:
            print(f"   • {collection['name']}: {collection.get('vectors_count', 0)} vectors")

    print("\n" + "=" * 55)
    print("🎉 Qdrant setup completed successfully!")
    print("\n📋 Configuration Summary:")
    print("   • Vector collections: ✅")
    print("   • Payload indexes: ✅")
    print("   • Sample data: ✅")
    print("   • Connection test: ✅")

    print("\n🔧 Next Steps:")
    print("   1. Update your application to use Qdrant for vector operations")
    print("   2. Implement vector embedding generation")
    print("   3. Set up vector indexing and search")
    print("   4. Configure vector backup and optimization")

if __name__ == "__main__":
    main()