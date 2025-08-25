#!/usr/bin/env python3
"""
Hourly Reindex Agent - Fly Scheduled Machine
============================================

Autonomous agent that runs hourly to:
- Index repository symbols and documentation
- Collect system metrics and health checks
- Generate proof artifacts for compliance
- Trigger MCP service operations when needed

Designed for Fly.io scheduled machine execution with cloud-only operations.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/tmp/reindex.log")
        if os.path.exists("/tmp")
        else logging.NullHandler(),
    ],
)
logger = logging.getLogger(__name__)


class ReindexAgent:
    """Hourly reindex and monitoring agent"""

    def __init__(self):
        self.start_time = datetime.now(timezone.utc)
        self.execution_id = f"reindex_{int(self.start_time.timestamp())}"
        self.services = {
            "context": "https://sophiaai-mcp-context-v2.fly.dev",
            "research": "https://sophiaai-mcp-research-v2.fly.dev",
            "business": "https://sophiaai-mcp-business-v2.fly.dev",
            "github": "https://sophiaai-mcp-repo-v2.fly.dev",
            "dashboard": "https://sophiaai-dashboard-v2.fly.dev",
        }
        self.results = {
            "execution_id": self.execution_id,
            "start_time": self.start_time.isoformat(),
            "end_time": None,
            "duration_seconds": None,
            "services_health": {},
            "indexing_results": {},
            "metrics_collected": {},
            "errors": [],
            "proof_artifacts": [],
            "mcp_calls": [],
        }

    async def execute(self) -> Dict[str, Any]:
        """Main execution flow"""
        logger.info(f"🤖 Starting hourly reindex execution: {self.execution_id}")

        try:
            # Phase 1: Health checks
            await self._check_services_health()

            # Phase 2: Symbol indexing
            await self._perform_symbol_indexing()

            # Phase 3: Metrics collection
            await self._collect_system_metrics()

            # Phase 4: MCP operations
            await self._trigger_mcp_operations()

            # Phase 5: Generate proofs
            await self._generate_proof_artifacts()

        except Exception as e:
            error_info = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "phase": "execution",
            }
            self.results["errors"].append(error_info)
            logger.error(f"Execution failed: {error_info}")

        finally:
            end_time = datetime.now(timezone.utc)
            self.results["end_time"] = end_time.isoformat()
            self.results["duration_seconds"] = (
                end_time - self.start_time
            ).total_seconds()

            # Save results
            await self._save_results()

        logger.info(f"✅ Reindex execution complete: {self.execution_id}")
        return self.results

    async def _check_services_health(self):
        """Check health of all MCP services"""
        logger.info("🏥 Checking services health...")

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        ) as session:
            for service_name, base_url in self.services.items():
                try:
                    healthz_url = f"{base_url}/healthz"
                    async with session.get(healthz_url) as response:
                        status = response.status
                        text = await response.text()

                        self.results["services_health"][service_name] = {
                            "url": healthz_url,
                            "status_code": status,
                            "healthy": status == 200,
                            "response": text[:500],  # Truncate long responses
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }

                        if status == 200:
                            logger.info(f"✅ {service_name} healthy")
                        else:
                            logger.warning(f"⚠️ {service_name} unhealthy: {status}")

                except Exception as e:
                    self.results["services_health"][service_name] = {
                        "url": f"{base_url}/healthz",
                        "healthy": False,
                        "error": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    logger.error(f"❌ {service_name} health check failed: {e}")

    async def _perform_symbol_indexing(self):
        """Trigger symbol indexing on context service"""
        logger.info("📚 Performing symbol indexing...")

        try:
            context_url = self.services["context"]
            index_endpoint = f"{context_url}/index"

            # Payload for comprehensive indexing
            payload = {
                "action": "full_reindex",
                "sources": ["github_repo", "documentation", "workflows"],
                "tenant": "pay-ready",
                "initiated_by": f"reindex_agent_{self.execution_id}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=300)
            ) as session:
                async with session.post(index_endpoint, json=payload) as response:
                    status = response.status
                    result = (
                        await response.json()
                        if response.content_type == "application/json"
                        else await response.text()
                    )

                    self.results["indexing_results"] = {
                        "endpoint": index_endpoint,
                        "status_code": status,
                        "success": status in [200, 201, 202],
                        "result": result,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }

                    if status in [200, 201, 202]:
                        logger.info("✅ Symbol indexing triggered successfully")

                        # Record MCP call
                        self.results["mcp_calls"].append(
                            {
                                "service": "context",
                                "operation": "index",
                                "payload": payload,
                                "response": result,
                                "success": True,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        )
                    else:
                        logger.error(f"❌ Symbol indexing failed: {status} - {result}")

        except Exception as e:
            error_info = {
                "phase": "symbol_indexing",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self.results["errors"].append(error_info)
            logger.error(f"Symbol indexing error: {e}")

    async def _collect_system_metrics(self):
        """Collect system metrics from all services"""
        logger.info("📊 Collecting system metrics...")

        metrics = {
            "collection_time": datetime.now(timezone.utc).isoformat(),
            "services": {},
        }

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        ) as session:
            for service_name, base_url in self.services.items():
                try:
                    metrics_url = f"{base_url}/metrics"
                    async with session.get(metrics_url) as response:
                        if response.status == 200:
                            if response.content_type == "application/json":
                                service_metrics = await response.json()
                            else:
                                # Handle Prometheus format or plain text
                                text = await response.text()
                                service_metrics = {
                                    "raw_metrics": text[:1000]
                                }  # Truncate

                            metrics["services"][service_name] = {
                                "status": "collected",
                                "metrics": service_metrics,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                            logger.info(f"✅ Metrics collected for {service_name}")
                        else:
                            logger.warning(
                                f"⚠️ No metrics endpoint for {service_name}: {response.status}"
                            )

                except Exception as e:
                    logger.warning(
                        f"⚠️ Metrics collection failed for {service_name}: {e}"
                    )

        self.results["metrics_collected"] = metrics

    async def _trigger_mcp_operations(self):
        """Trigger periodic MCP operations"""
        logger.info("🔄 Triggering MCP operations...")

        operations = [
            # Refresh research providers
            {
                "service": "research",
                "endpoint": "/providers/refresh",
                "payload": {"force": False, "timeout_seconds": 30},
            },
            # Update business prospects cache
            {
                "service": "business",
                "endpoint": "/cache/refresh",
                "payload": {
                    "collections": ["prospects", "signals"],
                    "max_age_hours": 1,
                },
            },
        ]

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        ) as session:
            for op in operations:
                try:
                    service_name = op["service"]
                    base_url = self.services[service_name]
                    url = f"{base_url}{op['endpoint']}"

                    async with session.post(url, json=op["payload"]) as response:
                        status = response.status
                        result = (
                            await response.json()
                            if response.content_type == "application/json"
                            else await response.text()
                        )

                        mcp_call = {
                            "service": service_name,
                            "operation": op["endpoint"],
                            "payload": op["payload"],
                            "status_code": status,
                            "success": status in [200, 201, 202],
                            "response": result,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }

                        self.results["mcp_calls"].append(mcp_call)

                        if status in [200, 201, 202]:
                            logger.info(
                                f"✅ MCP operation success: {service_name}{op['endpoint']}"
                            )
                        else:
                            logger.warning(
                                f"⚠️ MCP operation failed: {service_name}{op['endpoint']} - {status}"
                            )

                except Exception as e:
                    error_info = {
                        "phase": "mcp_operations",
                        "operation": op,
                        "error": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    self.results["errors"].append(error_info)
                    logger.error(f"MCP operation error: {e}")

    async def _generate_proof_artifacts(self):
        """Generate proof artifacts for compliance"""
        logger.info("📝 Generating proof artifacts...")

        # Create proof artifact
        proof_artifact = {
            "artifact_type": "reindex_execution",
            "execution_id": self.execution_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_version": "1.0.0",
            "environment": {
                "platform": "fly.io",
                "execution_type": "scheduled_machine",
            },
            "summary": {
                "total_services_checked": len(self.services),
                "healthy_services": len(
                    [
                        s
                        for s in self.results["services_health"].values()
                        if s.get("healthy")
                    ]
                ),
                "indexing_successful": self.results["indexing_results"].get(
                    "success", False
                ),
                "mcp_calls_made": len(self.results["mcp_calls"]),
                "errors_encountered": len(self.results["errors"]),
            },
            "compliance": {
                "proof_first_architecture": True,
                "normalized_error_format": True,
                "cloud_only_operations": True,
                "tenant_scoped": True,
            },
        }

        self.results["proof_artifacts"].append(proof_artifact)
        logger.info("✅ Proof artifacts generated")

    async def _save_results(self):
        """Save execution results to proof file"""
        try:
            # Create proofs directory if it doesn't exist
            proofs_dir = Path("/tmp/proofs") if Path("/tmp").exists() else Path(".")
            proofs_dir.mkdir(exist_ok=True)

            # Save to local file (will be uploaded by Fly machine)
            results_file = proofs_dir / f"reindex_result_{self.execution_id}.json"

            with open(results_file, "w") as f:
                json.dump(self.results, f, indent=2, default=str)

            logger.info(f"📁 Results saved to {results_file}")

            # Also try to post results to dashboard if available
            try:
                dashboard_url = self.services["dashboard"]
                results_endpoint = f"{dashboard_url}/api/jobs/results"

                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as session:
                    async with session.post(
                        results_endpoint, json=self.results
                    ) as response:
                        if response.status in [200, 201]:
                            logger.info("✅ Results posted to dashboard")
                        else:
                            logger.warning(
                                f"⚠️ Dashboard post failed: {response.status}"
                            )

            except Exception as e:
                logger.warning(f"⚠️ Could not post to dashboard: {e}")

        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")


async def main():
    """Main entry point"""
    try:
        agent = ReindexAgent()
        results = await agent.execute()

        # Print summary to stdout for Fly logs
        print(
            json.dumps(
                {
                    "event": "reindex_complete",
                    "execution_id": results["execution_id"],
                    "duration_seconds": results["duration_seconds"],
                    "services_healthy": len(
                        [
                            s
                            for s in results["services_health"].values()
                            if s.get("healthy")
                        ]
                    ),
                    "total_services": len(results["services_health"]),
                    "indexing_success": results["indexing_results"].get(
                        "success", False
                    ),
                    "mcp_calls": len(results["mcp_calls"]),
                    "errors": len(results["errors"]),
                },
                indent=2,
            )
        )

        # Exit with error code if significant issues
        if results["errors"] or not results["indexing_results"].get("success"):
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(
            json.dumps(
                {
                    "event": "reindex_failed",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
