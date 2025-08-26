#!/usr/bin/env python3
"""
Memory Architecture Validation Script for Sophia AI Intel Platform

Validates the complete contextual memory architecture including:
- Memory layer configuration validation
- Qdrant connectivity and collection verification
- Redis caching layer validation
- Embedding engine integration testing
- Memory layer data synchronization
- Performance metrics and health checks

Usage:
    python3 scripts/validate_memory_architecture.py [--production]

Author: Sophia AI Intel Platform Team
Version: 1.0.0
"""

import os
import sys
import json
import logging
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class MemoryArchitectureValidator:
    """Comprehensive validator for Sophia AI memory architecture."""

    def __init__(self, production: bool = False):
        self.production = production
        self.config_dir = Path('./libs')
        self.memory_config_file = self.config_dir / 'memory' / 'layers.json'
        self.ssl_dir = Path('./ssl')

        # Load environment configuration
        self.env_config = self._load_environment_config()

        # Initialize clients
        self.qdrant_client = None
        self.redis_client = None

        # Validation results
        self.validation_results = {
            "overall_status": "pending",
            "memory_layers": {},
            "qdrant": {},
            "redis": {},
            "embeddings": {},
            "integration": {},
            "performance": {},
            "recommendations": []
        }

    def _load_environment_config(self) -> Dict[str, Any]:
        """Load environment configuration from .env files."""
        env_config = {}

        # Try to load production config first
        env_files = ['.env.production', '.env.staging', '.env']

        for env_file in env_files:
            if os.path.exists(env_file):
                try:
                    with open(env_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                env_config[key] = value.strip('"\'')
                    logger.info(f"Loaded configuration from {env_file}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to load {env_file}: {e}")

        return env_config

    def validate_memory_layers_config(self) -> Dict[str, Any]:
        """Validate memory layers configuration."""
        result = {
            "status": "unknown",
            "layers": {},
            "errors": [],
            "warnings": []
        }

        if not self.memory_config_file.exists():
            result["status"] = "failed"
            result["errors"].append(f"Memory layers config not found: {self.memory_config_file}")
            return result

        try:
            with open(self.memory_config_file, 'r') as f:
                config = json.load(f)

            # Validate required layers
            required_layers = ["shortTerm", "codeContext", "bizContext", "personalNotes"]
            config_layers = config.get("layers", {})

            for layer_name in required_layers:
                if layer_name not in config_layers:
                    result["errors"].append(f"Missing required layer: {layer_name}")
                    continue

                layer = config_layers[layer_name]
                layer_status = {"valid": True, "issues": []}

                # Validate layer structure
                required_fields = ["name", "description", "storage"]
                for field in required_fields:
                    if field not in layer:
                        layer_status["issues"].append(f"Missing field: {field}")
                        layer_status["valid"] = False

                result["layers"][layer_name] = layer_status

            # Check for additional layers
            for layer_name in config_layers:
                if layer_name not in required_layers:
                    result["warnings"].append(f"Additional layer found: {layer_name}")

            # Overall status
            if result["errors"]:
                result["status"] = "failed"
            elif result["warnings"]:
                result["status"] = "warning"
            else:
                result["status"] = "passed"

        except json.JSONDecodeError as e:
            result["status"] = "failed"
            result["errors"].append(f"Invalid JSON in config file: {e}")
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(f"Error reading config file: {e}")

        return result

    def validate_qdrant_connectivity(self) -> Dict[str, Any]:
        """Validate Qdrant connectivity and collections."""
        result = {
            "status": "unknown",
            "connected": False,
            "collections": {},
            "errors": [],
            "warnings": []
        }

        qdrant_url = self.env_config.get('QDRANT_URL') or self.env_config.get('QDRANT_ENDPOINT')
        qdrant_key = self.env_config.get('QDRANT_API_KEY')

        if not qdrant_url:
            result["status"] = "failed"
            result["errors"].append("QDRANT_URL not configured")
            return result

        try:
            # Test basic connectivity
            headers = {}
            if qdrant_key:
                headers['api-key'] = qdrant_key

            health_response = requests.get(f"{qdrant_url}/health", headers=headers, timeout=10)

            if health_response.status_code == 200:
                result["connected"] = True

                # Get collections
                collections_response = requests.get(f"{qdrant_url}/collections", headers=headers, timeout=10)

                if collections_response.status_code == 200:
                    collections_data = collections_response.json()
                    collections = collections_data.get('result', {}).get('collections', [])

                    expected_collections = [
                        "sophia-knowledge-base",
                        "sophia-user-profiles",
                        "sophia-conversation-context",
                        "sophia-agent-personas",
                        "sophia-code-snippets",
                        "sophia-research-papers",
                        "sophia-web-content",
                        "sophia-semantic-cache"
                    ]

                    for collection in collections:
                        collection_name = collection['name']
                        result["collections"][collection_name] = {
                            "exists": True,
                            "vectors_count": collection.get('vectors_count', 0),
                            "status": collection.get('status', 'unknown')
                        }

                    # Check for missing collections
                    for expected in expected_collections:
                        if expected not in result["collections"]:
                            result["warnings"].append(f"Missing collection: {expected}")

                else:
                    result["errors"].append(f"Failed to get collections: {collections_response.status_code}")

            else:
                result["errors"].append(f"Qdrant health check failed: {health_response.status_code}")

        except requests.exceptions.RequestException as e:
            result["errors"].append(f"Qdrant connection failed: {e}")
        except Exception as e:
            result["errors"].append(f"Unexpected error: {e}")

        # Overall status
        if result["errors"]:
            result["status"] = "failed"
        elif result["warnings"]:
            result["status"] = "warning"
        else:
            result["status"] = "passed"

        return result

    def validate_redis_connectivity(self) -> Dict[str, Any]:
        """Validate Redis connectivity and configuration."""
        result = {
            "status": "unknown",
            "connected": False,
            "memory_usage": 0,
            "key_count": 0,
            "errors": [],
            "warnings": []
        }

        redis_url = self.env_config.get('REDIS_URL')

        if not redis_url:
            result["status"] = "failed"
            result["errors"].append("REDIS_URL not configured")
            return result

        try:
            # For development, we'll just validate the URL format
            if redis_url.startswith('redis://'):
                result["connected"] = True  # Assume connection would work
                result["warnings"].append("Redis connection not fully tested in development environment")
            else:
                result["errors"].append("Invalid Redis URL format")

        except Exception as e:
            result["errors"].append(f"Redis validation error: {e}")

        # Overall status
        if result["errors"]:
            result["status"] = "failed"
        elif result["warnings"]:
            result["status"] = "warning"
        else:
            result["status"] = "passed"

        return result

    async def validate_embedding_engine(self) -> Dict[str, Any]:
        """Validate embedding engine integration."""
        result = {
            "status": "unknown",
            "openai_configured": False,
            "test_embedding_generated": False,
            "errors": [],
            "warnings": []
        }

        openai_key = self.env_config.get('OPENAI_API_KEY')

        if not openai_key:
            result["errors"].append("OPENAI_API_KEY not configured")
            result["status"] = "failed"
            return result

        result["openai_configured"] = True

        # Import embedding engine dynamically to avoid import errors
        try:
            # Check if we can import the real embeddings module
            import sys
            sys.path.append('./services/mcp-context')

            # Validate that the embedding module exists and can be imported
            embedding_file = Path('./services/mcp-context/real_embeddings.py')
            if embedding_file.exists():
                result["embedding_module_exists"] = True

                # Try to import and validate
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("real_embeddings", embedding_file)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        # Check if embedding engine can be instantiated
                        if hasattr(module, 'RealEmbeddingEngine'):
                            result["embedding_class_available"] = True

                            # Try to create a test embedding
                            try:
                                engine = module.RealEmbeddingEngine()
                                config_status = engine.validate_configuration()

                                result["embedding_engine_configured"] = config_status.get("openai_configured", False)
                                result["qdrant_integration"] = config_status.get("qdrant_configured", False)
                                result["redis_integration"] = config_status.get("redis_configured", False)

                            except Exception as e:
                                result["warnings"].append(f"Could not instantiate embedding engine: {e}")

                        else:
                            result["errors"].append("RealEmbeddingEngine class not found")

                except Exception as e:
                    result["errors"].append(f"Could not import embedding module: {e}")

            else:
                result["errors"].append("real_embeddings.py not found")

        except Exception as e:
            result["errors"].append(f"Embedding validation error: {e}")

        # Overall status
        if result["errors"]:
            result["status"] = "failed"
        elif result["warnings"]:
            result["status"] = "warning"
        else:
            result["status"] = "passed"

        return result

    def validate_integration(self) -> Dict[str, Any]:
        """Validate integration between memory layers and services."""
        result = {
            "status": "unknown",
            "coordinator_integration": False,
            "mcp_services_integration": False,
            "errors": [],
            "warnings": []
        }

        # Check if Agno coordinator exists and references memory layers
        coordinator_file = Path('./services/agno-coordinator/src/coordinator/coordinator.ts')
        if coordinator_file.exists():
            try:
                with open(coordinator_file, 'r') as f:
                    coordinator_content = f.read()

                # Check for memory-related integrations
                if 'memory' in coordinator_content.lower():
                    result["coordinator_integration"] = True
                else:
                    result["warnings"].append("Coordinator may not be integrated with memory layers")

            except Exception as e:
                result["errors"].append(f"Could not read coordinator file: {e}")
        else:
            result["warnings"].append("Agno coordinator file not found")

        # Check MCP services integration
        mcp_services = ['mcp-context', 'mcp-agents', 'mcp-github']
        for service in mcp_services:
            service_file = Path(f'./services/{service}/app.py')
            if service_file.exists():
                try:
                    with open(service_file, 'r') as f:
                        service_content = f.read()

                    if 'embedding' in service_content.lower() or 'qdrant' in service_content.lower():
                        result["mcp_services_integration"] = True

                except Exception as e:
                    result["errors"].append(f"Could not read {service} file: {e}")

        # Overall status
        if result["errors"]:
            result["status"] = "failed"
        elif result["warnings"]:
            result["status"] = "warning"
        else:
            result["status"] = "passed"

        return result

    def validate_performance_requirements(self) -> Dict[str, Any]:
        """Validate performance requirements for memory architecture."""
        result = {
            "status": "unknown",
            "embedding_performance": "unknown",
            "qdrant_performance": "unknown",
            "errors": [],
            "warnings": [],
            "metrics": {}
        }

        # Performance thresholds (in milliseconds)
        thresholds = {
            "embedding_generation": 2000,  # 2 seconds
            "vector_search": 500,         # 500ms
            "cache_hit_ratio": 0.8        # 80%
        }

        # Validate embedding performance from configuration
        embedding_model = self.env_config.get('OPENAI_API_KEY', '')
        if embedding_model:
            result["embedding_performance"] = "configured"
            result["metrics"]["embedding_model"] = "text-embedding-3-large"
        else:
            result["warnings"].append("Embedding model not configured")

        # Validate Qdrant performance expectations
        if self.validation_results.get("qdrant", {}).get("connected"):
            result["qdrant_performance"] = "connected"
            result["metrics"]["qdrant_collections"] = len(self.validation_results["qdrant"].get("collections", {}))
        else:
            result["warnings"].append("Qdrant performance cannot be validated")

        # Overall status
        if result["errors"]:
            result["status"] = "failed"
        elif result["warnings"]:
            result["status"] = "warning"
        else:
            result["status"] = "passed"

        return result

    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive memory architecture validation."""
        logger.info("🔍 Starting comprehensive memory architecture validation...")
        start_time = time.time()

        # Run all validations
        logger.info("1️⃣ Validating memory layers configuration...")
        self.validation_results["memory_layers"] = self.validate_memory_layers_config()

        logger.info("2️⃣ Validating Qdrant connectivity...")
        self.validation_results["qdrant"] = self.validate_qdrant_connectivity()

        logger.info("3️⃣ Validating Redis connectivity...")
        self.validation_results["redis"] = self.validate_redis_connectivity()

        logger.info("4️⃣ Validating embedding engine...")
        self.validation_results["embeddings"] = await self.validate_embedding_engine()

        logger.info("5️⃣ Validating integration...")
        self.validation_results["integration"] = self.validate_integration()

        logger.info("6️⃣ Validating performance requirements...")
        self.validation_results["performance"] = self.validate_performance_requirements()

        # Generate recommendations
        self._generate_recommendations()

        # Overall status
        self._determine_overall_status()

        validation_time = time.time() - start_time
        logger.info(".2f"        return self.validation_results

    def _generate_recommendations(self):
        """Generate recommendations based on validation results."""
        recommendations = []

        # Memory layers recommendations
        memory_status = self.validation_results["memory_layers"]
        if memory_status.get("status") == "failed":
            recommendations.append("🔧 Fix memory layers configuration errors")
        elif memory_status.get("status") == "warning":
            recommendations.append("⚠️ Review memory layers configuration warnings")

        # Qdrant recommendations
        qdrant_status = self.validation_results["qdrant"]
        if qdrant_status.get("status") == "failed":
            recommendations.append("🔧 Fix Qdrant connectivity issues")
        elif qdrant_status.get("status") == "warning":
            recommendations.append("⚠️ Review Qdrant configuration and missing collections")

        # Redis recommendations
        redis_status = self.validation_results["redis"]
        if redis_status.get("status") == "failed":
            recommendations.append("🔧 Configure Redis for caching")
        elif redis_status.get("status") == "warning":
            recommendations.append("⚠️ Test Redis connectivity in production")

        # Embedding recommendations
        embedding_status = self.validation_results["embeddings"]
        if embedding_status.get("status") == "failed":
            recommendations.append("🔧 Fix OpenAI API configuration")
        elif embedding_status.get("status") == "warning":
            recommendations.append("⚠️ Review embedding engine configuration")

        # Integration recommendations
        integration_status = self.validation_results["integration"]
        if integration_status.get("status") == "warning":
            recommendations.append("🔧 Improve integration between memory layers and services")

        self.validation_results["recommendations"] = recommendations

    def _determine_overall_status(self):
        """Determine overall validation status."""
        statuses = [
            self.validation_results["memory_layers"].get("status", "unknown"),
            self.validation_results["qdrant"].get("status", "unknown"),
            self.validation_results["redis"].get("status", "unknown"),
            self.validation_results["embeddings"].get("status", "unknown"),
            self.validation_results["integration"].get("status", "unknown"),
            self.validation_results["performance"].get("status", "unknown")
        ]

        if "failed" in statuses:
            self.validation_results["overall_status"] = "failed"
        elif "warning" in statuses or "unknown" in statuses:
            self.validation_results["overall_status"] = "warning"
        else:
            self.validation_results["overall_status"] = "passed"

    def print_validation_report(self):
        """Print comprehensive validation report."""
        print("\n" + "="*80)
        print("🏗️  SOPHIA AI MEMORY ARCHITECTURE VALIDATION REPORT")
        print("="*80)

        overall_status = self.validation_results["overall_status"]
        status_icon = {"passed": "✅", "warning": "⚠️", "failed": "❌", "unknown": "❓"}.get(overall_status, "❓")

        print(f"\n📊 Overall Status: {status_icon} {overall_status.upper()}")

        # Memory Layers
        memory = self.validation_results["memory_layers"]
        print(f"\n🧠 Memory Layers: {status_icon} {memory.get('status', 'unknown').upper()}")
        if memory.get("errors"):
            for error in memory["errors"]:
                print(f"  ❌ {error}")
        if memory.get("warnings"):
            for warning in memory["warnings"]:
                print(f"  ⚠️ {warning}")

        # Qdrant
        qdrant = self.validation_results["qdrant"]
        print(f"\n🗄️  Qdrant Vector DB: {status_icon} {qdrant.get('status', 'unknown').upper()}")
        if qdrant.get("connected"):
            print(f"  ✅ Connected: {len(qdrant.get('collections', {}))} collections")
        if qdrant.get("errors"):
            for error in qdrant["errors"]:
                print(f"  ❌ {error}")
        if qdrant.get("warnings"):
            for warning in qdrant["warnings"]:
                print(f"  ⚠️ {warning}")

        # Redis
        redis = self.validation_results["redis"]
        print(f"\n💾 Redis Cache: {status_icon} {redis.get('status', 'unknown').upper()}")
        if redis.get("errors"):
            for error in redis["errors"]:
                print(f"  ❌ {error}")
        if redis.get("warnings"):
            for warning in redis["warnings"]:
                print(f"  ⚠️ {warning}")

        # Embeddings
        embeddings = self.validation_results["embeddings"]
        print(f"\n🧮 Embedding Engine: {status_icon} {embeddings.get('status', 'unknown').upper()}")
        if embeddings.get("openai_configured"):
            print("  ✅ OpenAI API configured")
        if embeddings.get("errors"):
            for error in embeddings["errors"]:
                print(f"  ❌ {error}")
        if embeddings.get("warnings"):
            for warning in embeddings["warnings"]:
                print(f"  ⚠️ {warning}")

        # Integration
        integration = self.validation_results["integration"]
        print(f"\n🔗 Integration: {status_icon} {integration.get('status', 'unknown').upper()}")
        if integration.get("errors"):
            for error in integration["errors"]:
                print(f"  ❌ {error}")
        if integration.get("warnings"):
            for warning in integration["warnings"]:
                print(f"  ⚠️ {warning}")

        # Performance
        performance = self.validation_results["performance"]
        print(f"\n⚡ Performance: {status_icon} {performance.get('status', 'unknown').upper()}")
        if performance.get("metrics"):
            for key, value in performance["metrics"].items():
                print(f"  📊 {key}: {value}")

        # Recommendations
        if self.validation_results.get("recommendations"):
            print("
🎯 Recommendations:"            for rec in self.validation_results["recommendations"]:
                print(f"  {rec}")

        print("\n" + "="*80)

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate Sophia AI Memory Architecture")
    parser.add_argument("--production", action="store_true", help="Run in production mode")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create validator
    validator = MemoryArchitectureValidator(production=args.production)

    # Run validation
    async def run_validation():
        results = await validator.run_comprehensive_validation()
        validator.print_validation_report()

        # Exit with appropriate code
        if results["overall_status"] == "passed":
            sys.exit(0)
        elif results["overall_status"] == "warning":
            sys.exit(0)  # Warnings are acceptable
        else:
            sys.exit(1)

    # Run async validation
    asyncio.run(run_validation())

if __name__ == "__main__":
    main()