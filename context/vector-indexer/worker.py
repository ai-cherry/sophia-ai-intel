#!/usr/bin/env python3
"""
Sophia AI Vector Indexer Worker
================================

Offline vector processing worker for document indexing.
Processes staged documents, creates embeddings, and upserts to Qdrant.
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
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Environment configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
# Use native OpenAI endpoint for embeddings
EMBED_ENDPOINT = os.getenv("EMBED_ENDPOINT", "https://api.openai.com/v1/embeddings")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-large")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # Use OpenAI API key directly
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL", "")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "sophia_documents")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))

# Qdrant client initialization
qdrant_client = None
if QDRANT_API_KEY:
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
else:
    qdrant_client = QdrantClient(url=QDRANT_URL)


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
    Get embeddings from native OpenAI API endpoint.
    
    Args:
        session: aiohttp session for making requests
        text: Text to embed
        
    Returns:
        Embedding vector or None if failed
    """
    try:
        # Use OpenAI API key directly
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": EMBED_MODEL,
            "input": text
        }
        
        async with session.post(EMBED_ENDPOINT, json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                # OpenAI standard response format
                if "data" in data and len(data["data"]) > 0:
                    return data["data"][0]["embedding"]
                else:
                    logger.error(f"Unexpected embedding response format: {data}")
                    return None
            else:
                error_text = await resp.text()
                logger.error(f"Failed to compute embedding: {resp.status} - {error_text}")
                return None
                
    except Exception as e:
        logger.error(f"Error computing embedding: {e}")
        return None


async def upsert_qdrant(session: aiohttp.ClientSession, collection: str, points: List[Dict[str, Any]]) -> bool:
    """
    Upsert vectors to Qdrant with proper metadata.
    
    Args:
        session: aiohttp session (for consistency, though Qdrant client handles its own)
        collection: Collection name in Qdrant
        points: List of point data with id, vector, and payload
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure collection exists with proper configuration
        collections = qdrant_client.get_collections().collections
        collection_exists = any(c.name == collection for c in collections)
        
        if not collection_exists:
            # Create collection with appropriate vector size
            vector_size = len(points[0]["vector"]) if points else 3072  # Default for text-embedding-3-large
            qdrant_client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            logger.info(f"Created Qdrant collection: {collection}")
        
        # Convert points to Qdrant format
        qdrant_points = []
        for point in points:
            qdrant_point = PointStruct(
                id=point["id"],
                vector=point["vector"],
                payload=point["payload"]
            )
            qdrant_points.append(qdrant_point)
        
        # Upsert points
        operation_info = qdrant_client.upsert(
            collection_name=collection,
            wait=True,
            points=qdrant_points
        )
        
        logger.info(f"Successfully upserted {len(qdrant_points)} points to Qdrant collection {collection}")
        return True
        
    except Exception as e:
        logger.error(f"Error upserting to Qdrant: {e}")
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
            
            # Compute embedding
            embedding = await compute_embedding(session, chunk)
            if not embedding:
                logger.warning(f"Failed to get embedding for chunk {i} of document {doc_id}")
                continue
            
            # Create point for Qdrant
            point_id = f"{doc_id}_chunk_{i}"
            point = {
                "id": point_id,
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
                    "embedding_model": EMBED_MODEL,
                    "metadata": doc.get("metadata", {})
                }
            }
            points.append(point)
        
        # Upsert all points for this document
        if points:
            success = await upsert_qdrant(session, COLLECTION_NAME, points)
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
                "content": "This is a test document for vector indexing. It contains sample content that will be chunked and embedded.",
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
    Fetches staged documents and processes them for vector indexing.
    """
    logger.info("Starting vector indexer run")
    
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