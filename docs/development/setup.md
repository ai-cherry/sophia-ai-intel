# Development Setup Guide

## Overview

This guide covers setting up a development environment for SOPHIA AI microservices, including local development, testing, and deployment preparation.

## Prerequisites

### System Requirements

- **Python**: 3.11 or later
- **Docker**: 20.10 or later
- **Docker Compose**: 2.0 or later
- **Git**: 2.30 or later
- **Redis**: 6.0 or later (for rate limiting and caching)

### Development Tools

```bash
# Install Python development dependencies
pip install -r platform/common/base-requirements.txt
pip install pytest black flake8 mypy pre-commit

# Install Docker and Docker Compose
# (platform-specific installation required)
```

## Project Structure

```
sophia-ai-intel-1/
├── platform/common/          # Shared libraries and base requirements
│   ├── base-requirements.txt
│   └── security.py
├── services/                 # Individual microservices
│   ├── mcp-context/
│   ├── mcp-github/
│   └── ...
├── ops/docker/              # Shared Docker templates
├── docs/                    # Documentation
└── scripts/                 # Development and deployment scripts
```

## Local Development Setup

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd sophia-ai-intel-1

# Set up Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install base dependencies
pip install -r platform/common/base-requirements.txt
```

### 2. Environment Configuration

Create `.env` file in the project root:

```bash
# .env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/sophia_dev

# Redis (for rate limiting and caching)
REDIS_HOST=localhost
REDIS_PORT=6379

# API Keys (comma-separated for development)
API_KEYS=dev-key-1,dev-key-2,dev-key-3

# Service Ports
PORT=8080

# Environment
ENVIRONMENT=development
PYTHONUNBUFFERED=1
```

### 3. Start Infrastructure Services

```bash
# Start Redis for development
docker run -d -p 6379:6379 redis:7-alpine

# Or use Docker Compose for full stack
docker-compose up -d redis postgres
```

## Service Development

### Creating a New Service

1. **Create service directory structure**:
   ```bash
   mkdir -p services/my-service
   cd services/my-service
   ```

2. **Create requirements.txt**:
   ```txt
   -r ../../platform/common/base-requirements.txt
   # Add service-specific dependencies here
   ```

3. **Create main application**:
   ```python
   # app.py
   from fastapi import FastAPI
   from platform.common.security import create_security_middleware

   app = FastAPI(title="My Service")

   # Add security middleware
   valid_keys = ["dev-key-1", "dev-key-2"]  # Load from env in production
   app.add_middleware(create_security_middleware(valid_keys))

   @app.get("/health")
   async def health_check():
       return {"status": "healthy"}

   @app.get("/")
   async def root():
       return {"message": "My Service"}
   ```

4. **Create Dockerfile** (optional - use shared template):
   ```dockerfile
   # Use shared template
   FROM ops/docker/python-fastapi.Dockerfile
   ```

### Running a Service Locally

```bash
# From service directory
cd services/my-service

# Install dependencies
pip install -r requirements.txt

# Run service
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

### Testing with API Key

```bash
# Test health endpoint
curl http://localhost:8080/health

# Test with API key
curl -H "X-API-Key: dev-key-1" http://localhost:8080/
```

## Docker Development

### Building Service Images

```bash
# Build using shared template
docker build \
  --build-arg SERVICE_REQUIREMENTS_PATH=services/my-service/requirements.txt \
  --build-arg SERVICE_SOURCE_PATH=services/my-service \
  --build-arg SERVICE_APP_MODULE=app:app \
  -f ops/docker/python-fastapi.Dockerfile \
  -t sophia/my-service:dev \
  .
```

### Running with Docker Compose

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  my-service:
    build:
      context: ..
      dockerfile: ops/docker/python-fastapi.Dockerfile
      args:
        SERVICE_REQUIREMENTS_PATH: services/my-service/requirements.txt
        SERVICE_SOURCE_PATH: services/my-service
    ports:
      - "8080:8080"
    environment:
      - API_KEYS=dev-key-1,dev-key-2
      - REDIS_HOST=redis
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## Security Implementation

### Using Security Middleware

```python
from platform.common.security import (
    create_security_middleware,
    require_api_key
)

# Global middleware
app.add_middleware(create_security_middleware(
    valid_api_keys=["key1", "key2"],
    redis_host="localhost",
    rate_limit_requests=100,
    rate_limit_window=60
))

# Per-endpoint protection
@app.get("/protected")
async def protected_endpoint(api_key: str = Depends(require_api_key(["key1", "key2"]))):
    return {"message": "Protected content"}
```

### Rate Limiting

The security middleware automatically implements Redis-based rate limiting:

- **Default**: 100 requests per 60 seconds per IP+API key combination
- **Configuration**: Adjustable via `SecurityConfig`
- **Headers**: Returns rate limit status in response headers

## Testing

### Unit Tests

```python
# tests/test_app.py
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_protected_endpoint():
    # Test without API key
    response = client.get("/protected")
    assert response.status_code == 401

    # Test with valid API key
    response = client.get("/protected", headers={"X-API-Key": "dev-key-1"})
    assert response.status_code == 200
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_app.py
```

## Code Quality

### Linting and Formatting

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

## Debugging

### Local Debugging

```python
# Enable debug mode
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug prints
@app.middleware("http")
async def debug_middleware(request, call_next):
    print(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"Response: {response.status_code}")
    return response
```

### Docker Debugging

```bash
# Run container with bash
docker run -it --entrypoint /bin/bash sophia/my-service:dev

# Check logs
docker logs <container_id>

# Debug with environment variables
docker run -e DEBUG=1 -p 8080:8080 sophia/my-service:dev
```

## Deployment Preparation

### Environment Variables

```bash
# Production environment variables
export API_KEYS=prod-key-1,prod-key-2,prod-key-3
export REDIS_HOST=redis-production-server
export DATABASE_URL=postgresql://prod-user:prod-pass@prod-db:5432/sophia_prod
export ENVIRONMENT=production
```

### Health Checks

Ensure all services implement proper health checks:

```python
@app.get("/health")
async def health_check():
    # Check database connectivity
    # Check Redis connectivity
    # Check external service dependencies
    return {"status": "healthy", "checks": {...}}
```

### Monitoring

```python
# Add monitoring endpoints
@app.get("/metrics")
async def metrics():
    # Return Prometheus metrics
    return generate_metrics()

@app.get("/ready")
async def readiness():
    # Check if service is ready to accept traffic
    return {"status": "ready"}
```

## Troubleshooting

### Common Issues

1. **Import errors**: Check that `PYTHONPATH` includes the service directory
2. **Port conflicts**: Ensure services use different ports in development
3. **Redis connection errors**: Verify Redis is running and accessible
4. **API key errors**: Check that API keys are properly configured

### Getting Help

1. Check the logs: `docker logs <container_id>`
2. Verify environment variables: `docker exec <container_id> env`
3. Test connectivity: `docker exec <container_id> curl localhost:8080/health`
4. Check service dependencies: Ensure all required services are running

## Performance Optimization

### Development Optimizations

```python
# Enable auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8080

# Use development database
DATABASE_URL=postgresql://user:password@localhost:5432/sophia_dev
```

### Production Considerations

- Use production WSGI server (Gunicorn + Uvicorn workers)
- Implement connection pooling
- Add caching layers
- Optimize database queries
- Use async/await patterns

## Contributing

### Development Workflow

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and add tests
3. Run tests: `pytest`
4. Format code: `black .`
5. Create pull request

### Code Review Checklist

- [ ] Tests pass
- [ ] Code is formatted with Black
- [ ] Type hints are added
- [ ] Documentation is updated
- [ ] Security considerations are addressed
- [ ] Performance impact is considered