#!/usr/bin/env python3
"""
Standardized server entry point for MCP Context Service

This module provides a consistent server startup interface for the MCP Context service,
following best practices for production deployment with Uvicorn.

Usage:
    Development:
        python server.py
    
    Production:
        gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8081
    
    Docker:
        CMD ["python", "server.py"]
"""

import os
import sys
import uvicorn
from app import app

# Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8081"))
RELOAD = os.getenv("RELOAD", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").lower()
WORKERS = int(os.getenv("WORKERS", "1"))

def main():
    """Main entry point for the server"""
    
    # Ensure we're in the correct directory
    if not os.path.exists("app.py"):
        print("Error: app.py not found. Please run from the service directory.")
        sys.exit(1)
    
    print(f"🚀 Starting MCP Context Service")
    print(f"   Host: {HOST}")
    print(f"   Port: {PORT}")
    print(f"   Workers: {WORKERS}")
    print(f"   Log Level: {LOG_LEVEL}")
    print(f"   Auto-reload: {RELOAD}")
    print(f"   Health check: http://{HOST}:{PORT}/healthz")
    
    # Run the server
    if WORKERS > 1 and not RELOAD:
        # Multi-worker mode (production)
        uvicorn.run(
            "app:app",
            host=HOST,
            port=PORT,
            log_level=LOG_LEVEL,
            workers=WORKERS,
            access_log=True
        )
    else:
        # Single worker mode (development)
        uvicorn.run(
            app,
            host=HOST,
            port=PORT,
            log_level=LOG_LEVEL,
            reload=RELOAD,
            access_log=True
        )

if __name__ == "__main__":
    main()