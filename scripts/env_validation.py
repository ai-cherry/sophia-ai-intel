#!/usr/bin/env python3
"""
Comprehensive Environment Variable Validation Script
Validates all 98+ environment variables from .env file
Tests Redis credentials, Qdrant JWT, and service connectivity
"""

import os
import sys
import json
import subprocess
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import redis
import requests
from qdrant_client import QdrantClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnvValidator:
    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self.validation_results = {
            "phase1": {"environment_variables": {}, "redis": {}, "qdrant": {}, "python_dotenv": {}, "nodejs_dotenv": {}},
            "phase2": {"lambda_labs": {}, "qdrant": {}, "redis": {}, "openai": {}, "openrouter": {}, "github": {}, "hubspot": {}, "slack": {}, "dnsimple": {}},
            "summary": {"total_variables": 0, "valid_variables": 0, "invalid_variables": 0, "connectivity_tests": 0, "passed_tests": 0, "failed_tests": 0}
        }

    def load_environment_file(self) -> Dict[str, str]:
        """Load and parse environment file"""
        logger.info(f"Loading environment file: {self.env_file}")

        if not os.path.exists(self.env_file):
            raise FileNotFoundError(f"Environment file not found: {self.env_file}")

        # Load with python-dotenv
        load_dotenv(self.env_file)

        # Parse file manually to count variables
        variables = {}
        with open(self.env_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    variables[key] = value

        logger.info(f"Found {len(variables)} environment variables")
        return variables

    def validate_redis_credentials(self, variables: Dict[str, str]) -> Dict[str, any]:
        """Validate Redis credentials and connectivity"""
        logger.info("Validating Redis credentials")

        redis_config = {
            "REDIS_USERNAME": variables.get("REDIS_USERNAME"),
            "REDIS_PASSWORD": variables.get("REDIS_PASSWORD"),
            "REDIS_HOST": variables.get("REDIS_HOST"),
            "REDIS_PORT": variables.get("REDIS_PORT"),
            "REDIS_URL": variables.get("REDIS_URL")
        }

        results = {
            "credentials_present": all([redis_config["REDIS_USERNAME"], redis_config["REDIS_PASSWORD"]]),
            "expected_username": redis_config["REDIS_USERNAME"] == "scoobyjava",
            "expected_password": redis_config["REDIS_PASSWORD"] == "Huskers1983$",
            "connectivity_test": False,
            "error": None
        }

        if results["credentials_present"] and results["expected_username"] and results["expected_password"]:
            try:
                # Test Redis connection
                r = redis.Redis(
                    host=redis_config["REDIS_HOST"],
                    port=int(redis_config["REDIS_PORT"]),
                    username=redis_config["REDIS_USERNAME"],
                    password=redis_config["REDIS_PASSWORD"],
                    decode_responses=True
                )
                r.ping()
                results["connectivity_test"] = True
                logger.info("Redis connectivity test passed")
            except Exception as e:
                results["error"] = str(e)
                logger.error(f"Redis connectivity test failed: {e}")
        else:
            results["error"] = "Redis credentials not properly configured"

        return results

    def validate_qdrant_config(self, variables: Dict[str, str]) -> Dict[str, any]:
        """Validate Qdrant JWT token and connectivity"""
        logger.info("Validating Qdrant configuration")

        qdrant_config = {
            "QDRANT_URL": variables.get("QDRANT_URL"),
            "QDRANT_API_KEY": variables.get("QDRANT_API_KEY")
        }

        results = {
            "url_present": bool(qdrant_config["QDRANT_URL"]),
            "api_key_present": bool(qdrant_config["QDRANT_API_KEY"]),
            "connectivity_test": False,
            "error": None
        }

        if results["url_present"] and results["api_key_present"]:
            try:
                # Test Qdrant connection
                client = QdrantClient(
                    url=qdrant_config["QDRANT_URL"],
                    api_key=qdrant_config["QDRANT_API_KEY"]
                )
                # Try to list collections
                client.get_collections()
                results["connectivity_test"] = True
                logger.info("Qdrant connectivity test passed")
            except Exception as e:
                results["error"] = str(e)
                logger.error(f"Qdrant connectivity test failed: {e}")
        else:
            results["error"] = "Qdrant configuration incomplete"

        return results

    def test_lambda_labs_connectivity(self, variables: Dict[str, str]) -> Dict[str, any]:
        """Test Lambda Labs API connectivity"""
        logger.info("Testing Lambda Labs API connectivity")

        lambda_config = {
            "LAMBDA_API_KEY": variables.get("LAMBDA_API_KEY"),
            "LAMBDA_CLOUD_ENDPOINT": variables.get("LAMBDA_CLOUD_ENDPOINT", "https://cloud.lambdalabs.com/api/v1")
        }

        results = {
            "api_key_present": bool(lambda_config["LAMBDA_API_KEY"]),
            "endpoint_present": bool(lambda_config["LAMBDA_CLOUD_ENDPOINT"]),
            "connectivity_test": False,
            "error": None
        }

        if results["api_key_present"]:
            try:
                headers = {"Authorization": f"Bearer {lambda_config['LAMBDA_API_KEY']}"}
                response = requests.get(f"{lambda_config['LAMBDA_CLOUD_ENDPOINT']}/instances", headers=headers, timeout=10)
                if response.status_code == 200:
                    results["connectivity_test"] = True
                    logger.info("Lambda Labs API connectivity test passed")
                else:
                    results["error"] = f"HTTP {response.status_code}: {response.text}"
            except Exception as e:
                results["error"] = str(e)
                logger.error(f"Lambda Labs connectivity test failed: {e}")
        else:
            results["error"] = "Lambda Labs API key missing"

        return results

    def test_openai_connectivity(self, variables: Dict[str, str]) -> Dict[str, any]:
        """Test OpenAI API connectivity"""
        logger.info("Testing OpenAI API connectivity")

        openai_key = variables.get("OPENAI_API_KEY")
        results = {
            "api_key_present": bool(openai_key),
            "connectivity_test": False,
            "error": None
        }

        if results["api_key_present"]:
            try:
                headers = {"Authorization": f"Bearer {openai_key}"}
                response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=10)
                if response.status_code == 200:
                    results["connectivity_test"] = True
                    logger.info("OpenAI API connectivity test passed")
                else:
                    results["error"] = f"HTTP {response.status_code}: {response.text}"
            except Exception as e:
                results["error"] = str(e)
                logger.error(f"OpenAI connectivity test failed: {e}")
        else:
            results["error"] = "OpenAI API key missing"

        return results

    def test_openrouter_connectivity(self, variables: Dict[str, str]) -> Dict[str, any]:
        """Test OpenRouter API connectivity"""
        logger.info("Testing OpenRouter API connectivity")

        openrouter_key = variables.get("OPENROUTER_API_KEY")
        results = {
            "api_key_present": bool(openrouter_key),
            "connectivity_test": False,
            "error": None
        }

        if results["api_key_present"]:
            try:
                headers = {"Authorization": f"Bearer {openrouter_key}"}
                response = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=10)
                if response.status_code == 200:
                    results["connectivity_test"] = True
                    logger.info("OpenRouter API connectivity test passed")
                else:
                    results["error"] = f"HTTP {response.status_code}: {response.text}"
            except Exception as e:
                results["error"] = str(e)
                logger.error(f"OpenRouter connectivity test failed: {e}")
        else:
            results["error"] = "OpenRouter API key missing"

        return results

    def run_comprehensive_validation(self) -> Dict[str, any]:
        """Run complete environment validation"""
        logger.info("Starting comprehensive environment validation")

        try:
            # Phase 1: Load and validate environment variables
            variables = self.load_environment_file()

            # Update summary
            self.validation_results["summary"]["total_variables"] = len(variables)

            # Validate Redis credentials
            redis_results = self.validate_redis_credentials(variables)
            self.validation_results["phase1"]["redis"] = redis_results

            # Validate Qdrant configuration
            qdrant_results = self.validate_qdrant_config(variables)
            self.validation_results["phase1"]["qdrant"] = qdrant_results

            # Phase 2: Test external service connectivity
            lambda_results = self.test_lambda_labs_connectivity(variables)
            self.validation_results["phase2"]["lambda_labs"] = lambda_results

            openai_results = self.test_openai_connectivity(variables)
            self.validation_results["phase2"]["openai"] = openai_results

            openrouter_results = self.test_openrouter_connectivity(variables)
            self.validation_results["phase2"]["openrouter"] = openrouter_results

            # Count valid variables and tests
            for var_name, var_value in variables.items():
                if var_value and var_value.strip():
                    self.validation_results["summary"]["valid_variables"] += 1
                else:
                    self.validation_results["summary"]["invalid_variables"] += 1

            # Count connectivity tests
            all_tests = [
                redis_results, qdrant_results, lambda_results,
                openai_results, openrouter_results
            ]

            for test in all_tests:
                if "connectivity_test" in test:
                    self.validation_results["summary"]["connectivity_tests"] += 1
                    if test["connectivity_test"]:
                        self.validation_results["summary"]["passed_tests"] += 1
                    else:
                        self.validation_results["summary"]["failed_tests"] += 1

            logger.info("Comprehensive validation completed")
            return self.validation_results

        except Exception as e:
            logger.error(f"Validation failed with error: {e}")
            self.validation_results["error"] = str(e)
            return self.validation_results

def main():
    """Main execution function"""
    validator = EnvValidator()

    results = validator.run_comprehensive_validation()

    # Save results to file
    with open("env_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("\n" + "="*80)
    print("ENVIRONMENT VALIDATION RESULTS")
    print("="*80)

    summary = results["summary"]
    print(f"Total Variables: {summary['total_variables']}")
    print(f"Valid Variables: {summary['valid_variables']}")
    print(f"Invalid Variables: {summary['invalid_variables']}")
    print(f"Connectivity Tests: {summary['connectivity_tests']}")
    print(f"Passed Tests: {summary['passed_tests']}")
    print(f"Failed Tests: {summary['failed_tests']}")

    if "error" in results:
        print(f"\nError: {results['error']}")

    print(f"\nDetailed results saved to: env_validation_results.json")

    return 0 if summary["failed_tests"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())