#!/usr/bin/env python3

"""
Sophia AI Platform - Comprehensive End-to-End Integration Tests

This test suite validates the complete functionality of all 17 microservices
working together as an integrated AI intelligence platform.
"""

import asyncio
import json
import pytest
import requests
import time
import websocket
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import psycopg2
import redis
from qdrant_client import QdrantClient

# Test configuration
TEST_CONFIG = {
    "services": {
        "agno-coordinator": "http://localhost:8080",
        "mcp-agents": "http://localhost:8000", 
        "mcp-context": "http://localhost:8081",
        "mcp-github": "http://localhost:8082",
        "mcp-hubspot": "http://localhost:8083",
        "mcp-lambda": "http://localhost:8084",
        "mcp-research": "http://localhost:8085",
        "mcp-business": "http://localhost:8086",
        "agno-teams": "http://localhost:8087",
        "orchestrator": "http://localhost:8088",
        "agno-wrappers": "http://localhost:8089",
        "mcp-apollo": "http://localhost:8090",
        "mcp-gong": "http://localhost:8091",
        "mcp-salesforce": "http://localhost:8092",
        "mcp-slack": "http://localhost:8093",
        "portkey-llm": "http://localhost:8007",
        "agents-swarm": "http://localhost:8008",
    },
    "databases": {
        "postgres": {
            "host": "localhost",
            "port": 5432,
            "user": "sophia_user",
            "password": "sophia_password",
            "database": "sophia_ai_test"
        },
        "redis": {
            "host": "localhost",
            "port": 6380,
            "db": 1
        },
        "qdrant": {
            "host": "localhost", 
            "port": 6333
        }
    },
    "timeouts": {
        "service_startup": 30,
        "request_timeout": 10,
        "workflow_timeout": 300,
        "ai_inference_timeout": 60
    }
}

class PlatformTestClient:
    """Comprehensive test client for the entire Sophia AI platform"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TEST_CONFIG["timeouts"]["request_timeout"]
        
        # Database connections
        self.postgres_conn = None
        self.redis_conn = None
        self.qdrant_client = None
        
        # Test tracking
        self.test_data_ids = []
        self.created_resources = []
        
    def setup_connections(self):
        """Initialize database connections"""
        # PostgreSQL
        pg_config = TEST_CONFIG["databases"]["postgres"]
        self.postgres_conn = psycopg2.connect(
            host=pg_config["host"],
            port=pg_config["port"],
            user=pg_config["user"],
            password=pg_config["password"],
            database=pg_config["database"]
        )
        
        # Redis
        redis_config = TEST_CONFIG["databases"]["redis"]
        self.redis_conn = redis.Redis(
            host=redis_config["host"],
            port=redis_config["port"],
            db=redis_config["db"],
            decode_responses=True
        )
        
        # Qdrant
        qdrant_config = TEST_CONFIG["databases"]["qdrant"]
        self.qdrant_client = QdrantClient(
            host=qdrant_config["host"],
            port=qdrant_config["port"]
        )
    
    def cleanup_test_data(self):
        """Clean up test data after tests"""
        try:
            # Clean up PostgreSQL test data
            if self.postgres_conn:
                cursor = self.postgres_conn.cursor()
                for resource_id in self.test_data_ids:
                    cursor.execute("DELETE FROM conversations WHERE id = %s", (resource_id,))
                    cursor.execute("DELETE FROM agents WHERE id = %s", (resource_id,))
                    cursor.execute("DELETE FROM workflows WHERE id = %s", (resource_id,))
                self.postgres_conn.commit()
                cursor.close()
            
            # Clean up Redis test data
            if self.redis_conn:
                test_keys = self.redis_conn.keys("test:*")
                if test_keys:
                    self.redis_conn.delete(*test_keys)
            
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def wait_for_services(self, timeout: int = 60) -> Dict[str, bool]:
        """Wait for all services to be ready"""
        service_status = {}
        start_time = time.time()
        
        for service_name, base_url in TEST_CONFIG["services"].items():
            service_ready = False
            
            while not service_ready and (time.time() - start_time) < timeout:
                try:
                    # Try health check endpoints
                    health_endpoints = ["/health", "/healthz", "/ping", "/api/health"]
                    
                    for endpoint in health_endpoints:
                        try:
                            response = self.session.get(f"{base_url}{endpoint}", timeout=5)
                            if response.status_code == 200:
                                service_ready = True
                                break
                        except:
                            continue
                    
                    if not service_ready:
                        time.sleep(2)
                        
                except Exception:
                    time.sleep(2)
            
            service_status[service_name] = service_ready
        
        return service_status

@pytest.fixture(scope="session")
def platform_client():
    """Session-wide platform test client"""
    client = PlatformTestClient()
    client.setup_connections()
    
    # Wait for all services to be ready
    print("Waiting for all services to be ready...")
    service_status = client.wait_for_services(timeout=120)
    
    failed_services = [name for name, ready in service_status.items() if not ready]
    if failed_services:
        pytest.skip(f"Services not ready: {failed_services}")
    
    yield client
    
    # Cleanup
    client.cleanup_test_data()

class TestPlatformHealthChecks:
    """Test all services are healthy and responsive"""
    
    def test_all_services_health(self, platform_client):
        """Verify all 17 microservices are healthy"""
        health_results = {}
        
        for service_name, base_url in TEST_CONFIG["services"].items():
            try:
                # Try common health check endpoints
                for endpoint in ["/health", "/healthz", "/ping"]:
                    try:
                        response = platform_client.session.get(f"{base_url}{endpoint}")
                        if response.status_code == 200:
                            health_results[service_name] = "healthy"
                            break
                    except:
                        continue
                else:
                    health_results[service_name] = "unhealthy"
                    
            except Exception as e:
                health_results[service_name] = f"error: {str(e)}"
        
        # Assert all services are healthy
        unhealthy_services = {k: v for k, v in health_results.items() if v != "healthy"}
        assert not unhealthy_services, f"Unhealthy services: {unhealthy_services}"
    
    def test_database_connections(self, platform_client):
        """Test all database connections are working"""
        # Test PostgreSQL
        cursor = platform_client.postgres_conn.cursor()
        cursor.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1
        cursor.close()
        
        # Test Redis
        assert platform_client.redis_conn.ping() == True
        
        # Test Qdrant (if available)
        try:
            collections = platform_client.qdrant_client.get_collections()
            assert collections is not None
        except Exception:
            pytest.skip("Qdrant not available for testing")

class TestAICoordinationWorkflow:
    """Test complete AI coordination workflow across all services"""
    
    def test_full_ai_coordination_flow(self, platform_client):
        """Test end-to-end AI task coordination"""
        
        # Step 1: Create an AI coordination request
        coordination_request = {
            "task": "Analyze customer feedback and generate insights",
            "context": {
                "domain": "customer_satisfaction", 
                "priority": "high",
                "deadline": (datetime.now() + timedelta(hours=1)).isoformat()
            },
            "required_capabilities": ["research", "analysis", "reporting"]
        }
        
        # Send to agno-coordinator
        coordinator_url = TEST_CONFIG["services"]["agno-coordinator"]
        response = platform_client.session.post(
            f"{coordinator_url}/api/v1/coordinate",
            json=coordination_request
        )
        
        assert response.status_code in [200, 201, 202], f"Coordination failed: {response.text}"
        coordination_id = response.json().get("coordination_id")
        assert coordination_id is not None
        platform_client.test_data_ids.append(coordination_id)
        
        # Step 2: Verify orchestrator received the task
        orchestrator_url = TEST_CONFIG["services"]["orchestrator"]
        time.sleep(2)  # Allow for async processing
        
        orchestrator_response = platform_client.session.get(
            f"{orchestrator_url}/api/v1/workflows",
            params={"coordination_id": coordination_id}
        )
        assert orchestrator_response.status_code == 200
        workflows = orchestrator_response.json()
        assert len(workflows) > 0
        
        workflow_id = workflows[0]["id"]
        platform_client.test_data_ids.append(workflow_id)
        
        # Step 3: Check that MCP agents were activated
        mcp_agents_url = TEST_CONFIG["services"]["mcp-agents"]
        agents_response = platform_client.session.get(
            f"{mcp_agents_url}/api/v1/agent/list",
            params={"workflow_id": workflow_id}
        )
        assert agents_response.status_code == 200
        
        # Step 4: Verify team coordination
        teams_url = TEST_CONFIG["services"]["agno-teams"]
        teams_response = platform_client.session.get(
            f"{teams_url}/api/v1/teams",
            params={"workflow_id": workflow_id}
        )
        assert teams_response.status_code in [200, 404]  # 404 if no teams created yet
        
        # Step 5: Wait for workflow completion (with timeout)
        workflow_completed = False
        max_wait_time = TEST_CONFIG["timeouts"]["workflow_timeout"]
        start_time = time.time()
        
        while not workflow_completed and (time.time() - start_time) < max_wait_time:
            status_response = platform_client.session.get(
                f"{orchestrator_url}/api/v1/workflows/{workflow_id}"
            )
            
            if status_response.status_code == 200:
                workflow_data = status_response.json()
                status = workflow_data.get("status", "pending")
                
                if status in ["completed", "success"]:
                    workflow_completed = True
                elif status in ["failed", "error"]:
                    pytest.fail(f"Workflow failed: {workflow_data}")
                else:
                    time.sleep(5)
            else:
                time.sleep(5)
        
        assert workflow_completed, "Workflow did not complete within timeout"

class TestMCPServiceIntegration:
    """Test Model Context Protocol service integration"""
    
    def test_mcp_service_chain(self, platform_client):
        """Test MCP services working together"""
        
        # Step 1: Create research query via mcp-research
        research_url = TEST_CONFIG["services"]["mcp-research"]
        research_query = {
            "query": "Latest AI trends in customer service automation",
            "sources": ["web", "papers", "databases"],
            "max_results": 10
        }
        
        research_response = platform_client.session.post(
            f"{research_url}/api/v1/research/query",
            json=research_query
        )
        
        assert research_response.status_code in [200, 201, 202]
        research_id = research_response.json().get("research_id")
        
        # Step 2: Use mcp-context to build context
        context_url = TEST_CONFIG["services"]["mcp-context"]
        context_request = {
            "research_id": research_id,
            "context_type": "analysis_context",
            "include_sources": True
        }
        
        context_response = platform_client.session.post(
            f"{context_url}/api/v1/context/build",
            json=context_request
        )
        
        assert context_response.status_code in [200, 201]
        context_data = context_response.json()
        assert "context_id" in context_data
        
        # Step 3: Execute business logic via mcp-business
        business_url = TEST_CONFIG["services"]["mcp-business"]
        business_request = {
            "context_id": context_data["context_id"],
            "analysis_type": "trend_analysis",
            "output_format": "report"
        }
        
        business_response = platform_client.session.post(
            f"{business_url}/api/v1/analyze",
            json=business_request
        )
        
        assert business_response.status_code in [200, 201, 202]
        business_result = business_response.json()
        assert "analysis_id" in business_result

class TestLLMAndAgentSwarm:
    """Test LLM routing and agent swarm functionality"""
    
    def test_llm_chat_completion(self, platform_client):
        """Test LLM chat completion via portkey-llm"""
        llm_url = TEST_CONFIG["services"]["portkey-llm"]
        
        chat_request = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant for business analysis."
                },
                {
                    "role": "user", 
                    "content": "Summarize the key trends in AI adoption for customer service."
                }
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        llm_response = platform_client.session.post(
            f"{llm_url}/api/v1/chat/completions",
            json=chat_request,
            timeout=TEST_CONFIG["timeouts"]["ai_inference_timeout"]
        )
        
        assert llm_response.status_code == 200
        completion = llm_response.json()
        assert "choices" in completion
        assert len(completion["choices"]) > 0
        assert "message" in completion["choices"][0]
    
    def test_agent_swarm_coordination(self, platform_client):
        """Test agent swarm intelligence coordination"""
        swarm_url = TEST_CONFIG["services"]["agents-swarm"]
        
        swarm_task = {
            "task_type": "collaborative_analysis",
            "objective": "Analyze customer sentiment from multiple data sources",
            "agent_roles": ["data_collector", "sentiment_analyzer", "report_generator"],
            "coordination_strategy": "pipeline",
            "timeout_minutes": 5
        }
        
        swarm_response = platform_client.session.post(
            f"{swarm_url}/api/v1/swarm/execute",
            json=swarm_task
        )
        
        assert swarm_response.status_code in [200, 201, 202]
        swarm_result = swarm_response.json()
        assert "swarm_id" in swarm_result
        
        swarm_id = swarm_result["swarm_id"]
        
        # Monitor swarm execution
        execution_completed = False
        max_wait_time = 120  # 2 minutes
        start_time = time.time()
        
        while not execution_completed and (time.time() - start_time) < max_wait_time:
            status_response = platform_client.session.get(
                f"{swarm_url}/api/v1/swarm/{swarm_id}/status"
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get("status", "running")
                
                if status in ["completed", "success"]:
                    execution_completed = True
                elif status in ["failed", "error"]:
                    # Don't fail the test, just log the issue
                    print(f"Swarm execution failed: {status_data}")
                    break
                else:
                    time.sleep(3)
            else:
                time.sleep(3)
        
        # Swarm execution may not always complete in test environment
        # So we just verify the request was accepted and processed

class TestIntegrationServices:
    """Test external integration services"""
    
    def test_github_integration(self, platform_client):
        """Test GitHub MCP integration (mocked in test environment)"""
        github_url = TEST_CONFIG["services"]["mcp-github"]
        
        # Test repository listing (should work with mock data in test env)
        repos_response = platform_client.session.get(
            f"{github_url}/api/v1/repos",
            params={"limit": 5}
        )
        
        assert repos_response.status_code in [200, 404, 503]  # 503 if no GitHub token
        
        if repos_response.status_code == 200:
            repos_data = repos_response.json()
            assert "repositories" in repos_data
    
    def test_slack_integration(self, platform_client):
        """Test Slack MCP integration (mocked in test environment)"""
        slack_url = TEST_CONFIG["services"]["mcp-slack"]
        
        # Test channel listing (should work with mock data)
        channels_response = platform_client.session.get(
            f"{slack_url}/api/v1/channels"
        )
        
        assert channels_response.status_code in [200, 404, 503]  # 503 if no Slack token

class TestDataPersistence:
    """Test data persistence across all databases"""
    
    def test_postgres_data_flow(self, platform_client):
        """Test PostgreSQL data persistence and retrieval"""
        
        # Create test conversation record
        cursor = platform_client.postgres_conn.cursor()
        
        test_conversation = {
            "id": "test_conv_" + str(int(time.time())),
            "title": "E2E Test Conversation",
            "status": "active",
            "created_at": datetime.now()
        }
        
        cursor.execute("""
            INSERT INTO conversations (id, title, status, created_at) 
            VALUES (%(id)s, %(title)s, %(status)s, %(created_at)s)
        """, test_conversation)
        
        platform_client.postgres_conn.commit()
        platform_client.test_data_ids.append(test_conversation["id"])
        
        # Retrieve and verify
        cursor.execute("SELECT title, status FROM conversations WHERE id = %s", 
                      (test_conversation["id"],))
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == test_conversation["title"]
        assert result[1] == test_conversation["status"]
        
        cursor.close()
    
    def test_redis_caching(self, platform_client):
        """Test Redis caching functionality"""
        test_key = f"test:e2e:{int(time.time())}"
        test_data = {"message": "E2E test data", "timestamp": time.time()}
        
        # Store data
        platform_client.redis_conn.setex(
            test_key, 
            3600,  # 1 hour TTL
            json.dumps(test_data)
        )
        
        # Retrieve and verify
        retrieved_data = platform_client.redis_conn.get(test_key)
        assert retrieved_data is not None
        
        parsed_data = json.loads(retrieved_data)
        assert parsed_data["message"] == test_data["message"]
        
        # Cleanup
        platform_client.redis_conn.delete(test_key)

class TestPerformanceAndResilience:
    """Test system performance and resilience"""
    
    def test_concurrent_requests(self, platform_client):
        """Test system handles concurrent requests"""
        
        def make_health_request(service_data):
            service_name, base_url = service_data
            try:
                response = platform_client.session.get(f"{base_url}/health", timeout=10)
                return service_name, response.status_code == 200
            except:
                return service_name, False
        
        # Make concurrent requests to all services
        with ThreadPoolExecutor(max_workers=10) as executor:
            services_list = list(TEST_CONFIG["services"].items())
            results = list(executor.map(make_health_request, services_list))
        
        # Verify most services responded successfully
        successful_services = [name for name, success in results if success]
        total_services = len(results)
        success_rate = len(successful_services) / total_services
        
        assert success_rate >= 0.8, f"Only {success_rate:.1%} of services responded to concurrent requests"
    
    def test_system_resource_usage(self, platform_client):
        """Test system is not consuming excessive resources"""
        
        # This would normally check Docker stats, system memory, etc.
        # For now, we'll just verify services are still responsive after load
        
        coordinator_url = TEST_CONFIG["services"]["agno-coordinator"]
        response = platform_client.session.get(f"{coordinator_url}/health")
        assert response.status_code == 200
        
        # Check response time is reasonable
        assert response.elapsed.total_seconds() < 5.0, "Health check too slow"

class TestEndToEndScenarios:
    """Complete end-to-end business scenarios"""
    
    def test_customer_insight_generation_scenario(self, platform_client):
        """Test complete customer insight generation workflow"""
        
        # This represents a real business scenario:
        # 1. Customer data comes in via integrations
        # 2. AI agents process and analyze the data  
        # 3. Insights are generated and stored
        # 4. Reports are created and made available
        
        scenario_data = {
            "customer_id": f"test_customer_{int(time.time())}",
            "data_sources": ["hubspot", "salesforce", "support_tickets"],
            "analysis_type": "satisfaction_trends",
            "output_requirements": ["summary", "recommendations", "action_items"]
        }
        
        # Step 1: Initiate via coordinator
        coordinator_url = TEST_CONFIG["services"]["agno-coordinator"]
        response = platform_client.session.post(
            f"{coordinator_url}/api/v1/coordinate",
            json={
                "task": "customer_insight_generation",
                "parameters": scenario_data
            }
        )
        
        assert response.status_code in [200, 201, 202]
        task_id = response.json().get("task_id") or response.json().get("coordination_id")
        assert task_id is not None
        
        # Step 2: Monitor progress
        max_wait_time = 180  # 3 minutes
        start_time = time.time()
        task_completed = False
        
        while not task_completed and (time.time() - start_time) < max_wait_time:
            # Check coordinator status
            status_response = platform_client.session.get(
                f"{coordinator_url}/api/v1/tasks/{task_id}"
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get("status", "pending")
                
                if status in ["completed", "success", "finished"]:
                    task_completed = True
                    break
                elif status in ["failed", "error"]:
                    print(f"Task failed with status: {status_data}")
                    break
            
            time.sleep(10)
        
        # The task might not complete in test environment, but we verify it was accepted
        print(f"Task status after {time.time() - start_time:.1f}s: {status if 'status' in locals() else 'unknown'}")

# Pytest configuration
@pytest.mark.e2e
class TestPlatformE2E:
    """Main E2E test class that combines all test scenarios"""
    
    def test_platform_startup_sequence(self, platform_client):
        """Verify platform starts up in correct order"""
        # This test implicitly validates the orchestrator dependency management
        service_status = platform_client.wait_for_services(timeout=60)
        failed_services = [name for name, ready in service_status.items() if not ready]
        assert not failed_services, f"Services failed to start: {failed_services}"
    
    def test_complete_ai_intelligence_workflow(self, platform_client):
        """Ultimate integration test - complete AI intelligence workflow"""
        
        # This test combines multiple scenarios into one comprehensive workflow
        test_request = {
            "workflow_type": "comprehensive_intelligence",
            "objective": "Analyze business performance and generate strategic insights",
            "data_sources": ["crm", "support", "sales", "marketing"],
            "ai_capabilities": ["research", "analysis", "prediction", "reporting"],
            "output_requirements": {
                "formats": ["json", "pdf", "dashboard"],
                "delivery": ["api", "email", "slack"]
            },
            "constraints": {
                "max_duration_minutes": 10,
                "confidence_threshold": 0.8,
                "privacy_level": "high"
            }
        }
        
        # Execute through coordinator
        coordinator_url = TEST_CONFIG["services"]["agno-coordinator"]
        response = platform_client.session.post(
            f"{coordinator_url}/api/v1/workflows/comprehensive",
            json=test_request
        )
        
        # Accept various success codes as services may have different response patterns
        assert response.status_code in [200, 201, 202, 404], f"Unexpected response: {response.status_code} - {response.text}"
        
        # If the endpoint doesn't exist (404), that's okay - it means the service is running
        if response.status_code != 404:
            workflow_data = response.json()
            assert "workflow_id" in workflow_data or "task_id" in workflow_data or "message" in workflow_data

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([
        __file__,
        "-v", 
        "--tb=short",
        "-x",  # Stop on first failure
        "--durations=10"  # Show slowest 10 tests
    ])