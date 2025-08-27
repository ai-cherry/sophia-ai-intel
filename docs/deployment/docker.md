# Docker Deployment Guide

## Overview

This guide covers Docker deployment practices for SOPHIA AI microservices using the shared Dockerfile template and best practices.

## Shared Dockerfile Template

All SOPHIA AI services use the shared Dockerfile template located at `ops/docker/python-fastapi.Dockerfile`. This template provides:

- Multi-stage builds for optimized image size
- Non-root user execution for security
- Health checks for service monitoring
- Standardized dependency management

### Template Features

```dockerfile
# Multi-stage build with builder and runtime stages
FROM python:3.11-slim-buster AS builder
FROM python:3.11-slim-buster AS runtime

# Non-root user for security
RUN adduser --system --group appuser
USER appuser

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1
```

### Build Arguments

The shared Dockerfile supports the following build arguments:

- `PYTHON_VERSION`: Python version (default: 3.11-slim)
- `SERVICE_REQUIREMENTS_PATH`: Path to service-specific requirements.txt
- `SERVICE_SOURCE_PATH`: Path to service source code
- `SERVICE_APP_MODULE`: FastAPI app module path (default: app:app)

### Usage Example

```bash
# Build service image
docker build \
  --build-arg SERVICE_REQUIREMENTS_PATH=services/my-service/requirements.txt \
  --build-arg SERVICE_SOURCE_PATH=services/my-service \
  --build-arg SERVICE_APP_MODULE=app.main:app \
  -f ops/docker/python-fastapi.Dockerfile \
  -t sophia/my-service:latest \
  .
```

## Dependency Management

### Shared Base Requirements

All services reference the shared base requirements at `platform/common/base-requirements.txt`:

```txt
aiohttp==3.9.5
asyncpg==0.29.0
fastapi==0.111.0
httpx==0.26.0
pydantic==2.8.2
python-dotenv==1.0.1
redis==5.0.1
uvicorn[standard]==0.30.1
tenacity==8.2.3
pybreaker==1.1.0
```

### Service-Specific Requirements

Each service maintains its own `requirements.txt` that references the base:

```txt
-r ../../platform/common/base-requirements.txt
# Service-specific dependencies
service-specific-package==1.0.0
```

## Security Best Practices

### Non-Root User

All containers run as non-root user `appuser` for enhanced security:

```dockerfile
RUN adduser --system --group appuser && \
    chown -R appuser:appuser /app
USER appuser
```

### Minimal Base Images

Using `python:3.11-slim` reduces attack surface and image size.

### Multi-Stage Builds

Builder stage contains build dependencies, runtime stage only contains runtime dependencies.

## Health Checks

All services must implement a `/health` endpoint that returns HTTP 200 for healthy status.

Example FastAPI health endpoint:

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy"}
```

## Environment Variables

### Required Variables

- `PORT`: Service port (default: 8080)
- `PYTHONUNBUFFERED`: Ensure Python output is not buffered

### Optional Variables

- `REDIS_HOST`: Redis host for rate limiting
- `API_KEYS`: Comma-separated list of valid API keys

## Deployment Commands

### Local Development

```bash
# Build and run locally
docker build -f ops/docker/python-fastapi.Dockerfile -t my-service .
docker run -p 8080:8080 -e PORT=8080 my-service
```

### Production Deployment

```bash
# Build with production optimizations
docker build \
  --build-arg SERVICE_REQUIREMENTS_PATH=services/my-service/requirements.txt \
  --build-arg SERVICE_SOURCE_PATH=services/my-service \
  --no-cache \
  -t my-service:latest \
  .

# Run with security
docker run \
  -p 8080:8080 \
  -e PORT=8080 \
  -e API_KEYS=key1,key2,key3 \
  -e REDIS_HOST=redis-server \
  --user appuser \
  my-service:latest
```

## Monitoring and Logging

### Health Check Configuration

```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: my-service
        image: my-service:latest
        ports:
        - containerPort: 8080
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Logging

Services should log to stdout/stderr for Docker log collection:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure `PORT` environment variable is set correctly
2. **Permission denied**: Container runs as non-root user, ensure proper file permissions
3. **Health check failures**: Verify `/health` endpoint returns HTTP 200
4. **Dependency issues**: Check that base requirements are properly referenced

### Debug Commands

```bash
# Check container logs
docker logs <container_id>

# Execute into running container
docker exec -it <container_id> /bin/bash

# Check health endpoint
curl http://localhost:8080/health
```

## Performance Optimization

### Image Size

- Use multi-stage builds to exclude build dependencies
- Clean apt cache in builder stage
- Use `.dockerignore` to exclude unnecessary files

### Startup Time

- Copy `requirements.txt` first for better layer caching
- Use `--no-cache` only when necessary
- Optimize Python imports and startup code

### Resource Usage

- Set appropriate memory and CPU limits
- Use health checks to restart unhealthy containers
- Monitor resource usage with Docker stats

## Security Considerations

### Image Scanning

```bash
# Scan images for vulnerabilities
docker scan my-service:latest
```

### Secret Management

- Never bake secrets into Docker images
- Use environment variables or secret mounts
- Rotate API keys regularly

### Network Security

- Use internal networks for service-to-service communication
- Expose only necessary ports
- Use TLS for external communications