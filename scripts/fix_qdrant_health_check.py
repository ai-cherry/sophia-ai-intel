#!/usr/bin/env python3
"""
Qdrant Health Check Fix Utility
Tests and fixes Qdrant health check endpoints for Cloud vs self-hosted setups
"""

import os
import sys
import json
import requests
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def detect_qdrant_setup(qdrant_url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Detect if Qdrant is Cloud or self-hosted and determine correct health endpoint"""
    result = {
        "setup_type": "unknown",
        "health_endpoint": "/health",
        "working_endpoints": [],
        "recommendation": ""
    }

    # Check if it's a cloud URL
    if "cloud.qdrant.io" in qdrant_url or "aws.cloud.qdrant.io" in qdrant_url:
        result["setup_type"] = "cloud"
        result["health_endpoint"] = "/healthz"
        result["recommendation"] = "Use /healthz for Qdrant Cloud health checks"
    else:
        result["setup_type"] = "self-hosted"
        result["health_endpoint"] = "/health"
        result["recommendation"] = "Use /health for self-hosted Qdrant"

    # Test the recommended endpoint
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    test_url = f"{qdrant_url.rstrip('/')}{result['health_endpoint']}"
    try:
        response = requests.get(test_url, headers=headers, timeout=10)
        if response.status_code == 200:
            result["working_endpoints"].append(result["health_endpoint"])
    except Exception as e:
        logger.warning(f"Could not test {test_url}: {e}")

    # Also test the alternative endpoint
    alt_endpoint = "/healthz" if result["health_endpoint"] == "/health" else "/health"
    alt_url = f"{qdrant_url.rstrip('/')}{alt_endpoint}"
    try:
        response = requests.get(alt_url, headers=headers, timeout=10)
        if response.status_code == 200:
            result["working_endpoints"].append(alt_endpoint)
    except Exception as e:
        logger.debug(f"Alternative endpoint {alt_url} not working: {e}")

    return result

def update_env_file(env_file_path: str, qdrant_url: str) -> bool:
    """Update .env file to use correct Qdrant endpoint variable"""
    try:
        with open(env_file_path, 'r') as f:
            lines = f.readlines()

        updated_lines = []
        modified = False

        for line in lines:
            if line.startswith('QDRANT_URL='):
                # Add a comment about health endpoint
                if "cloud.qdrant.io" in qdrant_url:
                    updated_lines.append(f"{line.rstrip()}  # Qdrant Cloud - use /healthz endpoint\n")
                else:
                    updated_lines.append(f"{line.rstrip()}  # Self-hosted Qdrant - use /health endpoint\n")
                modified = True
            else:
                updated_lines.append(line)

        if modified:
            with open(env_file_path, 'w') as f:
                f.writelines(updated_lines)
            logger.info(f"Updated {env_file_path} with health endpoint guidance")
            return True

    except Exception as e:
        logger.error(f"Failed to update {env_file_path}: {e}")
        return False

    return False

def main():
    print("🔧 Qdrant Health Check Fix Utility")
    print("=" * 50)

    # Get Qdrant configuration from environment
    qdrant_url = os.getenv("QDRANT_URL") or os.getenv("QDRANT_ENDPOINT")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    if not qdrant_url:
        logger.error("No QDRANT_URL or QDRANT_ENDPOINT found in environment")
        print("❌ Please set QDRANT_URL or QDRANT_ENDPOINT environment variable")
        return 1

    print(f"📋 Current Configuration:")
    print(f"  QDRANT_URL: {qdrant_url}")
    print(f"  QDRANT_API_KEY: {'Present' if qdrant_api_key else 'Missing'}")
    print()

    # Detect setup and recommend correct endpoint
    print("🔍 Detecting Qdrant setup...")
    detection = detect_qdrant_setup(qdrant_url, qdrant_api_key)

    print(f"✅ Setup Type: {detection['setup_type']}")
    print(f"✅ Recommended Health Endpoint: {detection['health_endpoint']}")
    print(f"✅ Working Endpoints: {', '.join(detection['working_endpoints']) if detection['working_endpoints'] else 'None found'}")
    print(f"📝 Recommendation: {detection['recommendation']}")
    print()

    # Check if .env file exists and update it
    env_files = [".env", ".env.production", ".env.staging"]
    updated_env = False

    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"🔄 Updating {env_file}...")
            if update_env_file(env_file, qdrant_url):
                updated_env = True
                print(f"✅ Updated {env_file} with health endpoint guidance")
            else:
                print(f"⚠️  Could not update {env_file}")

    if not updated_env:
        print("ℹ️  No .env files found to update")

    print()
    print("🎯 Next Steps:")
    print("1. Update any health check scripts to use the correct endpoint")
    print("2. Update monitoring configurations to use the correct endpoint")
    print("3. Test the health endpoint manually:")
    if qdrant_api_key:
        print(f"   curl -H 'Authorization: Bearer {qdrant_api_key[:20]}...' {qdrant_url.rstrip('/')}{detection['health_endpoint']}")
    else:
        print(f"   curl {qdrant_url.rstrip('/')}{detection['health_endpoint']}")
    print()

    if detection["working_endpoints"]:
        print("✅ Health check endpoint is working correctly!")
        return 0
    else:
        print("❌ Health check endpoint is not responding")
        print("   Please verify your QDRANT_API_KEY and network connectivity")
        return 1

if __name__ == "__main__":
    sys.exit(main())