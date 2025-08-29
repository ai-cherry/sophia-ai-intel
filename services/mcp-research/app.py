#!/usr/bin/env python3
"""
MCP Research Service - Multi-Provider Research Integration
=========================================================

Production-ready research service that integrates multiple search providers
and provides aggregated, deduplicated, summarized results.

Key Features:
- Multi-provider search (DuckDuckGo, GitHub, Documentation, Academic)
- Result aggregation and deduplication
- LLM-powered summarization
- Redis caching for performance
- Comprehensive error handling

Providers:
- Web Search: DuckDuckGo instant answers
- Code Search: GitHub repositories
- Documentation: Official docs sites
- Academic: ArXiv papers

Version: 2.0.0
Author: Sophia AI Intelligence Team
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from real_search import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8085))
    uvicorn.run(app, host="0.0.0.0", port=port)
