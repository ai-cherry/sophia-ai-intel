"""
Sophia AI Intel - Comprehensive Test Configuration
Shared fixtures and configuration for all tests
"""

import asyncio
import os
import pytest
import asyncpg
import redis.asyncio as redis
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock
import docker
from typing import AsyncGenerator, Dict, Any
import tempfile
import shutil

# Test environment setup
os.environ.update({
    'ENVIRONMENT': 'test',
    'TESTING': '1',
    'LOG_LEVEL': 'WARNING',
    'MOCK_EXTERNAL_APIS': 'true',
})

# ===========================================
# Database Fixtures
# ===========================================

@pytest.fixture(scope="session")
async def postgres_pool():
    """Create PostgreSQL connection pool for tests"""
    pool = await asyncpg.create_pool(
        "postgresql://sophia_test:sophia_test_password_123@localhost:5433/sophia_test",
        min_size=5,
        max_size=20
    )
    yield pool
    await pool.close()

@pytest.fixture
async def postgres_conn(postgres_pool):
    """Get PostgreSQL connection from pool"""
    async with postgres_pool.acquire() as conn:
        # Start transaction for isolation
        async with conn.transaction():
            yield conn
            # Transaction automatically rolled back

@pytest.fixture(scope="session")
async def redis_client():
    """Create Redis client for tests"""
    client = redis.Redis.from_url("redis://localhost:6380/1")
    yield client
    await client.flushdb()  # Clean up test data
    await client.close()

# ===========================================
# Service Fixtures
# ===========================================

@pytest.fixture
def docker_client():
    """Docker client for container management tests"""
    return docker.from_env()

@pytest.fixture
async def mcp_agents_client():
    """HTTP client for MCP Agents service"""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        yield client

@pytest.fixture
async def mcp_context_client():
    """HTTP client for MCP Context service"""
    async with AsyncClient(base_url="http://localhost:8081") as client:
        yield client

@pytest.fixture
async def agno_coordinator_client():
    """HTTP client for Agno Coordinator service"""
    async with AsyncClient(base_url="http://localhost:8080") as client:
        yield client

@pytest.fixture
async def dashboard_client():
    """HTTP client for Sophia Dashboard"""
    async with AsyncClient(base_url="http://localhost:3000") as client:
        yield client

# ===========================================
# Mock Fixtures
# ===========================================

@pytest.fixture
def mock_openai():
    """Mock OpenAI API responses"""
    return AsyncMock(spec=['chat', 'embeddings'])

@pytest.fixture
def mock_anthropic():
    """Mock Anthropic API responses"""
    return AsyncMock(spec=['completions'])

@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    mock.exists.return_value = False
    return mock

@pytest.fixture
def mock_postgres():
    """Mock PostgreSQL connection"""
    mock = AsyncMock()
    mock.fetch.return_value = []
    mock.fetchrow.return_value = None
    mock.execute.return_value = "SELECT 1"
    return mock

# ===========================================
# Test Data Fixtures
# ===========================================

@pytest.fixture
def sample_user_data():
    """Sample user data for tests"""
    return {
        "id": "test-user-123",
        "email": "test@sophia-intel.ai",
        "username": "testuser",
        "full_name": "Test User",
        "role": "user"
    }

@pytest.fixture
def sample_agent_data():
    """Sample agent data for tests"""
    return {
        "id": "test-agent-456",
        "name": "Test Agent",
        "description": "Agent for testing",
        "model": "gpt-4",
        "system_prompt": "You are a test agent",
        "status": "active"
    }

@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for tests"""
    return {
        "id": "test-conv-789",
        "user_id": "test-user-123",
        "agent_id": "test-agent-456",
        "title": "Test Conversation",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
    }

@pytest.fixture
def sample_mcp_request():
    """Sample MCP request data"""
    return {
        "method": "test_method",
        "params": {"key": "value"},
        "context": {"user_id": "test-user-123"}
    }

# ===========================================
# Environment Fixtures
# ===========================================

@pytest.fixture(scope="session")
def test_env():
    """Test environment variables"""
    return {
        'POSTGRES_URL': 'postgresql://sophia_test:sophia_test_password_123@localhost:5433/sophia_test',
        'REDIS_URL': 'redis://localhost:6380/1',
        'QDRANT_URL': 'http://localhost:6334',
        'ENVIRONMENT': 'test',
        'LOG_LEVEL': 'WARNING'
    }

@pytest.fixture
def temp_directory():
    """Temporary directory for file-based tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

# ===========================================
# Health Check Fixtures
# ===========================================

@pytest.fixture
async def service_health_checker():
    """Service health check utility"""
    async def check_service_health(url: str, timeout: int = 5):
        async with AsyncClient(timeout=timeout) as client:
            try:
                response = await client.get(f"{url}/health")
                return response.status_code == 200
            except Exception:
                return False
    return check_service_health

# ===========================================
# Integration Test Fixtures
# ===========================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def full_stack_setup(postgres_conn, redis_client):
    """Setup full stack for integration tests"""
    # Initialize test data
    await postgres_conn.execute("""
        INSERT INTO users (id, email, username, full_name, role) 
        VALUES ($1, $2, $3, $4, $5) ON CONFLICT (id) DO NOTHING
    """, "test-user-123", "test@sophia-intel.ai", "testuser", "Test User", "user")
    
    await redis_client.set("test:session", "active", ex=3600)
    
    yield {
        "postgres": postgres_conn,
        "redis": redis_client
    }
    
    # Cleanup
    await postgres_conn.execute("DELETE FROM users WHERE id = $1", "test-user-123")
    await redis_client.delete("test:session")

# ===========================================
# Performance Test Fixtures
# ===========================================

@pytest.fixture
def performance_metrics():
    """Track performance metrics during tests"""
    metrics = {
        'response_times': [],
        'memory_usage': [],
        'cpu_usage': [],
        'db_queries': []
    }
    return metrics

# ===========================================
# Security Test Fixtures
# ===========================================

@pytest.fixture
def security_scanner():
    """Security scanning utilities"""
    class SecurityScanner:
        def check_sql_injection(self, query: str) -> bool:
            """Check for SQL injection patterns"""
            dangerous_patterns = [
                'DROP TABLE', 'DELETE FROM', 'UPDATE SET',
                '--', '/*', '*/', 'UNION SELECT'
            ]
            return not any(pattern in query.upper() for pattern in dangerous_patterns)
        
        def check_xss(self, content: str) -> bool:
            """Check for XSS patterns"""
            xss_patterns = ['<script>', 'javascript:', 'onload=', 'onclick=']
            return not any(pattern in content.lower() for pattern in xss_patterns)
    
    return SecurityScanner()

# ===========================================
# Teardown and Cleanup
# ===========================================

@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Auto cleanup after each test"""
    yield
    # Cleanup logic here if needed

def pytest_configure(config):
    """Pytest configuration hook"""
    # Create required directories
    os.makedirs('reports', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data/test', exist_ok=True)

def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add markers based on test paths
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Add service-specific markers
        if "mcp" in str(item.fspath):
            item.add_marker(pytest.mark.mcp)
        elif "agents" in str(item.fspath):
            item.add_marker(pytest.mark.agents)
        elif "dashboard" in str(item.fspath):
            item.add_marker(pytest.mark.frontend)

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Create test reports with additional info"""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == "call":
        # Add custom reporting logic here
        pass

# ===========================================
# Async Test Utilities
# ===========================================

class AsyncTestCase:
    """Base class for async test cases"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for async test methods"""
        self.loop = asyncio.get_event_loop()