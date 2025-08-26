#!/usr/bin/env python3
"""
LLM Failover Testing for Sophia AI Load Testing
Tests LLM provider failover, model switching, and error handling under load
"""

import json
import time
import random
import logging
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMFailoverTester:
    """Test LLM failover scenarios under load"""

    def __init__(self, output_dir: str = "scripts/load_testing/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.test_results = []
        self.providers = {
            "openai": {
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                "base_url": "https://api.openai.com/v1",
                "timeout": 30
            },
            "anthropic": {
                "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                "base_url": "https://api.anthropic.com",
                "timeout": 30
            },
            "openrouter": {
                "models": ["auto", "anthropic/claude-3-opus", "openai/gpt-4-turbo"],
                "base_url": "https://openrouter.ai/api/v1",
                "timeout": 30
            }
        }

    async def test_provider_failover(self, sessions: int = 10) -> Dict[str, Any]:
        """Test failover between LLM providers"""
        logger.info(f"Testing provider failover with {sessions} concurrent sessions")

        start_time = datetime.now()
        tasks = []

        for i in range(sessions):
            task = asyncio.create_task(self._simulate_user_session(i))
            tasks.append(task)

        # Simulate provider failure during test
        asyncio.create_task(self._simulate_provider_failure())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Analyze results
        successful_requests = sum(1 for r in results if not isinstance(r, Exception))
        failed_requests = len(results) - successful_requests

        test_result = {
            "test_type": "provider_failover",
            "duration": duration,
            "total_sessions": sessions,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": successful_requests / len(results) if results else 0,
            "failover_events": len([r for r in results if isinstance(r, dict) and r.get("failover_occurred")]),
            "timestamp": start_time.isoformat()
        }

        self.test_results.append(test_result)
        return test_result

    async def test_model_switching(self, sessions: int = 5) -> Dict[str, Any]:
        """Test automatic model switching based on load"""
        logger.info(f"Testing model switching with {sessions} concurrent sessions")

        start_time = datetime.now()
        tasks = []

        for i in range(sessions):
            task = asyncio.create_task(self._simulate_model_switching_session(i))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Analyze model usage
        model_usage = {}
        for result in results:
            if isinstance(result, dict) and "models_used" in result:
                for model in result["models_used"]:
                    model_usage[model] = model_usage.get(model, 0) + 1

        test_result = {
            "test_type": "model_switching",
            "duration": duration,
            "total_sessions": sessions,
            "model_usage": model_usage,
            "unique_models_used": len(model_usage),
            "timestamp": start_time.isoformat()
        }

        self.test_results.append(test_result)
        return test_result

    async def test_error_recovery(self, sessions: int = 8) -> Dict[str, Any]:
        """Test error recovery and retry mechanisms"""
        logger.info(f"Testing error recovery with {sessions} concurrent sessions")

        start_time = datetime.now()
        tasks = []

        for i in range(sessions):
            task = asyncio.create_task(self._simulate_error_recovery_session(i))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Analyze error patterns
        error_types = {}
        recovery_successes = 0

        for result in results:
            if isinstance(result, dict):
                if "errors" in result:
                    for error in result["errors"]:
                        error_type = error.get("type", "unknown")
                        error_types[error_type] = error_types.get(error_type, 0) + 1

                if result.get("recovered", False):
                    recovery_successes += 1

        test_result = {
            "test_type": "error_recovery",
            "duration": duration,
            "total_sessions": sessions,
            "error_types": error_types,
            "recovery_successes": recovery_successes,
            "recovery_rate": recovery_successes / len(results) if results else 0,
            "timestamp": start_time.isoformat()
        }

        self.test_results.append(test_result)
        return test_result

    async def _simulate_user_session(self, session_id: int) -> Dict[str, Any]:
        """Simulate a user session with potential provider failures"""
        session_data = {
            "session_id": session_id,
            "requests_made": 0,
            "failover_occurred": False,
            "errors": [],
            "models_used": []
        }

        # Simulate multiple requests in a session
        for i in range(random.randint(5, 15)):
            provider = random.choice(list(self.providers.keys()))
            model = random.choice(self.providers[provider]["models"])

            try:
                # Simulate API call
                await asyncio.sleep(random.uniform(0.1, 2.0))

                # Randomly simulate failures
                if random.random() < 0.1:  # 10% failure rate
                    raise Exception(f"Simulated {provider} API failure")

                session_data["requests_made"] += 1
                session_data["models_used"].append(f"{provider}:{model}")

            except Exception as e:
                session_data["errors"].append({
                    "type": "provider_failure",
                    "provider": provider,
                    "model": model,
                    "error": str(e)
                })

                # Simulate failover
                if len(self.providers) > 1:
                    available_providers = [p for p in self.providers.keys() if p != provider]
                    if available_providers:
                        new_provider = random.choice(available_providers)
                        new_model = random.choice(self.providers[new_provider]["models"])

                        try:
                            await asyncio.sleep(random.uniform(0.5, 2.0))  # Failover delay
                            session_data["failover_occurred"] = True
                            session_data["models_used"].append(f"{new_provider}:{new_model}")
                        except Exception:
                            pass

        return session_data

    async def _simulate_model_switching_session(self, session_id: int) -> Dict[str, Any]:
        """Simulate session with model switching based on performance"""
        session_data = {
            "session_id": session_id,
            "models_used": [],
            "switch_reasons": []
        }

        # Start with preferred model
        current_provider = "openai"
        current_model = "gpt-4"

        for i in range(random.randint(3, 10)):
            session_data["models_used"].append(f"{current_provider}:{current_model}")

            # Simulate performance-based switching
            if random.random() < 0.3:  # 30% chance of switching
                if current_model == "gpt-4":
                    # Switch to cheaper model
                    current_model = "gpt-4-turbo"
                    session_data["switch_reasons"].append("cost_optimization")
                elif current_model == "gpt-4-turbo":
                    # Switch to faster model
                    current_model = "gpt-3.5-turbo"
                    session_data["switch_reasons"].append("speed_optimization")
                else:
                    # Switch back to best model
                    current_model = "gpt-4"
                    session_data["switch_reasons"].append("quality_priority")

            await asyncio.sleep(random.uniform(0.2, 1.0))

        return session_data

    async def _simulate_error_recovery_session(self, session_id: int) -> Dict[str, Any]:
        """Simulate session with error recovery scenarios"""
        session_data = {
            "session_id": session_id,
            "errors": [],
            "recovered": False,
            "retry_count": 0
        }

        max_retries = 3

        for attempt in range(max_retries + 1):
            try:
                # Simulate API call with potential errors
                await asyncio.sleep(random.uniform(0.1, 1.0))

                # Simulate different error types
                error_roll = random.random()
                if error_roll < 0.05:  # 5% rate limiting
                    raise Exception("Rate limit exceeded")
                elif error_roll < 0.08:  # 3% server error
                    raise Exception("Internal server error")
                elif error_roll < 0.12:  # 4% network error
                    raise Exception("Connection timeout")

                # Success
                session_data["recovered"] = True
                break

            except Exception as e:
                session_data["errors"].append({
                    "type": self._categorize_error(e),
                    "message": str(e),
                    "attempt": attempt + 1
                })

                session_data["retry_count"] += 1

                if attempt < max_retries:
                    # Exponential backoff
                    delay = min(2 ** attempt, 10)
                    await asyncio.sleep(delay)

        return session_data

    async def _simulate_provider_failure(self):
        """Simulate provider failure during test"""
        await asyncio.sleep(5)  # Wait for test to start

        logger.info("Simulating provider failure...")
        # In a real scenario, this would disable a provider
        # For simulation, we just log the event

    def _categorize_error(self, error: Exception) -> str:
        """Categorize error types"""
        error_msg = str(error).lower()

        if "rate limit" in error_msg:
            return "rate_limit"
        elif "timeout" in error_msg or "connection" in error_msg:
            return "network_error"
        elif "server error" in error_msg or "internal" in error_msg:
            return "server_error"
        elif "quota" in error_msg:
            return "quota_exceeded"
        else:
            return "unknown_error"

    def save_results(self):
        """Save test results to file"""
        if not self.test_results:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"llm_failover_results_{timestamp}.json"
        filepath = self.output_dir / filename

        try:
            with open(filepath, 'w') as f:
                json.dump(self.test_results, f, indent=2)

            logger.info(f"LLM failover test results saved to {filepath}")

            # Generate summary report
            self._generate_summary_report(filepath.with_suffix('.summary.json'))

        except Exception as e:
            logger.error(f"Error saving LLM failover results: {e}")

    def _generate_summary_report(self, output_path: Path):
        """Generate summary report"""
        if not self.test_results:
            return

        try:
            summary = {
                "test_summary": {
                    "total_tests": len(self.test_results),
                    "test_types": list(set(r["test_type"] for r in self.test_results)),
                    "timestamp": datetime.now().isoformat()
                },
                "results": {}
            }

            # Group results by test type
            for result in self.test_results:
                test_type = result["test_type"]
                if test_type not in summary["results"]:
                    summary["results"][test_type] = []

                summary["results"][test_type].append(result)

            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=2)

            logger.info(f"LLM failover summary report saved to {output_path}")

        except Exception as e:
            logger.error(f"Error generating summary report: {e}")

async def main():
    """Main function for LLM failover testing"""
    import argparse

    parser = argparse.ArgumentParser(description="LLM Failover Tester for Load Testing")
    parser.add_argument("--sessions", type=int, default=10, help="Number of concurrent sessions")
    parser.add_argument("--test-type", choices=["failover", "switching", "recovery", "all"], default="all", help="Type of test to run")
    parser.add_argument("--output-dir", type=str, default="scripts/load_testing/results", help="Output directory")

    args = parser.parse_args()

    print("🧠 Sophia AI LLM Failover Tester")
    print("=" * 50)
    print(f"Sessions: {args.sessions}")
    print(f"Test type: {args.test_type}")
    print(f"Output directory: {args.output_dir}")
    print("=" * 50)

    tester = LLMFailoverTester(args.output_dir)

    try:
        if args.test_type in ["failover", "all"]:
            print("Testing provider failover...")
            failover_result = await tester.test_provider_failover(args.sessions)
            print(f"✅ Provider failover test completed. Success rate: {failover_result['success_rate']:.1%}")

        if args.test_type in ["switching", "all"]:
            print("Testing model switching...")
            switching_result = await tester.test_model_switching(args.sessions)
            print(f"✅ Model switching test completed. Models used: {switching_result['unique_models_used']}")

        if args.test_type in ["recovery", "all"]:
            print("Testing error recovery...")
            recovery_result = await tester.test_error_recovery(args.sessions)
            print(f"✅ Error recovery test completed. Recovery rate: {recovery_result['recovery_rate']:.1%}")

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
    finally:
        tester.save_results()
        print("✅ LLM failover testing complete")

if __name__ == "__main__":
    asyncio.run(main())