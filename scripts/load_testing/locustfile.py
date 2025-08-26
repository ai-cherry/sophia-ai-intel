#!/usr/bin/env python3
"""
Sophia AI Intel Load Testing Framework using Locust
Comprehensive load testing for all Sophia AI services and endpoints
"""

import json
import random
import time
from typing import Dict, Any, List, Optional
from locust import HttpUser, task, between, constant, constant_pacing
from locust.exception import StopUser
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SophiaAIUser(HttpUser):
    """Base user class for Sophia AI load testing"""

    # Default wait time between tasks
    wait_time = between(1, 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_token = None
        self.user_id = None
        self.session_data = {}

    def on_start(self):
        """Initialize user session"""
        self.authenticate()

    def authenticate(self):
        """Authenticate user and get token"""
        try:
            auth_payload = {
                "username": f"user_{random.randint(1, 1000)}",
                "password": "test_password",
                "client_id": "load_test_client"
            }

            response = self.client.post("/auth/login",
                                      json=auth_payload,
                                      headers={"Content-Type": "application/json"})

            if response.status_code == 200:
                auth_data = response.json()
                self.auth_token = auth_data.get("access_token")
                self.user_id = auth_data.get("user_id")
                logger.info(f"User {self.user_id} authenticated successfully")
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                raise StopUser(f"Authentication failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise StopUser(f"Authentication error: {e}")

    def get_auth_headers(self) -> Dict[str, str]:
        """Get headers with authentication"""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

class DashboardUser(SophiaAIUser):
    """User simulating dashboard interactions"""

    @task(10)
    def load_dashboard(self):
        """Load main dashboard"""
        with self.client.get("/",
                           headers=self.get_auth_headers(),
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Dashboard load failed: {response.status_code}")

    @task(5)
    def get_ai_state(self):
        """Get current AI state"""
        with self.client.get("/api/ai/state",
                           headers=self.get_auth_headers(),
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"AI state request failed: {response.status_code}")

    @task(3)
    def get_notifications(self):
        """Get user notifications"""
        with self.client.get("/api/notifications",
                           headers=self.get_auth_headers(),
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Notifications request failed: {response.status_code}")

class ResearchUser(SophiaAIUser):
    """User simulating research operations"""

    @task(8)
    def perform_research(self):
        """Perform AI research query"""
        research_queries = [
            "What are the latest trends in AI technology?",
            "Analyze the competitive landscape for our product",
            "Find recent developments in machine learning",
            "Research market opportunities in healthcare AI",
            "Analyze customer feedback patterns"
        ]

        query = random.choice(research_queries)

        payload = {
            "query": query,
            "depth": random.choice(["basic", "intermediate", "comprehensive"]),
            "sources": ["web", "academic", "news"],
            "max_results": random.randint(5, 20)
        }

        with self.client.post("/api/research",
                            json=payload,
                            headers=self.get_auth_headers(),
                            catch_response=True) as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"Research request failed: {response.status_code}")

    @task(4)
    def get_research_history(self):
        """Get research history"""
        with self.client.get("/api/research/history",
                           headers=self.get_auth_headers(),
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Research history request failed: {response.status_code}")

class ContextUser(SophiaAIUser):
    """User simulating context and knowledge operations"""

    @task(6)
    def query_context(self):
        """Query knowledge base"""
        context_queries = [
            "What do we know about customer segment A?",
            "Find information about our product features",
            "Retrieve information about competitors",
            "What are our current business metrics?",
            "Find documentation about API usage"
        ]

        query = random.choice(context_queries)

        payload = {
            "query": query,
            "context_type": random.choice(["customer", "product", "competitor", "internal"]),
            "max_results": random.randint(3, 10)
        }

        with self.client.post("/api/context/search",
                            json=payload,
                            headers=self.get_auth_headers(),
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Context query failed: {response.status_code}")

    @task(3)
    def update_context(self):
        """Update knowledge base"""
        payload = {
            "content": f"Updated information from load test {time.time()}",
            "context_type": "test_data",
            "metadata": {"source": "load_test", "timestamp": time.time()}
        }

        with self.client.post("/api/context/update",
                            json=payload,
                            headers=self.get_auth_headers(),
                            catch_response=True) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Context update failed: {response.status_code}")

class BusinessUser(SophiaAIUser):
    """User simulating business operations"""

    @task(7)
    def hubspot_integration(self):
        """Test HubSpot integration"""
        operations = ["contacts", "deals", "companies", "activities"]

        operation = random.choice(operations)

        with self.client.get(f"/api/business/hubspot/{operation}",
                           headers=self.get_auth_headers(),
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HubSpot {operation} request failed: {response.status_code}")

    @task(4)
    def sales_intelligence(self):
        """Test sales intelligence features"""
        payload = {
            "operation": "analyze_pipeline",
            "filters": {
                "date_range": "last_30_days",
                "deal_size": "all"
            }
        }

        with self.client.post("/api/business/sales/intelligence",
                            json=payload,
                            headers=self.get_auth_headers(),
                            catch_response=True) as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"Sales intelligence request failed: {response.status_code}")

class AgentUser(SophiaAIUser):
    """User simulating agent interactions"""

    @task(9)
    def execute_agent_task(self):
        """Execute agent task"""
        agent_types = ["sales_coach", "client_health", "competitor_analyst", "revenue_forecaster"]

        agent = random.choice(agent_types)

        payload = {
            "agent_type": agent,
            "task": f"Perform {agent} analysis for load testing",
            "parameters": {
                "timeframe": "current_quarter",
                "output_format": "json"
            }
        }

        with self.client.post("/api/agents/execute",
                            json=payload,
                            headers=self.get_auth_headers(),
                            catch_response=True) as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"Agent task execution failed: {response.status_code}")

    @task(2)
    def list_agents(self):
        """List available agents"""
        with self.client.get("/api/agents",
                           headers=self.get_auth_headers(),
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Agent list request failed: {response.status_code}")

class MonitoringUser(SophiaAIUser):
    """User simulating monitoring and health checks"""

    # Run more frequently than other users
    wait_time = constant_pacing(2)

    @task(10)
    def health_check(self):
        """Perform health check"""
        with self.client.get("/health",
                           headers=self.get_auth_headers(),
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(5)
    def metrics_endpoint(self):
        """Access metrics endpoint"""
        with self.client.get("/metrics",
                           headers=self.get_auth_headers(),
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Metrics request failed: {response.status_code}")

class ComprehensiveLoadTestUser(SophiaAIUser):
    """User that performs comprehensive workflow testing"""

    def on_start(self):
        """Initialize comprehensive test user"""
        super().on_start()
        self.workflow_step = 0
        self.test_data = {}

    @task
    def comprehensive_workflow(self):
        """Execute comprehensive end-to-end workflow"""
        workflow_steps = [
            self.step_authenticate,
            self.step_load_dashboard,
            self.step_perform_research,
            self.step_query_context,
            self.step_execute_agent,
            self.step_check_results,
            self.step_logout
        ]

        if self.workflow_step < len(workflow_steps):
            step_func = workflow_steps[self.workflow_step]
            try:
                step_func()
                self.workflow_step += 1
            except Exception as e:
                logger.error(f"Workflow step {self.workflow_step} failed: {e}")
                self.workflow_step = 0  # Reset workflow on failure
        else:
            self.workflow_step = 0  # Reset workflow when complete

    def step_authenticate(self):
        """Step 1: Authentication"""
        if not self.auth_token:
            self.authenticate()

    def step_load_dashboard(self):
        """Step 2: Load dashboard"""
        with self.client.get("/",
                           headers=self.get_auth_headers(),
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.test_data["dashboard_loaded"] = True
            else:
                response.failure(f"Dashboard load failed: {response.status_code}")

    def step_perform_research(self):
        """Step 3: Perform research"""
        payload = {
            "query": "Load test research query",
            "depth": "basic",
            "max_results": 5
        }

        with self.client.post("/api/research",
                            json=payload,
                            headers=self.get_auth_headers(),
                            catch_response=True) as response:
            if response.status_code in [200, 202]:
                response.success()
                self.test_data["research_id"] = response.json().get("research_id")
            else:
                response.failure(f"Research request failed: {response.status_code}")

    def step_query_context(self):
        """Step 4: Query context"""
        payload = {
            "query": "Load test context query",
            "max_results": 3
        }

        with self.client.post("/api/context/search",
                            json=payload,
                            headers=self.get_auth_headers(),
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Context query failed: {response.status_code}")

    def step_execute_agent(self):
        """Step 5: Execute agent"""
        payload = {
            "agent_type": "sales_coach",
            "task": "Load test agent task",
            "parameters": {"test": True}
        }

        with self.client.post("/api/agents/execute",
                            json=payload,
                            headers=self.get_auth_headers(),
                            catch_response=True) as response:
            if response.status_code in [200, 202]:
                response.success()
                self.test_data["agent_task_id"] = response.json().get("task_id")
            else:
                response.failure(f"Agent task execution failed: {response.status_code}")

    def step_check_results(self):
        """Step 6: Check results"""
        if "research_id" in self.test_data:
            research_id = self.test_data["research_id"]
            with self.client.get(f"/api/research/{research_id}",
                               headers=self.get_auth_headers(),
                               catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Research results check failed: {response.status_code}")

    def step_logout(self):
        """Step 7: Logout"""
        with self.client.post("/auth/logout",
                            headers=self.get_auth_headers(),
                            catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                self.auth_token = None
                self.user_id = None
            else:
                response.failure(f"Logout failed: {response.status_code}")

# Load test configuration
if __name__ == "__main__":
    # This allows running the file directly for testing
    print("Sophia AI Load Testing Framework")
    print("Run with: locust -f scripts/load_testing/locustfile.py")
    print("\nAvailable user types:")
    print("- DashboardUser: Dashboard interactions")
    print("- ResearchUser: Research operations")
    print("- ContextUser: Knowledge base operations")
    print("- BusinessUser: Business integrations")
    print("- AgentUser: Agent interactions")
    print("- MonitoringUser: Health and monitoring")
    print("- ComprehensiveLoadTestUser: End-to-end workflows")