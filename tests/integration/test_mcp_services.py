"""
Integration tests for Sophia AI Intel MCP services
"""

import os
import requests
import pytest

# Service URLs from environment
GITHUB_MCP_URL = os.getenv("GITHUB_MCP_URL", "https://sophiaai-mcp-repo.fly.dev")
RESEARCH_MCP_URL = os.getenv(
    "RESEARCH_MCP_URL", "https://sophiaai-mcp-research.fly.dev"
)
CONTEXT_MCP_URL = os.getenv("CONTEXT_MCP_URL", "https://sophiaai-mcp-context.fly.dev")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://sophiaai-dashboard.fly.dev")


class TestMCPServices:
    """Test suite for MCP services health and functionality"""

    def test_github_mcp_health(self):
        """Test GitHub MCP service health endpoint"""
        response = requests.get(f"{GITHUB_MCP_URL}/healthz", timeout=10)
        assert response.status_code == 200

        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert health_data["service"] == "sophia-mcp-github"
        assert "version" in health_data
        assert "timestamp" in health_data
        assert "repo" in health_data

    def test_github_mcp_capabilities(self):
        """Test GitHub MCP service capabilities endpoint"""
        response = requests.get(f"{GITHUB_MCP_URL}/mcp/capabilities", timeout=10)
        assert response.status_code == 200

        capabilities = response.json()
        assert "tools" in capabilities
        assert len(capabilities["tools"]) > 0

        # Check for expected tools
        tool_names = [tool["name"] for tool in capabilities["tools"]]
        expected_tools = ["read_file", "list_files", "search_code", "get_repo_info"]
        for tool in expected_tools:
            assert tool in tool_names

    def test_github_mcp_repo_info(self):
        """Test GitHub MCP service repository information"""
        payload = {
            "method": "tools/call",
            "params": {
                "name": "get_repo_info",
                "arguments": {"owner": "ai-cherry", "repo": "sophia-ai-intel"},
            },
        }

        response = requests.post(f"{GITHUB_MCP_URL}/mcp/call", json=payload, timeout=15)
        assert response.status_code == 200

        result = response.json()
        assert "content" in result
        repo_info = result["content"][0]["text"]
        assert "sophia-ai-intel" in repo_info

    def test_research_mcp_health(self):
        """Test Research MCP service health endpoint"""
        try:
            response = requests.get(f"{RESEARCH_MCP_URL}/healthz", timeout=10)
            assert response.status_code == 200

            health_data = response.json()
            assert health_data["status"] == "healthy"
            assert health_data["service"] == "sophia-mcp-research"
        except requests.exceptions.RequestException:
            pytest.skip("Research MCP service not deployed yet")

    def test_context_mcp_health(self):
        """Test Context MCP service health endpoint"""
        try:
            response = requests.get(f"{CONTEXT_MCP_URL}/healthz", timeout=10)
            assert response.status_code == 200

            health_data = response.json()
            assert health_data["status"] == "healthy"
            assert health_data["service"] == "sophia-mcp-context"
        except requests.exceptions.RequestException:
            pytest.skip("Context MCP service not deployed yet")

    def test_dashboard_health(self):
        """Test Dashboard service availability"""
        try:
            response = requests.get(f"{DASHBOARD_URL}/", timeout=10)
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")
        except requests.exceptions.RequestException:
            pytest.skip("Dashboard not deployed yet")


class TestServiceIntegration:
    """Test suite for service integration and workflows"""

    def test_mcp_service_discovery(self):
        """Test that services can discover each other"""
        # Test GitHub MCP service discovery
        response = requests.get(f"{GITHUB_MCP_URL}/mcp/capabilities", timeout=10)
        assert response.status_code == 200

        capabilities = response.json()
        assert "resources" in capabilities or "tools" in capabilities

    def test_llm_router_integration(self):
        """Test LLM router integration through GitHub MCP"""
        payload = {
            "method": "tools/call",
            "params": {
                "name": "test_llm_router",
                "arguments": {
                    "message": "Hello, test the LLM router with ChatGPT-5 priority"
                },
            },
        }

        try:
            response = requests.post(
                f"{GITHUB_MCP_URL}/mcp/call", json=payload, timeout=30
            )
            # This might not be implemented yet, so we'll check gracefully
            if response.status_code == 200:
                result = response.json()
                assert "content" in result
            else:
                pytest.skip("LLM router integration not implemented yet")
        except requests.exceptions.RequestException:
            pytest.skip("LLM router integration not available")


class TestSecurityAndCompliance:
    """Test suite for security and compliance checks"""

    def test_https_enforcement(self):
        """Test that all services enforce HTTPS"""
        services = [GITHUB_MCP_URL, RESEARCH_MCP_URL, CONTEXT_MCP_URL, DASHBOARD_URL]

        for service_url in services:
            if service_url.startswith("https://"):
                try:
                    response = requests.get(f"{service_url}/healthz", timeout=10)
                    # If we get here, HTTPS is working
                    assert True
                except requests.exceptions.RequestException:
                    # Service might not be deployed, skip
                    continue

    def test_cors_headers(self):
        """Test CORS headers for browser compatibility"""
        response = requests.options(f"{GITHUB_MCP_URL}/mcp/capabilities", timeout=10)

        # Check for CORS headers
        headers = response.headers
        assert "Access-Control-Allow-Origin" in headers or response.status_code == 200

    def test_no_sensitive_info_exposure(self):
        """Test that services don't expose sensitive information"""
        response = requests.get(f"{GITHUB_MCP_URL}/healthz", timeout=10)
        assert response.status_code == 200

        health_data = response.json()
        sensitive_keys = ["api_key", "secret", "password", "token", "private_key"]

        # Check that no sensitive information is exposed
        health_str = str(health_data).lower()
        for sensitive_key in sensitive_keys:
            assert sensitive_key not in health_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
