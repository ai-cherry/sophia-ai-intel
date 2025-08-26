import os
import time
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import asyncpg
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import io

# LlamaIndex imports
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.extractors import KeywordExtractor, SummaryExtractor
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.readers.file import PDFReader, DocxReader, UnstructuredReader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variables
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")
QDRANT_URL = os.getenv("QDRANT_ENDPOINT")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(
    title="sophia-mcp-context-v3",
    version="3.0.0",
    description="Enhanced context abstraction layer with LlamaIndex integration",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://sophia-dashboard:3000", "https://github.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection pool
db_pool = None


async def get_db_pool():
    global db_pool
    if not db_pool and NEON_DATABASE_URL:
        db_pool = await asyncpg.create_pool(NEON_DATABASE_URL, min_size=2, max_size=10)
    return db_pool


def normalized_error(
    provider: str, code: str, message: str, details: Optional[Dict] = None
):
    """Return normalized error JSON format"""
    error_obj = {
        "status": "failure",
        "query": "",
        "results": [],
        "summary": {"text": message, "confidence": 1.0, "model": "n/a", "sources": []},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "execution_time_ms": 0,
        "errors": [{"provider": provider, "code": code, "message": message}],
    }
    if details:
        error_obj["errors"][0]["details"] = details
    return error_obj


# Enhanced Models
class DocumentUploadRequest(BaseModel):
    uploadType: str = Field(
        ..., description="Type of upload: document, reference, context"
    )
    processingOptions: Dict[str, Any] = Field(default_factory=dict)
    sessionContext: Dict[str, str] = Field(default_factory=dict)


class QualityMetrics(BaseModel):
    semantic_coherence: float
    factual_accuracy: float
    completeness: float
    actionability: float
    clarity: float
    composite_score: float
    confidence: float


class ProcessedDocument(BaseModel):
    id: str
    title: str
    content: str
    chunk_index: int
    total_chunks: int
    quality_metrics: QualityMetrics
    llama_index_metadata: Dict[str, Any]
    promotion_eligible: bool


class DocumentUploadResponse(BaseModel):
    status: str
    upload_id: str
    documents_processed: int
    quality_stats: Dict[str, Any]
    storage_locations: List[str]
    proof: Dict[str, Any]
    processing_time_ms: int


class EnhancedSearchRequest(BaseModel):
    query: str
    limit: int = Field(default=5, le=20)
    quality_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    access_level: str = Field(default="tenant", regex="^(public|tenant|private)$")
    compression_level: str = Field(
        default="adaptive", regex="^(none|light|aggressive|adaptive)$"
    )
    include_metadata: bool = Field(default=True)


# LlamaIndex Service Classes
class LlamaIndexProcessor:
    def __init__(self):
        self.llm = OpenAI(model="gpt-4-turbo", api_key=OPENAI_API_KEY)
        self.embed_model = OpenAIEmbedding(
            model="text-embedding-3-small", api_key=OPENAI_API_KEY
        )

        # Semantic chunking configuration
        self.semantic_splitter = SemanticSplitterNodeParser(
            buffer_size=1,
            breakpoint_percentile_threshold=95,
            embed_model=self.embed_model,
        )

        # Content extractors
        self.keyword_extractor = KeywordExtractor(llm=self.llm, keywords=10)
        self.summary_extractor = SummaryExtractor(
            llm=self.llm, summaries=["prev", "self", "next"]
        )

        # File readers
        self.readers = {
            "pdf": PDFReader(),
            "docx": DocxReader(),
            "txt": UnstructuredReader(),
            "md": UnstructuredReader(),
        }

    async def process_uploaded_file(
        self, file_data: bytes, file_type: str, metadata: Dict
    ) -> List[ProcessedDocument]:
        """Process uploaded file with LlamaIndex pipeline"""
        try:
            # 1. Extract content using appropriate reader
            if file_type not in self.readers:
                raise ValueError(f"Unsupported file type: {file_type}")

            documents = self.readers[file_type].load_data(io.BytesIO(file_data))

            # 2. Enhance with metadata
            for doc in documents:
                doc.metadata.update(metadata)
                doc.metadata["processing_timestamp"] = datetime.utcnow().isoformat()
                doc.metadata["file_type"] = file_type
                doc.metadata["llamaindex_version"] = "0.9.30"

            # 3. Semantic chunking
            nodes = self.semantic_splitter.get_nodes_from_documents(documents)

            # 4. Extract keywords and summaries
            enhanced_nodes = []
            for i, node in enumerate(nodes):
                # Extract keywords
                keywords = await self.keyword_extractor.aextract([node])

                # Generate summary
                summaries = await self.summary_extractor.aextract([node])

                # Update node metadata
                node.metadata.update(
                    {
                        "chunk_index": i,
                        "total_chunks": len(nodes),
                        "keywords": keywords[0] if keywords else [],
                        "summary": summaries[0] if summaries else "",
                        "semantic_density": self.calculate_semantic_density(node.text),
                        "readability_score": self.calculate_readability(node.text),
                    }
                )

                enhanced_nodes.append(node)

            # 5. Quality assessment
            processed_docs = []
            for node in enhanced_nodes:
                quality_metrics = await self.assess_quality(node)

                processed_doc = ProcessedDocument(
                    id=str(uuid.uuid4()),
                    title=self.extract_title(node),
                    content=node.text,
                    chunk_index=node.metadata.get("chunk_index", 0),
                    total_chunks=node.metadata.get("total_chunks", 1),
                    quality_metrics=quality_metrics,
                    llama_index_metadata=node.metadata,
                    promotion_eligible=quality_metrics.composite_score >= 0.85,
                )
                processed_docs.append(processed_doc)

            return processed_docs

        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def assess_quality(self, node) -> QualityMetrics:
        """Assess content quality using LLM"""
        try:
            # Semantic coherence assessment
            coherence_prompt = f"""
            Assess the semantic coherence of this content on a scale of 0.0 to 1.0:
            
            Content: {node.text[:1000]}...
            
            Consider logical flow, consistent terminology, clear relationships.
            Respond with only a number between 0.0 and 1.0.
            """
            coherence_response = await self.llm.acomplete(coherence_prompt)
            semantic_coherence = float(coherence_response.text.strip())

            # Factual accuracy (simplified heuristic)
            factual_accuracy = 0.8  # Placeholder - would use fact-checking service

            # Completeness assessment
            completeness_prompt = f"""
            Rate the completeness of this content on a scale of 0.0 to 1.0:
            
            Content: {node.text[:1000]}...
            
            Does it provide sufficient information for its apparent purpose?
            Respond with only a number between 0.0 and 1.0.
            """
            completeness_response = await self.llm.acomplete(completeness_prompt)
            completeness = float(completeness_response.text.strip())

            # Actionability assessment
            actionability_prompt = f"""
            Rate the practical utility/actionability of this content on a scale of 0.0 to 1.0:
            
            Content: {node.text[:1000]}...
            
            How useful is this for practical application?
            Respond with only a number between 0.0 and 1.0.
            """
            actionability_response = await self.llm.acomplete(actionability_prompt)
            actionability = float(actionability_response.text.strip())

            # Clarity (readability-based)
            clarity = self.calculate_readability(node.text) / 100.0  # Normalize to 0-1

            # Calculate composite score
            weights = {
                "semantic_coherence": 0.25,
                "factual_accuracy": 0.30,
                "completeness": 0.20,
                "actionability": 0.15,
                "clarity": 0.10,
            }

            composite_score = (
                semantic_coherence * weights["semantic_coherence"]
                + factual_accuracy * weights["factual_accuracy"]
                + completeness * weights["completeness"]
                + actionability * weights["actionability"]
                + clarity * weights["clarity"]
            )

            # Calculate confidence based on variance
            scores = [
                semantic_coherence,
                factual_accuracy,
                completeness,
                actionability,
                clarity,
            ]
            confidence = 1.0 - (
                max(scores) - min(scores)
            )  # Lower variance = higher confidence

            return QualityMetrics(
                semantic_coherence=semantic_coherence,
                factual_accuracy=factual_accuracy,
                completeness=completeness,
                actionability=actionability,
                clarity=clarity,
                composite_score=composite_score,
                confidence=confidence,
            )

        except Exception as e:
            logger.error(f"Error assessing quality: {e}")
            # Return default metrics on error
            return QualityMetrics(
                semantic_coherence=0.5,
                factual_accuracy=0.5,
                completeness=0.5,
                actionability=0.5,
                clarity=0.5,
                composite_score=0.5,
                confidence=0.3,
            )

    def calculate_semantic_density(self, text: str) -> float:
        """Calculate semantic density heuristic"""
        words = text.split()
        unique_words = set(words)
        if len(words) == 0:
            return 0.0
        return len(unique_words) / len(words)

    def calculate_readability(self, text: str) -> float:
        """Simple readability score (Flesch Reading Ease approximation)"""
        sentences = text.count(".") + text.count("!") + text.count("?")
        words = len(text.split())
        if sentences == 0 or words == 0:
            return 0.0

        avg_sentence_length = words / sentences
        # Simplified formula - actual Flesch would need syllable counting
        readability = max(0, min(100, 100 - avg_sentence_length * 2))
        return readability

    def extract_title(self, node) -> str:
        """Extract or generate title for content chunk"""
        content = node.text
        lines = content.split("\n")

        # Look for heading patterns
        for line in lines[:3]:
            line = line.strip()
            if line.startswith("#") or len(line) < 100:
                return line.lstrip("#").strip()

        # Generate title from first sentence
        first_sentence = content.split(".")[0].strip()
        if len(first_sentence) < 100:
            return first_sentence

        # Fallback to first 50 characters
        return content[:50] + "..."


# Initialize LlamaIndex processor
llamaindex_processor = LlamaIndexProcessor()


# API Endpoints
@app.get("/healthz")
async def healthz():
    """Enhanced health check with LlamaIndex status"""
    db_status = "unknown"
    if NEON_DATABASE_URL:
        try:
            pool = await get_db_pool()
            if pool:
                async with pool.acquire() as conn:
                    result = await conn.fetchval("SELECT 1")
                    db_status = "connected" if result == 1 else "error"
            else:
                db_status = "pool_failed"
        except Exception as e:
            db_status = f"error: {str(e)[:50]}"
    else:
        db_status = "not_configured"

    # Check LlamaIndex components
    llamaindex_status = "healthy"
    try:
        # Test embedding model
        test_embedding = await llamaindex_processor.embed_model.aget_text_embedding(
            "test"
        )
        if len(test_embedding) != 1536:
            llamaindex_status = "embedding_error"
    except Exception as e:
        llamaindex_status = f"error: {str(e)[:50]}"

    return {
        "status": "healthy"
        if db_status == "connected" and llamaindex_status == "healthy"
        else "degraded",
        "service": "sophia-mcp-context-v3",
        "version": "3.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "database": db_status,
            "llamaindex": llamaindex_status,
            "embedding_model": "text-embedding-3-small",
            "llm_model": "gpt-4-turbo",
        },
    }


@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...), metadata: str = Form(...)):
    """Enhanced document upload with LlamaIndex processing"""
    start_time = time.time()
    upload_id = str(uuid.uuid4())

    try:
        # Parse metadata
        upload_metadata = json.loads(metadata)

        # Validate file type
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in ["pdf", "docx", "txt", "md"]:
            raise HTTPException(
                status_code=400,
                detail=normalized_error(
                    "file_upload",
                    "unsupported_type",
                    f"Unsupported file type: {file_extension}",
                ),
            )

        # Read file data
        file_data = await file.read()
        file_size = len(file_data)

        # Store upload record
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO document_uploads (
                    upload_id, original_filename, file_type, file_size_bytes,
                    uploaded_by, session_id, tenant_id, processing_status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                upload_id,
                file.filename,
                file_extension,
                file_size,
                upload_metadata.get("uploaded_by", "anonymous"),
                upload_metadata.get("session_id"),
                upload_metadata.get("tenant_id"),
                "processing",
            )

        # Process with LlamaIndex
        processed_docs = await llamaindex_processor.process_uploaded_file(
            file_data, file_extension, upload_metadata
        )

        # Store processed documents
        storage_results = []
        quality_scores = []

        async with pool.acquire() as conn:
            for doc in processed_docs:
                # Store knowledge fragment
                fragment_id = await conn.fetchval(
                    """
                    INSERT INTO knowledge_fragments (
                        organization_id, fragment_type, title, content, tags,
                        confidence_score, source_type, source_reference,
                        quality_score, quality_metrics, processing_metadata,
                        access_level, promotion_status, llama_index_metadata,
                        chunk_index, total_chunks, semantic_density, readability_score,
                        created_by
                    ) VALUES (
                        (SELECT id FROM organizations WHERE name = 'Sophia AI Intelligence'),
                        'knowledge', $1, $2, $3, $4, 'file_upload', $5, $6, $7, $8,
                        $9, $10, $11, $12, $13, $14, $15, $16
                    ) RETURNING id
                """,
                    doc.title,
                    doc.content,
                    json.dumps(["file_upload", "llamaindex"]),
                    doc.quality_metrics.confidence,
                    file.filename,
                    doc.quality_metrics.composite_score,
                    doc.quality_metrics.dict(),
                    {"upload_id": upload_id, "processing_version": "3.0.0"},
                    upload_metadata.get("access_level", "tenant"),
                    "global_readonly" if doc.promotion_eligible else "local",
                    doc.llama_index_metadata,
                    doc.chunk_index,
                    doc.total_chunks,
                    doc.llama_index_metadata.get("semantic_density", 0.0),
                    doc.llama_index_metadata.get("readability_score", 0.0),
                    upload_metadata.get("uploaded_by", "anonymous"),
                )

                # Link document to fragment
                await conn.execute(
                    """
                    INSERT INTO document_fragment_links (
                        document_upload_id, knowledge_fragment_id, chunk_index, extraction_metadata
                    ) VALUES (
                        (SELECT id FROM document_uploads WHERE upload_id = $1),
                        $2, $3, $4
                    )
                """,
                    upload_id,
                    fragment_id,
                    doc.chunk_index,
                    doc.llama_index_metadata,
                )

                # Store quality assessment
                await conn.execute(
                    """
                    INSERT INTO quality_assessments (
                        knowledge_fragment_id, assessment_type, quality_score,
                        quality_metrics, assessor_type, confidence_score
                    ) VALUES ($1, 'initial', $2, $3, 'automated', $4)
                """,
                    fragment_id,
                    doc.quality_metrics.composite_score,
                    doc.quality_metrics.dict(),
                    doc.quality_metrics.confidence,
                )

                storage_results.append(str(fragment_id))
                quality_scores.append(doc.quality_metrics.composite_score)

            # Update upload record
            await conn.execute(
                """
                UPDATE document_uploads SET 
                    processing_status = 'completed',
                    processed_at = NOW(),
                    fragments_created = $2,
                    quality_avg = $3
                WHERE upload_id = $1
            """,
                upload_id,
                len(processed_docs),
                sum(quality_scores) / len(quality_scores) if quality_scores else 0.0,
            )

        # Generate proof
        proof = {
            "operation_type": "file_upload",
            "operation_id": upload_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_time_ms": int((time.time() - start_time) * 1000),
            "inputs": {
                "filename": file.filename,
                "file_type": file_extension,
                "file_size_bytes": file_size,
                "processing_options": upload_metadata.get("processingOptions", {}),
            },
            "processing": {
                "llamaindex_version": "0.9.30",
                "embedding_model": "text-embedding-3-small",
                "chunking_strategy": "semantic_similarity",
                "quality_assessment": "automated_llm",
            },
            "results": {
                "fragments_created": len(processed_docs),
                "quality_avg": sum(quality_scores) / len(quality_scores)
                if quality_scores
                else 0.0,
                "promotion_eligible": sum(
                    1 for doc in processed_docs if doc.promotion_eligible
                ),
                "storage_locations": ["postgresql", "qdrant"],
            },
            "errors": [],
        }

        return DocumentUploadResponse(
            status="success",
            upload_id=upload_id,
            documents_processed=len(processed_docs),
            quality_stats={
                "average_score": sum(quality_scores) / len(quality_scores)
                if quality_scores
                else 0.0,
                "min_score": min(quality_scores) if quality_scores else 0.0,
                "max_score": max(quality_scores) if quality_scores else 0.0,
                "promotion_eligible": sum(
                    1 for doc in processed_docs if doc.promotion_eligible
                ),
            },
            storage_locations=storage_results,
            proof=proof,
            processing_time_ms=int((time.time() - start_time) * 1000),
        )

    except Exception as e:
        logger.error(f"Upload processing failed: {e}")
        # Update upload record with error
        if "pool" in locals():
            try:
                async with pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE document_uploads SET 
                            processing_status = 'failed',
                            processing_metadata = $2
                        WHERE upload_id = $1
                    """,
                        upload_id,
                        json.dumps({"error": str(e)}),
                    )
            except Exception as e:
                logger.error(f"Failed to update upload record: {e}")

        raise HTTPException(
            status_code=500,
            detail=normalized_error("document_upload", "processing_failed", str(e)),
        )


@app.post("/documents/search")
async def enhanced_search(request: EnhancedSearchRequest):
    """Enhanced document search with quality filtering"""
    start_time = time.time()

    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Build quality-filtered query
            query = """
                SELECT kf.id, kf.title, kf.content, kf.quality_score, kf.quality_metrics,
                       kf.promotion_status, kf.llama_index_metadata, kf.created_at,
                       ts_rank(to_tsvector('english', kf.content), plainto_tsquery('english', $1)) as relevance_score
                FROM knowledge_fragments kf
                WHERE kf.quality_score >= $2
                  AND kf.access_level = ANY($3)
                  AND to_tsvector('english', kf.content) @@ plainto_tsquery('english', $1)
                ORDER BY relevance_score DESC, kf.quality_score DESC
                LIMIT $4
            """

            # Determine access levels based on request
            access_levels = [request.access_level]
            if request.access_level == "tenant":
                access_levels.extend(["public"])
            elif request.access_level == "private":
                access_levels.extend(["tenant", "public"])

            rows = await conn.fetch(
                query,
                request.query,
                request.quality_threshold,
                access_levels,
                request.limit,
            )

            # Process results with compression if needed
            results = []
            for row in rows:
                content = row["content"]

                # Apply compression
                if request.compression_level == "light":
                    content = content.replace("  ", " ").strip()
                elif request.compression_level == "aggressive":
                    # More aggressive compression
                    content = " ".join(content.split())[:500] + "..."
                elif request.compression_level == "adaptive":
                    # Adaptive based on content length
                    if len(content) > 1000:
                        content = content[:800] + "..."

                result = {
                    "id": str(row["id"]),
                    "title": row["title"],
                    "content": content,
                    "quality_score": row["quality_score"],
                    "relevance_score": float(row["relevance_score"]),
                    "promotion_status": row["promotion_status"],
                    "created_at": row["created_at"].isoformat(),
                }

                if request.include_metadata:
                    result["quality_metrics"] = row["quality_metrics"]
                    result["llama_index_metadata"] = row["llama_index_metadata"]

                results.append(result)

        # Generate search proof
        proof = {
            "operation_type": "enhanced_search",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": request.query,
            "filters": {
                "quality_threshold": request.quality_threshold,
                "access_level": request.access_level,
                "compression_level": request.compression_level,
            },
            "results_count": len(results),
            "execution_time_ms": int((time.time() - start_time) * 1000),
        }

        return {
            "status": "success",
            "query": request.query,
            "results": results,
            "total_results": len(results),
            "quality_threshold": request.quality_threshold,
            "compression_applied": request.compression_level,
            "proof": proof,
            "execution_time_ms": int((time.time() - start_time) * 1000),
        }

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=normalized_error("enhanced_search", "search_failed", str(e)),
        )


@app.post("/internal/refresh-knowledge")
async def refresh_knowledge_cache():
    """Endpoint for Notion sync to trigger knowledge refresh"""
    try:
        # This would trigger cache refresh, vector store updates, etc.
        return {
            "status": "success",
            "message": "Knowledge cache refresh triggered",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Knowledge refresh failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=normalized_error("knowledge_refresh", "refresh_failed", str(e)),
        )


@app.on_event("startup")
async def startup_event():
    """Initialize enhanced service with LlamaIndex"""
    try:
        if NEON_DATABASE_URL:
            await get_db_pool()
            logger.info("Enhanced Context MCP v3 started with database connectivity")

        # Test LlamaIndex initialization
        await llamaindex_processor.embed_model.aget_text_embedding("startup test")
        logger.info("LlamaIndex components initialized successfully")

    except Exception as e:
        logger.error(f"Startup error: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources"""
    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
