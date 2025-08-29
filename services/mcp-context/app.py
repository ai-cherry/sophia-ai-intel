#!/usr/bin/env python3
"""
Sophia AI Context MCP Service - Enhanced LlamaIndex Integration
===============================================================

Production-ready context service that provides semantic search, 
repository indexing, and memory coordination using LlamaIndex and vector databases.

Key Features:
- LlamaIndex integration for advanced semantic search
- Multi-database support (Qdrant, pgvector, Weaviate)
- GitHub webhook integration for real-time indexing
- Memory coordination with ranking and merging
- Comprehensive error handling and logging

Architecture:
- Repository Indexer: Code file processing and embedding
- Symbol Indexer: Code symbol and function analysis
- Advanced Indexer: Multi-database coordination
- Real Embeddings: OpenAI and local model support

Version: 2.0.0
Author: Sophia AI Intelligence Team
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import the enhanced context service
try:
    from enhanced_app import app
    print("✅ Enhanced context service loaded successfully")
except Exception as e:
    print(f"❌ Failed to load enhanced context service: {e}")
    # Fallback to basic app if enhanced fails
    from fastapi import FastAPI
    app = FastAPI(title="Sophia AI Context Service", version="2.0.0")
    
    @app.get("/")
    async def root():
        return {"message": "Sophia AI Context Service - Enhanced version not available"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 Starting Sophia AI Context MCP Service on port {port}")
    print("📋 Available endpoints:")
    print("   GET  /health - Health check")
    print("   POST /search - Semantic search")
    print("   POST /index - Repository indexing")
    print("   GET  /memory - Memory coordination")
    uvicorn.run(app, host="0.0.0.0", port=port)
