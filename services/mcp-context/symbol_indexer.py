import os
import uuid
from typing import List, Dict
import asyncpg
import weaviate
from weaviate.classes.init import Auth
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
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
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


# Weaviate client using official cloud connection pattern
weaviate_client = weaviate.connect_to_weaviate_cloud(
    cluster_url=WEAVIATE_URL,
    auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
) if WEAVIATE_URL and WEAVIATE_API_KEY else None


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
    Retrieves relevant symbols from Weaviate based on a query embedding.
    """
    if not WEAVIATE_URL or not WEAVIATE_API_KEY or not weaviate_client:
        logger.warning("Weaviate not configured, cannot retrieve symbols.")
        return []

    query_embedding = await create_embedding(query)

    near_vector = {"vector": query_embedding}
    
    response = (
        weaviate_client.query
        .get("SophiaCodeSymbols", ["name", "kind", "file", "line", "snippet"])
        .with_near_vector(near_vector)
        .with_limit(limit)
        .with_additional(["id", "distance"])
        .do()
    )

    symbols = []
    if 'data' in response and 'Get' in response['data'] and 'SophiaCodeSymbols' in response['data']['Get']:
        for item in response['data']['Get']['SophiaCodeSymbols']:
            # Convert distance to score (higher score = better match)
            distance = item['_additional']['distance']
            score = 1.0 - distance if distance is not None else 0.0
            
            symbols.append({
                "name": item.get("name"),
                "kind": item.get("kind"),
                "file": item.get("file"),
                "line": item.get("line"),
                "score": score,
                "snippet": item.get("snippet", ""),
            })
    return symbols


async def index_repository_symbols(repo_path: str):
    """
    Indexes code symbols from a given repository path into Weaviate.
    This function will scan files, extract symbols, create embeddings, and store them in Weaviate.
    """
    if not WEAVIATE_URL or not WEAVIATE_API_KEY or not weaviate_client:
        logger.warning("Weaviate not configured, skipping repository indexing.")
        return

    # Ensure the schema exists
    _ensure_symbols_schema_exists()

    data_objects = []
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

                            data_objects.append({
                                "data_object": {
                                    "name": symbol_name,
                                    "kind": symbol_kind,
                                    "file": relative_file_path,
                                    "line": line_number,
                                    "snippet": snippet,
                                },
                                "vector": vector
                            })
                except Exception as e:
                    logger.warning(f"Failed to process {file_path}: {e}")

    if data_objects:
        # Batch create objects in Weaviate
        for obj in data_objects:
            try:
                weaviate_client.data_object.create(
                    data_object=obj["data_object"],
                    class_name="SophiaCodeSymbols",
                    vector=obj["vector"]
                )
            except Exception as e:
                logger.warning(f"Failed to create symbol object: {e}")
        
        logger.info(
            f"Indexed {len(data_objects)} symbols into Weaviate class 'SophiaCodeSymbols'"
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


def _ensure_symbols_schema_exists():
    """Ensure Weaviate schema for code symbols exists"""
    if not weaviate_client:
        return
        
    try:
        schema = weaviate_client.schema.get()
        class_exists = any(c['class'] == "SophiaCodeSymbols" for c in schema.get('classes', []))

        if not class_exists:
            class_definition = {
                "class": "SophiaCodeSymbols",
                "description": "Code symbols indexed for semantic search",
                "vectorizer": "none",  # We provide our own vectors
                "properties": [
                    {
                        "name": "name",
                        "dataType": ["string"],
                        "description": "Symbol name"
                    },
                    {
                        "name": "kind",
                        "dataType": ["string"],
                        "description": "Symbol kind (function, class, etc.)"
                    },
                    {
                        "name": "file",
                        "dataType": ["string"],
                        "description": "File path"
                    },
                    {
                        "name": "line",
                        "dataType": ["int"],
                        "description": "Line number"
                    },
                    {
                        "name": "snippet",
                        "dataType": ["text"],
                        "description": "Code snippet"
                    }
                ]
            }
            
            weaviate_client.schema.create_class(class_definition)
            logger.info("Created Weaviate class: SophiaCodeSymbols")
        else:
            logger.info("Weaviate class SophiaCodeSymbols already exists")

    except Exception as e:
        logger.error(f"Failed to ensure symbols schema exists: {e}")


if weaviate_client:
    weaviate_client.close()  # Ensure Weaviate client is closed properly

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
