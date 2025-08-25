import os
import uuid
from typing import List, Dict
import asyncpg
from qdrant_client import QdrantClient, models
from openai import OpenAI
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Set up logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variables
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Consistent with other MCPs

# Initialize OpenAI client only if API key is set
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Initialize FastAPI app
app = FastAPI(
    title="Sophia AI Symbol Indexer MCP",
    description="Code symbol indexing and semantic search service",
    version="1.0.0"
)

# Database connection pool
db_pool = None


async def get_db_pool():
    global db_pool
    if not db_pool and NEON_DATABASE_URL:
        db_pool = await asyncpg.create_pool(NEON_DATABASE_URL)
    return db_pool


# Qdrant client
qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,  # Check if QDRANT_API_KEY is available
)


async def create_embedding(
    text: str, model: str = "text-embedding-ada-002"
) -> List[float]:
    """
    Generates an embedding for the given text using OpenAI's API.
    """
    if not client:
        raise ValueError("OpenAI client not initialized. OPENAI_API_KEY is missing.")

    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding


async def retrieve_relevant_symbols(query: str, limit: int = 5) -> List[Dict]:
    """
    Retrieves relevant symbols from Qdrant based on a query embedding.
    """
    if not QDRANT_URL or not QDRANT_API_KEY:
        logger.warning("Qdrant not configured, cannot retrieve symbols.")
        return []

    query_embedding = await create_embedding(query)

    search_result = qdrant_client.search(
        collection_name="sophia_code_symbols",
        query_vector=query_embedding,
        limit=limit,
        query_params=models.QueryParams(
            hnsw_ef=128, exact=False
        ),  # Parameters adjusted for better search quality
    )

    symbols = []
    for hit in search_result:
        symbols.append(
            {
                "name": hit.payload.get("name"),
                "kind": hit.payload.get("kind"),
                "file": hit.payload.get("file"),
                "line": hit.payload.get("line"),
                "score": hit.score,
                "snippet": hit.payload.get("snippet", ""),  # Include snippet
            }
        )
    return symbols


async def index_repository_symbols(repo_path: str):
    """
    Indexes code symbols from a given repository path into Qdrant.
    This function will scan files, extract symbols, create embeddings, and upsert them into Qdrant.
    """
    if not QDRANT_URL or not QDRANT_API_KEY:
        logger.warning("Qdrant not configured, skipping repository indexing.")
        return

    # Ensure the collection exists
    qdrant_client.recreate_collection(
        collection_name="sophia_code_symbols",
        vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
    )

    points = []
    for root, _, files in os.walk(repo_path):
        for file_name in files:
            if file_name.endswith(
                (".py", ".ts", ".js", ".tsx", ".java", ".go", ".rs")
            ):  # Supported file types
                file_path = os.path.join(root, file_name)
                relative_file_path = os.path.relpath(file_path, repo_path)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Simple symbol extraction (can be enhanced with AST parsing)
                    lines = content.splitlines()
                    for i, line in enumerate(lines):
                        line_number = i + 1
                        symbol_name = None
                        symbol_kind = None

                        if "def " in line and "(" in line:
                            symbol_name = line.split("def ")[1].split("(")[0].strip()
                            symbol_kind = "function"
                        elif "class " in line and ":" in line:
                            symbol_name = line.split("class ")[1].split(":")[0].strip()
                            symbol_kind = "class"

                        if symbol_name:
                            snippet = "\n".join(
                                lines[max(0, i - 2) : i + 3]
                            )  # 5-line snippet
                            vector = await create_embedding(
                                f"{symbol_kind} {symbol_name} in {relative_file_path}: {snippet}"
                            )

                            points.append(
                                models.PointStruct(
                                    id=str(uuid.uuid4()),
                                    vector=vector,
                                    payload={
                                        "name": symbol_name,
                                        "kind": symbol_kind,
                                        "file": relative_file_path,
                                        "line": line_number,
                                        "snippet": snippet,
                                    },
                                )
                            )
                except Exception as e:
                    logger.warning(f"Failed to process {file_path}: {e}")

    if points:
        qdrant_client.upsert(
            collection_name="sophia_code_symbols",
            wait=True,
            points=points,
        )
        logger.info(
            f"Indexed {len(points)} symbols into Qdrant collection 'sophia_code_symbols'"
        )
    else:
        logger.info("No symbols found or indexed.")


class IndexRepoRequest(BaseModel):
    repo_path: str = Field(..., description="Path to the repository to index")


@app.post("/index-repo-symbols")
async def index_repo_symbols_api(request: IndexRepoRequest):
    """
    API endpoint to trigger repository symbol indexing.
    """
    try:
        await index_repository_symbols(request.repo_path)
        return JSONResponse(
            status_code=200, content={"message": "Repository indexing started."}
        )
    except Exception as e:
        logger.error(f"Error during repository indexing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    if NEON_DATABASE_URL:
        await get_db_pool()
        logger.info("Symbol Indexer MCP v1 started with database connectivity")
    else:
        logger.warning(
            "Symbol Indexer MCP v1 started without database - storage disabled"
        )


@app.on_event("shutdown")
async def shutdown_event():
    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")


qdrant_client.close()  # Ensure qdrant client is closed properly

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
