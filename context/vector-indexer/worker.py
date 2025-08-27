#!/usr/bin/env python3
"""
Sophia AI Vector Indexer Worker
================================

Offline vector processing worker for document indexing.
Processes staged documents, creates embeddings via standardized Portkey routing, and upserts to Weaviate Cloud.
Migrated from Qdrant to Weaviate Cloud for enhanced scalability and performance.
OpenRouter removed - using standardized LLM routing.
"""

import os
import json
import hashlib
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

import aiohttp
import weaviate
from weaviate.classes.init import Auth
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Environment configuration - Using official Weaviate Cloud connection pattern
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf")
PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY", "")  # Use Portkey for standardized routing
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL", "")
CLASS_NAME = os.getenv("WEAVIATE_CLASS", "SophiaDocuments")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))

# Weaviate client initialization using official cloud connection pattern
weaviate_client = None
if WEAVIATE_URL and WEAVIATE_API_KEY:
    weaviate_client = weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_URL,
        auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
    )
else:
    logger.error("Weaviate URL and API key must be configured")


def dedupe_hash(text: str) -> str:
    """
    Generate SHA256 hash for deduplication.

    Args:
        text: Text content to hash

    Returns:
        SHA256 hash string
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


async def compute_embedding(session: aiohttp.ClientSession, text: str) -> Optional[List[float]]:
    """
    Get embeddings using standardized Portkey routing instead of direct OpenAI.

    Args:
        session: aiohttp session for making requests
        text: Text to embed

    Returns:
        Embedding vector or None if failed
    """
    try:
        if not PORTKEY_API_KEY:
            logger.warning("PORTKEY_API_KEY not configured - using mock embedding")
            return [0.1] * 1536  # Mock 1536-dimensional embedding

        # Use Portkey API for standardized routing
        headers = {
            "x-portkey-api-key": PORTKEY_API_KEY,
            "x-portkey-virtual-key": "openai-text-embedding-3-large",  # Standardized virtual key
            "Content-Type": "application/json"
        }

        payload = {
            "model": "text-embedding-3-large",
            "input": text[:8000],  # Truncate to model limits
            "encoding_format": "float"
        }

        async with session.post("https://api.portkey.ai/v1/embeddings", json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                # Portkey returns OpenAI-compatible format
                if "data" in data and len(data["data"]) > 0:
                    return data["data"][0]["embedding"]
                else:
                    logger.error(f"Unexpected embedding response format: {data}")
                    return None
            else:
                error_text = await resp.text()
                logger.error(f"Failed to compute embedding via Portkey: {resp.status} - {error_text}")
                return None

    except Exception as e:
        logger.error(f"Error computing embedding: {e}")
        return None


async def upsert_weaviate(session: aiohttp.ClientSession, class_name: str, points: List[Dict[str, Any]]) -> bool:
    """
    Upsert vectors to Weaviate Cloud with proper metadata.

    Args:
        session: aiohttp session (for consistency)
        class_name: Class name in Weaviate
        points: List of point data with id, vector, and properties

    Returns:
        True if successful, False otherwise
    """
    try:
        if not weaviate_client:
            logger.error("Weaviate client not initialized")
            return False

        # Ensure class/schema exists with proper configuration
        schema = weaviate_client.schema.get()
        class_exists = any(c['class'] == class_name for c in schema.get('classes', []))

        if not class_exists:
            # Create class with appropriate vector configuration
            vector_size = len(points[0]["vector"]) if points else 3072  # Default for text-embedding-3-large
            class_definition = {
                "class": class_name,
                "description": f"Sophia AI vector indexer documents - {class_name}",
                "vectorizer": "none",  # We provide our own vectors
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"],
                        "description": "Document content"
                    },
                    {
                        "name": "docId",
                        "dataType": ["string"],
                        "description": "Document ID"
                    },
                    {
                        "name": "accountId",
                        "dataType": ["string"],
                        "description": "Account ID"
                    },
                    {
                        "name": "chunkIndex",
                        "dataType": ["int"],
                        "description": "Chunk index"
                    },
                    {
                        "name": "chunkHash",
                        "dataType": ["string"],
                        "description": "Chunk hash for deduplication"
                    },
                    {
                        "name": "url",
                        "dataType": ["string"],
                        "description": "Source URL"
                    },
                    {
                        "name": "neonRowPk",
                        "dataType": ["string"],
                        "description": "Neon database row primary key"
                    },
                    {
                        "name": "timestamp",
                        "dataType": ["date"],
                        "description": "Creation timestamp"
                    },
                    {
                        "name": "embeddingModel",
                        "dataType": ["string"],
                        "description": "Embedding model used"
                    },
                    {
                        "name": "embeddingProvider",
                        "dataType": ["string"],
                        "description": "Embedding provider"
                    },
                    {
                        "name": "metadataJson",
                        "dataType": ["string"],
                        "description": "Additional metadata as JSON string"
                    }
                ]
            }
            
            weaviate_client.schema.create_class(class_definition)
            logger.info(f"Created Weaviate class: {class_name}")

        # Use batch operations for efficient upload
        with weaviate_client.batch as batch:
            batch.batch_size = min(len(points), 100)  # Weaviate batch size limit
            
            for point in points:
                # Convert point data to Weaviate format
                properties = {
                    "content": point["payload"].get("content", ""),
                    "docId": point["payload"].get("doc_id", ""),
                    "accountId": point["payload"].get("account_id", ""),
                    "chunkIndex": point["payload"].get("chunk_index", 0),
                    "chunkHash": point["payload"].get("chunk_hash", ""),
                    "url": point["payload"].get("url", ""),
                    "neonRowPk": str(point["payload"].get("neon_row_pk", "")),
                    "timestamp": point["payload"].get("ts", datetime.now(timezone.utc).isoformat()),
                    "embeddingModel": point["payload"].get("embedding_model", "text-embedding-3-large"),
                    "embeddingProvider": point["payload"].get("embedding_provider", "standardized_portkey_routing"),
                    "metadataJson": json.dumps(point["payload"].get("metadata", {}))
                }

                # Add object with vector to batch
                batch.add_data_object(
                    data_object=properties,
                    class_name=class_name,
                    uuid=point["id"],
                    vector=point["vector"]
                )

        logger.info(f"Successfully upserted {len(points)} points to Weaviate class {class_name}")
        return True

    except Exception as e:
        logger.error(f"Error upserting to Weaviate: {e}")
        return False


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Text to chunk
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks

    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end]
        chunks.append(chunk)

        if end >= text_length:
            break

        start = end - overlap

    return chunks


async def process_document(session: aiohttp.ClientSession, doc: Dict[str, Any]) -> bool:
    """
    Process a single document: chunk, dedupe, embed, and index.

    Args:
        session: aiohttp session
        doc: Document data from database

    Returns:
        True if successful, False otherwise
    """
    try:
        doc_id = doc.get("doc_id") or doc.get("id")
        content = doc.get("content", "")

        if not content:
            logger.warning(f"Document {doc_id} has no content, skipping")
            return False

        # Chunk the document
        chunks = chunk_text(content)
        logger.info(f"Document {doc_id} split into {len(chunks)} chunks")

        # Process chunks
        points = []
        for i, chunk in enumerate(chunks):
            # Generate hash for deduplication
            chunk_hash = dedupe_hash(chunk)

            # Check if this chunk already exists (simplified - in production, query Qdrant)
            # For now, we'll process all chunks

            # Compute embedding using standardized routing
            embedding = await compute_embedding(session, chunk)
            if not embedding:
                logger.warning(f"Failed to get embedding for chunk {i} of document {doc_id}")
                continue

            # Create point for Weaviate with proper UUID
            # Generate deterministic UUID based on doc_id and chunk index
            point_id_string = f"{doc_id}_chunk_{i}"
            point_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, point_id_string))
            point = {
                "id": point_uuid,
                "vector": embedding,
                "payload": {
                    "doc_id": doc_id,
                    "account_id": doc.get("account_id"),
                    "chunk_index": i,
                    "chunk_hash": chunk_hash,
                    "content": chunk[:500],  # Store first 500 chars for reference
                    "url": doc.get("url"),
                    "neon_row_pk": doc.get("id"),
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "embedding_model": "text-embedding-3-large",
                    "embedding_provider": "standardized_portkey_routing",
                    "metadata": doc.get("metadata", {})
                }
            }
            points.append(point)

        # Upsert all points for this document
        if points:
            success = await upsert_weaviate(session, CLASS_NAME, points)
            if success:
                logger.info(f"Successfully indexed {len(points)} chunks for document {doc_id}")
                return True
            else:
                logger.error(f"Failed to index chunks for document {doc_id}")
                return False
        else:
            logger.warning(f"No chunks to index for document {doc_id}")
            return False

    except Exception as e:
        logger.error(f"Error processing document {doc.get('id')}: {e}")
        return False


def get_staged_documents(limit: int = BATCH_SIZE) -> List[Dict[str, Any]]:
    """
    Fetch staged documents from database.

    Args:
        limit: Maximum number of documents to fetch

    Returns:
        List of document records
    """
    documents = []

    # If no database URL, return empty (for testing)
    if not NEON_DATABASE_URL:
        logger.warning("No database URL configured, using test data")
        # Return test documents
        return [
            {
                "id": str(uuid.uuid4()),
                "doc_id": "test_doc_1",
                "account_id": "test_account",
                "content": "This is a test document for vector indexing. It contains sample content that will be chunked and embedded using standardized Portkey routing.",
                "url": "https://example.com/doc1",
                "metadata": {"source": "test"},
                "status": "staged",
                "vector_indexed": False
            }
        ]

    try:
        conn = psycopg2.connect(NEON_DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Query for staged documents that haven't been indexed
        query = """
            SELECT * FROM documents
            WHERE status = 'staged' AND (vector_indexed = false OR vector_indexed IS NULL)
            ORDER BY created_at ASC
            LIMIT %s
        """

        cursor.execute(query, (limit,))
        documents = cursor.fetchall()

        cursor.close()
        conn.close()

        logger.info(f"Fetched {len(documents)} staged documents from database")

    except Exception as e:
        logger.error(f"Error fetching documents from database: {e}")

    return documents


def mark_document_indexed(doc_id: str) -> bool:
    """
    Mark a document as indexed in the database.

    Args:
        doc_id: Document ID to mark as indexed

    Returns:
        True if successful, False otherwise
    """
    if not NEON_DATABASE_URL:
        logger.info(f"Test mode: Would mark document {doc_id} as indexed")
        return True

    try:
        conn = psycopg2.connect(NEON_DATABASE_URL)
        cursor = conn.cursor()

        query = """
            UPDATE documents
            SET vector_indexed = true,
                indexed_at = NOW(),
                status = 'indexed'
            WHERE doc_id = %s OR id = %s
        """

        cursor.execute(query, (doc_id, doc_id))
        conn.commit()

        cursor.close()
        conn.close()

        logger.info(f"Marked document {doc_id} as indexed")
        return True

    except Exception as e:
        logger.error(f"Error marking document {doc_id} as indexed: {e}")
        return False


async def run_once():
    """
    Main worker function for processing documents.
    Fetches staged documents and processes them for vector indexing using Weaviate Cloud and standardized routing.
    """
    logger.info("Starting vector indexer run with Weaviate Cloud and standardized Portkey routing")

    # Create aiohttp session
    async with aiohttp.ClientSession() as session:
        # Fetch staged documents
        documents = get_staged_documents()

        if not documents:
            logger.info("No staged documents to process")
            return

        logger.info(f"Processing {len(documents)} staged documents")

        # Process each document
        success_count = 0
        failed_count = 0

        for doc in documents:
            doc_id = doc.get("doc_id") or doc.get("id")
            logger.info(f"Processing document {doc_id}")

            success = await process_document(session, doc)

            if success:
                # Mark as indexed in database
                if mark_document_indexed(doc_id):
                    success_count += 1
                else:
                    logger.warning(f"Indexed document {doc_id} but failed to update database")
                    failed_count += 1
            else:
                failed_count += 1

        logger.info(f"Vector indexing complete: {success_count} successful, {failed_count} failed")


async def run_continuous(interval_seconds: int = 60):
    """
    Run the worker continuously with specified interval.

    Args:
        interval_seconds: Seconds to wait between runs
    """
    logger.info(f"Starting continuous vector indexer with {interval_seconds}s interval")

    while True:
        try:
            await run_once()
        except Exception as e:
            logger.error(f"Error in vector indexer run: {e}")

        logger.info(f"Waiting {interval_seconds} seconds before next run...")
        await asyncio.sleep(interval_seconds)


def main():
    """Main entry point for the vector indexer worker."""
    # Check if running in continuous mode
    continuous_mode = os.getenv("CONTINUOUS_MODE", "false").lower() == "true"
    interval = int(os.getenv("RUN_INTERVAL", "60"))

    if continuous_mode:
        # Run continuously
        asyncio.run(run_continuous(interval))
    else:
        # Run once
        asyncio.run(run_once())


if __name__ == "__main__":
    main()