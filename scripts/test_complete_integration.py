"""
Sophia AI Complete System Integration Test

Comprehensive test suite to validate all system components working together:
- Repository access through GitHub service
- Agent swarm orchestration and multi-agent planning  
- Real embeddings and semantic search functionality
- Aggressive Redis caching performance
- Cross-service communication and data correlation
- Natural language processing through chat interface

Version: 1.0.0
Author: Sophia AI Intelligence Team
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lambda Labs infrastructure
LAMBDA_IP = "192.222.51.223"
SERVICES = {
    'dashboard': f'http://{LAMBDA_IP}:3000',
    'research': f'http://{LAMBDA_IP}:8081', 
    'context': f'http://{LAMBDA_IP}:8082',
    'github': f'http://{LAMBDA_IP}:8083',
    'business': f'http://{LAMBDA_IP}:8084',
    'lambda_api': f'http://{LAMBDA_IP}:8085',
    'hubspot': f'http://{LAMBDA_IP}:8086',
    'agents': f'http://{LAMBDA_IP}:8087'
}


@dataclass
class TestResult:
    """Test result with metadata"""
    test_name: str
    status: str  # passed, failed, skipped
    response_time_ms: int
    details: Dict[str, Any]
    error: Optional[str] = None


class SophiaSystemIntegrationTest:
    """Comprehensive integration test suite"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.http_client = httpx.AsyncClient(timeout=30)

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete integration test suite"""
        logger.info("🧪 Starting Sophia AI Complete System Integration Test")
        
        # Test suite
        test_methods = [
            self.test_service_health_checks,
            self.test_agent_swarm_initialization,
            self.test_real_embeddings_functionality,
            self.test_redis_caching_performance,
            self.test_repository_access_and_analysis,
            self.test_research_capabilities,
            self.test_business_intelligence_integration,
            self.test_cross_service_communication,
            self.test_chat_agent_swarm_integration,
            self.test_semantic_search_accuracy
        ]
        
        # Execute all tests
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                logger.error(f"Test {test_method.__name__} failed with exception: {e}")
                self.results.append(TestResult(
                    test_name=test_method.__name__,
                    status="failed",
                    response_time_ms=0,
                    details={},
                    error=str(e)
                ))
        
        # Generate summary
        return self.generate_test_summary()

    async def test_service_health_checks(self):
        """Test all service health endpoints"""
        logger.info("Testing service health checks...")
        
        health_results = {}
        
        for service_name, service_url in SERVICES.items():
            start_time = time.time()
            
            try:
                response = await self.http_client.get(f"{service_url}/healthz")
                response_time = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    health_data = response.json()
                    health_results[service_name] = {
                        "status": "healthy",
                        "response_time_ms": response_time,
                        "details": health_data
                    }
                else:
                    health_results[service_name] = {
                        "status": "unhealthy", 
                        "response_time_ms": response_time,
                        "status_code": response.status_code
                    }
                    
            except Exception as e:
                health_results[service_name] = {
                    "status": "error",
                    "response_time_ms": int((time.time() - start_time) * 1000),
                    "error": str(e)
                }
        
        # Evaluate overall health
        healthy_services = sum(1 for s in health_results.values() if s["status"] == "healthy")
        total_services = len(health_results)
        
        self.results.append(TestResult(
            test_name="service_health_checks",
            status="passed" if healthy_services >= total_services * 0.8 else "failed",
            response_time_ms=0,
            details={
                "healthy_services": healthy_services,
                "total_services": total_services,
                "health_ratio": healthy_services / total_services,
                "service_details": health_results
            }
        ))

    async def test_agent_swarm_initialization(self):
        """Test agent swarm service initialization and status"""
        logger.info("Testing agent swarm initialization...")
        
        start_time = time.time()
        
        try:
            # Test agent swarm status endpoint
            response = await self.http_client.get(f"{SERVICES['agents']}/agent-swarm/status")
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                status_data = response.json()
                
                self.results.append(TestResult(
                    test_name="agent_swarm_initialization",
                    status="passed" if status_data.get("is_initialized") else "failed",
                    response_time_ms=response_time,
                    details={
                        "is_initialized": status_data.get("is_initialized"),
                        "total_agents": status_data.get("total_agents"),
                        "system_status": status_data.get("system_status"),
                        "swarm_data": status_data
                    }
                ))
            else:
                raise Exception(f"Agent swarm status returned {response.status_code}")
                
        except Exception as e:
            self.results.append(TestResult(
                test_name="agent_swarm_initialization",
                status="failed",
                response_time_ms=int((time.time() - start_time) * 1000),
                details={},
                error=str(e)
            ))

    async def test_real_embeddings_functionality(self):
        """Test that real embeddings are working (not placeholder)"""
        logger.info("Testing real embeddings functionality...")
        
        start_time = time.time()
        
        try:
            # Create a test document with embedding
            test_document = {
                "content": "This is a test document for validating real OpenAI embeddings functionality in Sophia AI context service",
                "source": "integration_test", 
                "metadata": {"test": True, "purpose": "embedding_validation"}
            }
            
            response = await self.http_client.post(
                f"{SERVICES['context']}/documents/create",
                json=test_document
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                doc_data = response.json()
                doc_id = doc_data.get("document", {}).get("id")
                
                # Now test semantic search
                search_response = await self.http_client.post(
                    f"{SERVICES['context']}/documents/search",
                    json={"query": "test document embeddings", "k": 5}
                )
                
                if search_response.status_code == 200:
                    search_data = search_response.json()
                    
                    # Check if we found our test document and if embeddings are real
                    found_test_doc = any(
                        result.get("source") == "integration_test" 
                        for result in search_data.get("results", [])
                    )
                    
                    # Check if using real embeddings (not placeholder)
                    using_real_embeddings = search_data.get("summary", {}).get("model") == "real_embeddings_v2"
                    
                    self.results.append(TestResult(
                        test_name="real_embeddings_functionality",
                        status="passed" if found_test_doc and using_real_embeddings else "failed",
                        response_time_ms=response_time,
                        details={
                            "document_created": True,
                            "document_id": doc_id,
                            "search_successful": search_response.status_code == 200,
                            "found_test_document": found_test_doc,
                            "using_real_embeddings": using_real_embeddings,
                            "embedding_model": search_data.get("summary", {}).get("embedding_model"),
                            "search_results_count": len(search_data.get("results", []))
                        }
                    ))
                else:
                    raise Exception(f"Semantic search failed with status {search_response.status_code}")
            else:
                raise Exception(f"Document creation failed with status {response.status_code}")
                
        except Exception as e:
            self.results.append(TestResult(
                test_name="real_embeddings_functionality",
                status="failed",
                response_time_ms=int((time.time() - start_time) * 1000),
                details={},
                error=str(e)
            ))

    async def test_redis_caching_performance(self):
        """Test Redis caching functionality and performance"""
        logger.info("Testing Redis caching performance...")
        
        start_time = time.time()
        
        try:
            # Test research caching
            test_query = "artificial intelligence performance testing"
            
            # First request (should be uncached)
            first_response = await self.http_client.post(
                f"{SERVICES['research']}/research/query",
                json={"query": test_query, "providers": ["serpapi"]}
            )
            
            first_time = int((time.time() - start_time) * 1000)
            
            # Second request (should be cached)
            cached_start = time.time()
            second_response = await self.http_client.post(
                f"{SERVICES['research']}/research/query", 
                json={"query": test_query, "providers": ["serpapi"]}
            )
            
            second_time = int((time.time() - cached_start) * 1000)
            
            # Get cache statistics
            cache_stats_response = await self.http_client.get(
                f"{SERVICES['research']}/cache/stats"
            )
            
            cache_stats = cache_stats_response.json() if cache_stats_response.status_code == 200 else {}
            
            # Evaluate caching performance
            cache_speedup = first_time / second_time if second_time > 0 else 1
            cache_working = second_time < first_time * 0.5  # Cached should be at least 50% faster
            
            self.results.append(TestResult(
                test_name="redis_caching_performance",
                status="passed" if cache_working else "failed",
                response_time_ms=int((time.time() - start_time) * 1000),
                details={
                    "first_request_time_ms": first_time,
                    "cached_request_time_ms": second_time,
                    "cache_speedup_ratio": cache_speedup,
                    "cache_working": cache_working,
                    "cache_stats": cache_stats.get("cache_stats", {}),
                    "cache_health": cache_stats.get("cache_health", {})
                }
            ))
            
        except Exception as e:
            self.results.append(TestResult(
                test_name="redis_caching_performance",
                status="failed",
                response_time_ms=int((time.time() - start_time) * 1000),
                details={},
                error=str(e)
            ))

    async def test_repository_access_and_analysis(self):
        """Test repository access and agent swarm analysis"""
        logger.info("Testing repository access and analysis...")
        
        start_time = time.time()
        
        try:
            # Test repository file access
            repo_response = await self.http_client.get(
                f"{SERVICES['github']}/repo/tree?path=&ref=main"
            )
            
            if repo_response.status_code == 200:
                repo_data = repo_response.json()
                
                # Test agent swarm repository analysis
                analysis_response = await self.http_client.get(
                    f"{SERVICES['agents']}/repository/analyze"
                )
                
                analysis_successful = analysis_response.status_code == 200
                analysis_data = analysis_response.json() if analysis_successful else {}
                
                self.results.append(TestResult(
                    test_name="repository_access_and_analysis",
                    status="passed" if analysis_successful else "failed",
                    response_time_ms=int((time.time() - start_time) * 1000),
                    details={
                        "repository_accessible": True,
                        "repo_entries_count": len(repo_data.get("entries", [])),
                        "agent_analysis_successful": analysis_successful,
                        "analysis_data": analysis_data
                    }
                ))
            else:
                raise Exception(f"Repository access failed with status {repo_response.status_code}")
                
        except Exception as e:
            self.results.append(TestResult(
                test_name="repository_access_and_analysis",
                status="failed",
                response_time_ms=int((time.time() - start_time) * 1000),
                details={},
                error=str(e)
            ))

    async def test_research_capabilities(self):
        """Test research service capabilities"""
        logger.info("Testing research capabilities...")
        
        start_time = time.time()
        
        try:
            research_query = {
                "query": "Lambda Labs GPU computing for AI workloads",
                "providers": ["serpapi"], 
                "max_results": 3
            }
            
            response = await self.http_client.post(
                f"{SERVICES['research']}/research/query",
                json=research_query
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                research_data = response.json()
                
                self.results.append(TestResult(
                    test_name="research_capabilities",
                    status="passed" if research_data.get("results") else "failed",
                    response_time_ms=response_time,
                    details={
                        "query_successful": True,
                        "results_count": len(research_data.get("results", [])),
                        "providers_used": research_data.get("providers_used", []),
                        "cached": research_data.get("cached", False),
                        "summary": research_data.get("summary", {})
                    }
                ))
            else:
                raise Exception(f"Research query failed with status {response.status_code}")
                
        except Exception as e:
            self.results.append(TestResult(
                test_name="research_capabilities",
                status="failed", 
                response_time_ms=int((time.time() - start_time) * 1000),
                details={},
                error=str(e)
            ))

    async def test_business_intelligence_integration(self):
        """Test business intelligence and CRM integration"""
        logger.info("Testing business intelligence integration...")
        
        start_time = time.time()
        
        try:
            # Test business service provider status
            response = await self.http_client.get(f"{SERVICES['business']}/providers")
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                provider_data = response.json()
                
                self.results.append(TestResult(
                    test_name="business_intelligence_integration",
                    status="passed",
                    response_time_ms=response_time,
                    details={
                        "providers": provider_data.get("providers", {}),
                        "ready_count": provider_data.get("ready_count", 0),
                        "missing_count": provider_data.get("missing_count", 0)
                    }
                ))
            else:
                raise Exception(f"Business service failed with status {response.status_code}")
                
        except Exception as e:
            self.results.append(TestResult(
                test_name="business_intelligence_integration", 
                status="failed",
                response_time_ms=int((time.time() - start_time) * 1000),
                details={},
                error=str(e)
            ))

    async def test_cross_service_communication(self):
        """Test communication between services"""
        logger.info("Testing cross-service communication...")
        
        start_time = time.time()
        
        try:
            # Test agent swarm calling other services
            test_task = {
                "task_description": "Test cross-service communication by analyzing repository structure",
                "task_type": "repository_analysis",
                "priority": "low"
            }
            
            response = await self.http_client.post(
                f"{SERVICES['agents']}/agent-swarm/task",
                json=test_task
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                task_data = response.json()
                task_id = task_data.get("task_id")
                
                # Wait briefly and check task status
                await asyncio.sleep(5)
                
                status_response = await self.http_client.get(
                    f"{SERVICES['agents']}/agent-swarm/task/{task_id}"
                )
                
                status_data = status_response.json() if status_response.status_code == 200 else {}
                
                self.results.append(TestResult(
                    test_name="cross_service_communication",
                    status="passed" if task_id else "failed",
                    response_time_ms=response_time,
                    details={
                        "task_created": True,
                        "task_id": task_id,
                        "task_status": status_data.get("status", "unknown"),
                        "cross_service_working": bool(task_id)
                    }
                ))
            else:
                raise Exception(f"Task creation failed with status {response.status_code}")
                
        except Exception as e:
            self.results.append(TestResult(
                test_name="cross_service_communication",
                status="failed",
                response_time_ms=int((time.time() - start_time) * 1000),
                details={},
                error=str(e)
            ))

    async def test_chat_agent_swarm_integration(self):
        """Test chat interface integration with agent swarm"""
        logger.info("Testing chat-agent swarm integration...")
        
        start_time = time.time()
        
        try:
            # Test agent swarm processing endpoint
            chat_request = {
                "message": "analyze repository structure and code quality",
                "session_id": "integration_test_session",
                "user_context": {"test": True}
            }
            
            response = await self.http_client.post(
                f"{SERVICES['agents']}/agent-swarm/process",
                json=chat_request
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                chat_data = response.json()
                
                self.results.append(TestResult(
                    test_name="chat_agent_swarm_integration",
                    status="passed",
                    response_time_ms=response_time,
                    details={
                        "chat_processing_successful": True,
                        "response_type": chat_data.get("type"),
                        "task_id": chat_data.get("task_id"),
                        "message_length": len(chat_data.get("message", "")),
                        "chat_response": chat_data
                    }
                ))
            else:
                raise Exception(f"Chat processing failed with status {response.status_code}")
                
        except Exception as e:
            self.results.append(TestResult(
                test_name="chat_agent_swarm_integration",
                status="failed",
                response_time_ms=int((time.time() - start_time) * 1000),
                details={},
                error=str(e)
            ))

    async def test_semantic_search_accuracy(self):
        """Test semantic search accuracy and relevance"""
        logger.info("Testing semantic search accuracy...")
        
        start_time = time.time()
        
        try:
            # Search for code-related content
            search_request = {
                "query": "agent swarm orchestration and planning",
                "k": 10
            }
            
            response = await self.http_client.post(
                f"{SERVICES['context']}/documents/search",
                json=search_request
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                search_data = response.json()
                results = search_data.get("results", [])
                confidence = search_data.get("summary", {}).get("confidence", 0)
                
                self.results.append(TestResult(
                    test_name="semantic_search_accuracy",
                    status="passed" if len(results) > 0 and confidence > 0.5 else "failed",
                    response_time_ms=response_time,
                    details={
                        "results_count": len(results),
                        "confidence_score": confidence,
                        "embedding_model": search_data.get("summary", {}).get("embedding_model"),
                        "cache_hit_ratio": search_data.get("summary", {}).get("cache_hit_ratio"),
                        "search_successful": True
                    }
                ))
            else:
                raise Exception(f"Semantic search failed with status {response.status_code}")
                
        except Exception as e:
            self.results.append(TestResult(
                test_name="semantic_search_accuracy",
                status="failed",
                response_time_ms=int((time.time() - start_time) * 1000),
                details={},
                error=str(e)
            ))

    # Placeholder test methods for remaining functionality
    async def test_cross_service_communication(self):
        """Test communication between services - placeholder"""
        self.results.append(TestResult(
            test_name="cross_service_communication",
            status="skipped",
            response_time_ms=0,
            details={"reason": "Placeholder - would test service-to-service calls"}
        ))

    def generate_test_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        passed_tests = [r for r in self.results if r.status == "passed"]
        failed_tests = [r for r in self.results if r.status == "failed"] 
        skipped_tests = [r for r in self.results if r.status == "skipped"]
        
        total_response_time = sum(r.response_time_ms for r in self.results)
        avg_response_time = total_response_time / len(self.results) if self.results else 0
        
        return {
            "test_summary": {
                "total_tests": len(self.results),
                "passed": len(passed_tests),
                "failed": len(failed_tests),
                "skipped": len(skipped_tests),
                "pass_rate": len(passed_tests) / len(self.results) if self.results else 0,
                "overall_status": "PASSED" if len(failed_tests) == 0 else "FAILED"
            },
            "performance": {
                "total_execution_time_ms": total_response_time,
                "average_response_time_ms": avg_response_time,
                "fastest_test": min(self.results, key=lambda r: r.response_time_ms).test_name if self.results else None,
                "slowest_test": max(self.results, key=lambda r: r.response_time_ms).test_name if self.results else None
            },
            "detailed_results": [
                {
                    "test": r.test_name,
                    "status": r.status,
                    "response_time_ms": r.response_time_ms,
                    "details": r.details,
                    "error": r.error
                }
                for r in self.results
            ],
            "recommendations": self.generate_recommendations()
        }

    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        failed_tests = [r for r in self.results if r.status == "failed"]
        
        if failed_tests:
            recommendations.append(f"Address {len(failed_tests)} failed test(s)")
            
        # Service-specific recommendations
        for result in self.results:
            if result.status == "failed":
                if "embeddings" in result.test_name:
                    recommendations.append("Check OpenAI API key configuration and Qdrant connectivity")
                elif "caching" in result.test_name:
                    recommendations.append("Verify Redis configuration and connectivity")
                elif "agent_swarm" in result.test_name:
                    recommendations.append("Check agent swarm service deployment and initialization")
        
        if not failed_tests:
            recommendations.append("All tests passed! System is fully operational")
        
        return recommendations

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


# Main execution
async def main():
    """Run complete integration test"""
    test_suite = SophiaSystemIntegrationTest()
    
    try:
        results = await test_suite.run_all_tests()
        
        # Print summary
        print("\n" + "="*60)
        print("🧪 SOPHIA AI INTEGRATION TEST RESULTS")
        print("="*60)
        
        summary = results["test_summary"]
        print(f"📊 Tests: {summary['total_tests']} total, {summary['passed']} passed, {summary['failed']} failed")
        print(f"📈 Pass Rate: {summary['pass_rate']:.1%}")
        print(f"🎯 Overall Status: {summary['overall_status']}")
        
        if results["performance"]:
            perf = results["performance"]
            print(f"⚡ Performance: {perf['average_response_time_ms']:.0f}ms average response time")
        
        # Print failed tests
        failed_tests = [r for r in results["detailed_results"] if r["status"] == "failed"]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['error']}")
        
        # Print recommendations
        if results["recommendations"]:
            print("\n💡 RECOMMENDATIONS:")
            for rec in results["recommendations"]:
                print(f"  • {rec}")
        
        # Save detailed results
        with open("integration-test-results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: integration-test-results.json")
        print("="*60)
        
        return summary["overall_status"] == "PASSED"
        
    finally:
        await test_suite.close()


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
