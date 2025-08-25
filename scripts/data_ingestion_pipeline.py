#!/usr/bin/env python3
"""
Sophia AI Data Ingestion Pipeline
Handles data ingestion from various sources into PostgreSQL database with Redis caching.
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import hashlib
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIngestionPipeline:
    """Main data ingestion pipeline for Sophia AI"""

    def __init__(self):
        self.config = self._load_config()
        self.db_connection = None
        self.redis_client = None
        self.vector_store = None
        self.ingestion_stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            'database_url': os.getenv('DATABASE_URL'),
            'redis_url': os.getenv('REDIS_URL'),
            'qdrant_url': os.getenv('QDRANT_URL'),
            'qdrant_api_key': os.getenv('QDRANT_API_KEY'),
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
        }

    async def initialize(self) -> bool:
        """Initialize all pipeline components"""
        try:
            logger.info("🚀 Initializing Data Ingestion Pipeline")

            # Initialize database connection
            await self._init_database()

            # Initialize Redis cache
            await self._init_redis()

            # Initialize vector store
            await self._init_vector_store()

            logger.info("✅ Data Ingestion Pipeline initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize pipeline: {e}")
            return False

    async def _init_database(self):
        """Initialize database connection"""
        try:
            import psycopg2
            import psycopg2.extras

            self.db_connection = psycopg2.connect(self.config['database_url'])
            self.db_connection.autocommit = False

            # Create cursor
            self.db_cursor = self.db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            logger.info("✅ Database connection established")

        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    async def _init_redis(self):
        """Initialize Redis connection"""
        try:
            import redis

            # Parse Redis URL
            redis_url = self.config['redis_url']
            if redis_url.startswith('redis://'):
                url_parts = redis_url.replace('redis://', '').split(':')
                if len(url_parts) >= 2:
                    host = url_parts[0]
                    port = int(url_parts[1].split('/')[0]) if '/' in url_parts[1] else 6379
                else:
                    host = 'localhost'
                    port = 6379
            else:
                host = redis_url
                port = 6379

            self.redis_client = redis.Redis(
                host=host,
                port=port,
                decode_responses=True
            )

            # Test connection
            self.redis_client.ping()
            logger.info("✅ Redis connection established")

        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise

    async def _init_vector_store(self):
        """Initialize vector store connection"""
        try:
            import requests

            self.qdrant_headers = {
                'Content-Type': 'application/json',
                'api-key': self.config['qdrant_api_key']
            }

            # Test connection
            response = requests.get(f"{self.config['qdrant_url']}/health", headers=self.qdrant_headers)
            if response.status_code == 200:
                logger.info("✅ Vector store connection established")
            else:
                logger.warning(f"⚠️ Vector store health check returned {response.status_code}")

        except Exception as e:
            logger.error(f"❌ Vector store connection failed: {e}")
            raise

    async def ingest_knowledge_base(self, data_source: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest knowledge base data from various sources"""
        try:
            source_type = data_source.get('type', 'unknown')
            logger.info(f"📚 Starting knowledge base ingestion from {source_type}")

            if source_type == 'documents':
                return await self._ingest_documents(data_source)
            elif source_type == 'web_pages':
                return await self._ingest_web_pages(data_source)
            elif source_type == 'api_data':
                return await self._ingest_api_data(data_source)
            elif source_type == 'code_repository':
                return await self._ingest_code_repository(data_source)
            else:
                raise ValueError(f"Unknown data source type: {source_type}")

        except Exception as e:
            logger.error(f"❌ Knowledge base ingestion failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'stats': self.ingestion_stats
            }

    async def _ingest_documents(self, data_source: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest documents from file system or URLs"""
        documents = data_source.get('documents', [])
        processed = 0
        successful = 0

        for doc in documents:
            try:
                # Extract document content
                content = await self._extract_document_content(doc)
                if not content:
                    continue

                # Generate metadata
                metadata = {
                    'source': doc.get('source', 'unknown'),
                    'filename': doc.get('filename', ''),
                    'type': 'document',
                    'ingested_at': datetime.now().isoformat(),
                    'content_hash': hashlib.md5(content.encode()).hexdigest()
                }

                # Store in database
                doc_id = await self._store_knowledge(content, metadata)

                # Generate and store embedding
                await self._store_embedding(doc_id, content, metadata)

                successful += 1
                processed += 1

                # Cache the result
                await self._cache_document(doc_id, content, metadata)

            except Exception as e:
                logger.error(f"❌ Failed to process document {doc.get('filename', 'unknown')}: {e}")
                processed += 1
                continue

        return {
            'status': 'completed',
            'source_type': 'documents',
            'total_processed': processed,
            'successful': successful,
            'failed': processed - successful
        }

    async def _ingest_web_pages(self, data_source: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest web pages from URLs"""
        urls = data_source.get('urls', [])
        processed = 0
        successful = 0

        for url in urls:
            try:
                # Fetch web page content
                content = await self._fetch_web_content(url)
                if not content:
                    continue

                # Extract title and metadata
                title = await self._extract_title(content, url)
                metadata = {
                    'source': 'web',
                    'url': url,
                    'title': title,
                    'type': 'webpage',
                    'ingested_at': datetime.now().isoformat(),
                    'content_hash': hashlib.md5(content.encode()).hexdigest()
                }

                # Store in database
                doc_id = await self._store_knowledge(content, metadata)

                # Generate and store embedding
                await self._store_embedding(doc_id, content, metadata)

                successful += 1
                processed += 1

                # Cache the result
                await self._cache_document(doc_id, content, metadata)

            except Exception as e:
                logger.error(f"❌ Failed to process URL {url}: {e}")
                processed += 1
                continue

        return {
            'status': 'completed',
            'source_type': 'web_pages',
            'total_processed': processed,
            'successful': successful,
            'failed': processed - successful
        }

    async def _ingest_api_data(self, data_source: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest data from APIs"""
        api_config = data_source.get('api_config', {})
        processed = 0
        successful = 0

        try:
            # Fetch data from API
            api_data = await self._fetch_api_data(api_config)

            for item in api_data:
                try:
                    # Convert API item to content
                    content = json.dumps(item) if isinstance(item, dict) else str(item)

                    metadata = {
                        'source': 'api',
                        'api_endpoint': api_config.get('endpoint', ''),
                        'type': 'api_data',
                        'ingested_at': datetime.now().isoformat(),
                        'content_hash': hashlib.md5(content.encode()).hexdigest()
                    }

                    # Store in database
                    doc_id = await self._store_knowledge(content, metadata)

                    # Generate and store embedding
                    await self._store_embedding(doc_id, content, metadata)

                    successful += 1
                    processed += 1

                except Exception as e:
                    logger.error(f"❌ Failed to process API item: {e}")
                    processed += 1
                    continue

        except Exception as e:
            logger.error(f"❌ API data ingestion failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'stats': {'processed': processed, 'successful': successful, 'failed': processed - successful}
            }

        return {
            'status': 'completed',
            'source_type': 'api_data',
            'total_processed': processed,
            'successful': successful,
            'failed': processed - successful
        }

    async def _ingest_code_repository(self, data_source: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest code from repository"""
        repo_config = data_source.get('repo_config', {})
        processed = 0
        successful = 0

        try:
            # Get code files from repository
            code_files = await self._get_code_files(repo_config)

            for file_path, content in code_files.items():
                try:
                    metadata = {
                        'source': 'code',
                        'repository': repo_config.get('repository', ''),
                        'file_path': file_path,
                        'language': self._detect_language(file_path),
                        'type': 'code',
                        'ingested_at': datetime.now().isoformat(),
                        'content_hash': hashlib.md5(content.encode()).hexdigest()
                    }

                    # Store in database
                    doc_id = await self._store_knowledge(content, metadata)

                    # Generate and store embedding
                    await self._store_embedding(doc_id, content, metadata)

                    successful += 1
                    processed += 1

                except Exception as e:
                    logger.error(f"❌ Failed to process code file {file_path}: {e}")
                    processed += 1
                    continue

        except Exception as e:
            logger.error(f"❌ Code repository ingestion failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'stats': {'processed': processed, 'successful': successful, 'failed': processed - successful}
            }

        return {
            'status': 'completed',
            'source_type': 'code_repository',
            'total_processed': processed,
            'successful': successful,
            'failed': processed - successful
        }

    async def _store_knowledge(self, content: str, metadata: Dict[str, Any]) -> str:
        """Store knowledge in PostgreSQL database"""
        try:
            doc_id = str(uuid.uuid4())

            query = """
            INSERT INTO knowledge (id, title, content, type, source_url, metadata, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """

            title = metadata.get('title', metadata.get('filename', f'Document {doc_id[:8]}'))
            source_url = metadata.get('url', metadata.get('file_path', ''))
            doc_type = metadata.get('type', 'document')

            self.db_cursor.execute(query, (
                doc_id,
                title,
                content,
                doc_type,
                source_url,
                json.dumps(metadata)
            ))

            self.db_connection.commit()
            logger.info(f"✅ Stored knowledge document: {doc_id}")

            return doc_id

        except Exception as e:
            self.db_connection.rollback()
            logger.error(f"❌ Failed to store knowledge: {e}")
            raise

    async def _store_embedding(self, doc_id: str, content: str, metadata: Dict[str, Any]):
        """Generate and store embedding in vector database"""
        try:
            import requests

            # Generate embedding using OpenAI
            embedding = await self._generate_embedding(content)

            # Store in Qdrant
            payload = {
                "points": [{
                    "id": doc_id,
                    "vector": embedding,
                    "payload": {
                        "content": content[:1000],  # Truncate for payload
                        "metadata": metadata,
                        "doc_id": doc_id
                    }
                }]
            }

            response = requests.put(
                f"{self.config['qdrant_url']}/collections/sophia-knowledge-base/points",
                headers=self.qdrant_headers,
                json=payload
            )

            if response.status_code in [200, 201]:
                logger.info(f"✅ Stored embedding for document: {doc_id}")
            else:
                logger.error(f"❌ Failed to store embedding: {response.text}")

        except Exception as e:
            logger.error(f"❌ Failed to store embedding: {e}")

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI"""
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.config['openai_api_key'])

            response = await client.embeddings.create(
                model="text-embedding-ada-002",
                input=text[:8000]  # Truncate if too long
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {e}")
            return [0.0] * 1536  # Return zero vector on error

    async def _cache_document(self, doc_id: str, content: str, metadata: Dict[str, Any]):
        """Cache document in Redis"""
        try:
            cache_key = f"sophia:knowledge:{doc_id}"
            cache_data = {
                'content': content,
                'metadata': metadata,
                'cached_at': datetime.now().isoformat()
            }

            self.redis_client.setex(
                cache_key,
                86400,  # 24 hours
                json.dumps(cache_data)
            )

            logger.info(f"✅ Cached document: {doc_id}")

        except Exception as e:
            logger.error(f"❌ Failed to cache document: {e}")

    async def _extract_document_content(self, doc: Dict[str, Any]) -> Optional[str]:
        """Extract content from document"""
        try:
            if 'content' in doc:
                return doc['content']
            elif 'file_path' in doc:
                # Read from file
                with open(doc['file_path'], 'r', encoding='utf-8') as f:
                    return f.read()
            elif 'url' in doc:
                # Download from URL
                return await self._fetch_web_content(doc['url'])
            else:
                return None
        except Exception as e:
            logger.error(f"❌ Failed to extract document content: {e}")
            return None

    async def _fetch_web_content(self, url: str) -> Optional[str]:
        """Fetch content from web URL"""
        try:
            import requests
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"❌ Failed to fetch web content from {url}: {e}")
            return None

    async def _extract_title(self, content: str, url: str) -> str:
        """Extract title from content or URL"""
        try:
            # Simple title extraction (can be enhanced with BeautifulSoup)
            lines = content.split('\n')
            for line in lines[:10]:  # Check first 10 lines
                if 'title' in line.lower() or 'h1' in line.lower():
                    # Extract text between tags (simple regex)
                    import re
                    match = re.search(r'<title[^>]*>([^<]+)</title>', line, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()

            # Fallback to URL-based title
            return url.split('/')[-1] or 'Web Page'

        except Exception as e:
            logger.error(f"❌ Failed to extract title: {e}")
            return 'Untitled Document'

    async def _fetch_api_data(self, api_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch data from API"""
        try:
            import requests

            url = api_config.get('endpoint', '')
            headers = api_config.get('headers', {})
            params = api_config.get('params', {})

            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'results' in data:
                return data['results']
            else:
                return [data]

        except Exception as e:
            logger.error(f"❌ Failed to fetch API data: {e}")
            return []

    async def _get_code_files(self, repo_config: Dict[str, Any]) -> Dict[str, str]:
        """Get code files from repository"""
        try:
            import os

            repo_path = repo_config.get('local_path', '.')
            file_extensions = repo_config.get('extensions', ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs'])

            code_files = {}

            for root, dirs, files in os.walk(repo_path):
                for file in files:
                    if any(file.endswith(ext) for ext in file_extensions):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                code_files[file_path] = f.read()
                        except Exception as e:
                            logger.warning(f"⚠️ Could not read file {file_path}: {e}")

            return code_files

        except Exception as e:
            logger.error(f"❌ Failed to get code files: {e}")
            return {}

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file path"""
        ext = os.path.splitext(file_path)[1].lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala'
        }
        return language_map.get(ext, 'unknown')

    async def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics"""
        try:
            # Get database stats
            self.db_cursor.execute("SELECT COUNT(*) as total_docs FROM knowledge")
            db_stats = self.db_cursor.fetchone()

            # Get Redis stats
            redis_keys = len(self.redis_client.keys("sophia:knowledge:*"))

            return {
                'database_documents': db_stats['total_docs'] if db_stats else 0,
                'cached_documents': redis_keys,
                'ingestion_stats': self.ingestion_stats
            }

        except Exception as e:
            logger.error(f"❌ Failed to get ingestion stats: {e}")
            return {}

    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.db_connection:
                self.db_connection.close()
            if self.redis_client:
                self.redis_client.close()
            logger.info("✅ Pipeline resources cleaned up")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")


# Global pipeline instance
data_pipeline = DataIngestionPipeline()

async def initialize_pipeline():
    """Initialize the global data ingestion pipeline"""
    return await data_pipeline.initialize()

def get_data_pipeline():
    """Get the global data ingestion pipeline instance"""
    return data_pipeline

# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize pipeline
        success = await initialize_pipeline()
        if not success:
            print("❌ Failed to initialize data ingestion pipeline")
            return

        # Example: Ingest documents
        document_source = {
            'type': 'documents',
            'documents': [
                {
                    'filename': 'example.txt',
                    'content': 'This is an example document for Sophia AI.'
                }
            ]
        }

        result = await data_pipeline.ingest_knowledge_base(document_source)
        print(f"📊 Ingestion result: {result}")

        # Get stats
        stats = await data_pipeline.get_ingestion_stats()
        print(f"📈 Pipeline stats: {stats}")

        # Cleanup
        await data_pipeline.cleanup()

    # Run the example
    asyncio.run(main())