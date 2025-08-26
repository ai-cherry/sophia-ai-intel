#!/usr/bin/env python3
"""
Simplified Load Test Runner for Sophia AI
Executes acceptance and performance tests under realistic load conditions
"""

import asyncio
import json
import time
import logging
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LoadTestRunner:
    """Simplified load test runner"""

    def __init__(self):
        self.results_dir = Path("scripts/load_testing/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.test_results = {}

    def run_baseline_test(self):
        """Run baseline performance test"""
        logger.info("Running baseline performance test...")

        cmd = [
            "locust",
            "-f", "scripts/load_testing/locustfile.py",
            "--host", "http://localhost:8000",
            "--users", "20",
            "--spawn-rate", "5",
            "--run-time", "60",
            "--headless",
            "--csv", str(self.results_dir / "baseline_test")
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            self.test_results["baseline"] = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
            logger.info("Baseline test completed")
        except subprocess.TimeoutExpired:
            logger.error("Baseline test timed out")
            self.test_results["baseline"] = {"success": False, "error": "Timeout"}
        except Exception as e:
            logger.error(f"Baseline test failed: {e}")
            self.test_results["baseline"] = {"success": False, "error": str(e)}

    def run_hpa_test(self):
        """Run HPA validation test"""
        logger.info("Running HPA validation test...")

        cmd = [
            "locust",
            "-f", "scripts/load_testing/locustfile.py",
            "--host", "http://localhost:8000",
            "--users", "100",
            "--spawn-rate", "20",
            "--run-time", "300",
            "--headless",
            "--csv", str(self.results_dir / "hpa_test")
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=400)
            self.test_results["hpa_validation"] = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
                "timestamp": datetime.now().isoformat()
            }

            # Check HPA status
            self.test_results["hpa_status"] = self._check_hpa_status()
            logger.info("HPA validation test completed")
        except subprocess.TimeoutExpired:
            logger.error("HPA test timed out")
            self.test_results["hpa_validation"] = {"success": False, "error": "Timeout"}
        except Exception as e:
            logger.error(f"HPA test failed: {e}")
            self.test_results["hpa_validation"] = {"success": False, "error": str(e)}

    def run_stability_test(self):
        """Run system stability test"""
        logger.info("Running system stability test (10 minutes)...")

        cmd = [
            "locust",
            "-f", "scripts/load_testing/locustfile.py",
            "--host", "http://localhost:8000",
            "--users", "200",
            "--spawn-rate", "30",
            "--run-time", "600",
            "--headless",
            "--csv", str(self.results_dir / "stability_test")
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=700)
            self.test_results["stability"] = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
            logger.info("Stability test completed")
        except subprocess.TimeoutExpired:
            logger.error("Stability test timed out")
            self.test_results["stability"] = {"success": False, "error": "Timeout"}
        except Exception as e:
            logger.error(f"Stability test failed: {e}")
            self.test_results["stability"] = {"success": False, "error": str(e)}

    def _check_hpa_status(self):
        """Check HPA status"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "hpa", "-o", "json"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {"error": result.stderr}
        except Exception as e:
            return {"error": str(e)}

    def check_endpoints(self):
        """Check service endpoint accessibility"""
        logger.info("Checking service endpoints...")

        endpoints = [
            "http://localhost:8000/health",
            "http://localhost:8000/",
        ]

        endpoint_results = {}
        for endpoint in endpoints:
            try:
                result = subprocess.run(
                    ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", endpoint],
                    capture_output=True, text=True, timeout=10
                )
                endpoint_results[endpoint] = {
                    "status_code": result.stdout.strip(),
                    "accessible": result.stdout.strip() in ["200", "301", "302"]
                }
            except Exception as e:
                endpoint_results[endpoint] = {"error": str(e)}

        self.test_results["endpoint_check"] = {
            "results": endpoint_results,
            "timestamp": datetime.now().isoformat()
        }

        logger.info("Endpoint check completed")

    def generate_report(self):
        """Generate test report"""
        report = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "tests_run": list(self.test_results.keys()),
                "overall_success": all(
                    result.get("success", False)
                    for result in self.test_results.values()
                    if isinstance(result, dict) and "success" in result
                )
            },
            "results": self.test_results
        }

        report_path = self.results_dir / "load_test_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Test report saved to {report_path}")
        return report

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("LOAD TESTING SUMMARY")
        print("="*60)

        for test_name, result in self.test_results.items():
            if isinstance(result, dict):
                status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
                print(f"\n{test_name}: {status}")
                if "error" in result:
                    print(f"  Error: {result['error']}")

        print("\n" + "="*60)

def main():
    """Main function"""
    print("🔥 Sophia AI Load Testing Runner")
    print("=" * 40)

    runner = LoadTestRunner()

    try:
        # Check endpoints first
        runner.check_endpoints()

        # Run baseline test
        runner.run_baseline_test()

        # Run HPA validation
        runner.run_hpa_test()

        # Run stability test
        runner.run_stability_test()

        # Generate report
        report = runner.generate_report()
        runner.print_summary()

        print("✅ Load testing completed!")

    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
    except Exception as e:
        logger.error(f"❌ Testing failed: {e}")
        print(f"❌ Testing failed: {e}")

if __name__ == "__main__":
    main()