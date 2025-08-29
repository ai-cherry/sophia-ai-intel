# Sophia AI Developer Guide

## Overview

This guide provides comprehensive instructions for developers working on the Sophia AI platform, covering setup, architecture, development workflows, and best practices.

## Project Structure

```
sophia-ai-intel/
├── apps/
│   └── sophia-dashboard/     # Next.js frontend dashboard
├── services/                  # Backend microservices
│   ├── mcp-agents/           # Agent orchestration
│   ├── mcp-context/          # Context and memory management
│   ├── mcp-research/         # Research and search services
│   ├── mcp-github/           # GitHub integration
│   ├── mcp-hubspot/          # HubSpot integration
│   ├── mcp-salesforce/       # Salesforce integration
│   ├── mcp-gong/             # Gong integration
│   └── ...
├── libs/                      # Shared libraries
│   ├── llm/                  # LLM integration and routing
│   ├── secrets/              # Secrets management
│   └── config/               # Configuration management
├── docs/                      # Documentation
├── scripts/                   # Utility scripts
├── tests/                     # Test suite
└── infrastructure/           # Infrastructure as Code
```

## Development Environment Setup

### Prerequisites

1. **Docker and Docker Compose**
   - Install Docker Desktop or Docker Engine
   - Verify installation: `docker --version`

2. **Python 3.11+**
   - Install Python 3.11 or higher
   - Verify: `python --version`

3. **Node.js 18+**
   - Install Node.js 18 or higher
   - Verify: `node --version`

4. **GitHub CLI**
   - Install GitHub CLI for secrets management
   - Authenticate: `gh auth login`

### Initial Setup

1. **Clone the repository:**
```bash
git clone https://github.com/ai-cherry/sophia-ai-intel.git
cd sophia-ai-intel
```

2. **Set up Python environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. **Set up Node.js environment:**
```bash
cd apps/sophia-dashboard
npm install
```

4. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Architecture Overview

### Frontend Architecture

The frontend is built with Next.js 13+ using the App Router pattern:

```
apps/sophia-dashboard/
├── src/
│   ├── app/                  # App Router pages
│   │   ├── api/              # API routes
│   │   ├── components/       # React components
│   │   └── lib/              # Client libraries
│   └── components/           # Shared components
├── public/                   # Static assets
└── styles/                   # CSS and styling
```

Key components:
- **Unified Chat Interface**: `page-unified.tsx`
- **WebSocket Client**: `lib/swarm-client.ts`
- **Component Library**: `components/`

### Backend Architecture

Backend services follow a microservice pattern:

```
services/
├── mcp-agents/
│   ├── app_unified.py        # Main service entry point
│   ├── Dockerfile           # Container configuration
│   └── requirements.txt     # Dependencies
├── mcp-context/
│   ├── app.py               # Main context service
│   ├── memory_coordinator.py # Memory management
│   └── ...
└── ...
```

### Core Libraries

#### LLM Library (`libs/llm/`)
- **Base Client**: `base.py` - Abstract base classes
- **Provider Clients**: `openai_client.py`, `anthropic_client.py`
- **Router**: `router.py` - Smart provider selection
- **Cache**: `cache.py` - Response caching

#### Secrets Management (`libs/secrets/`)
- **Manager**: `manager.py` - Multi-backend secrets management
- **Backends**: GitHub Actions, Pulumi ESC, Fly.io, Environment

#### Configuration (`libs/config/`)
- **Config Manager**: `config.py` - Typed configuration objects
- **Environment Integration**: Automatic secrets loading

## Development Workflows

### Frontend Development

1. **Start development server:**
```bash
cd apps/sophia-dashboard
npm run dev
```

2. **Component Development:**
```bash
# Create new component
touch src/components/NewComponent.tsx

# Add to component library
export * from './NewComponent' in src/components/index.ts
```

3. **API Route Development:**
```bash
# Create new API route
mkdir -p src/app/api/new-feature
touch src/app/api/new-feature/route.ts
```

### Backend Service Development

1. **Service Development:**
```bash
# Navigate to service
cd services/mcp-new-service

# Create service files
touch app.py requirements.txt Dockerfile
```

2. **Local Testing:**
```bash
# Run service locally
python app.py

# Test with curl
curl http://localhost:8000/health
```

3. **Docker Testing:**
```bash
# Build and run container
docker build -t sophia-mcp-new-service .
docker run -p 8000:8000 sophia-mcp-new-service
```

### Adding New Features

#### 1. New MCP Service

1. **Create service directory:**
```bash
mkdir -p services/mcp-newservice
cd services/mcp-newservice
```

2. **Create service files:**
```python
# app.py
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

3. **Add dependencies:**
```bash
# requirements.txt
fastapi>=0.68.0
uvicorn>=0.15.0
```

4. **Create Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
```

5. **Add to docker-compose.yml:**
```yaml
mcp-newservice:
  build:
    context: .
    dockerfile: ./services/mcp-newservice/Dockerfile
  ports:
    - "8001:8000"
  environment:
    - ENVIRONMENT=development
```

#### 2. New Frontend Component

1. **Create component:**
```typescript
// src/components/NewFeature.tsx
'use client';

import { useState } from 'react';

interface NewFeatureProps {
  initialData?: any;
}

export default function NewFeature({ initialData }: NewFeatureProps) {
  const [data, setData] = useState(initialData || {});
  
  return (
    <div className="new-feature">
      {/* Component implementation */}
    </div>
  );
}
```

2. **Export component:**
```typescript
// src/components/index.ts
export { default as NewFeature } from './NewFeature';
```

3. **Use in pages:**
```typescript
// src/app/new-page/page.tsx
import { NewFeature } from '@/components';

export default function NewPage() {
  return (
    <div>
      <NewFeature />
    </div>
  );
}
```

## Testing

### Unit Testing

#### Python Services
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_service.py

# Run with coverage
pytest --cov=services tests/
```

#### Frontend Testing
```bash
cd apps/sophia-dashboard

# Run all tests
npm test

# Run specific test
npm test -- src/components/NewComponent.test.tsx

# Run with coverage
npm test -- --coverage
```

### Integration Testing

1. **Service Integration Tests:**
```bash
# Start services
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
./scripts/run-integration-tests.sh
```

2. **End-to-End Tests:**
```bash
# Start full platform
docker-compose up -d

# Run E2E tests
./scripts/run-e2e-tests.sh
```

### Test Structure

```
tests/
├── unit/                     # Unit tests
│   ├── test_agents.py        # Agents service tests
│   ├── test_context.py       # Context service tests
│   └── ...
├── integration/              # Integration tests
│   ├── test_api_endpoints.py # API endpoint tests
│   ├── test_service_mesh.py  # Service communication tests
│   └── ...
├── e2e/                      # End-to-end tests
│   ├── test_chat_workflow.py # Chat interface tests
│   ├── test_agent_swarm.py   # Swarm orchestration tests
│   └── ...
└── fixtures/                 # Test data and utilities
```

## Code Quality and Standards

### Python Standards

1. **Code Style**: PEP 8 compliance
2. **Type Hints**: Required for all functions and classes
3. **Documentation**: Google-style docstrings

```python
def calculate_score(
    context: str,
    query: str,
    model: str = "gpt-4"
) -> float:
    """Calculate relevance score between context and query.
    
    Args:
        context: The context text to evaluate
        query: The query text to match against
        model: The model to use for scoring
        
    Returns:
        float: Relevance score between 0 and 1
        
    Raises:
        ValueError: If context or query is empty
    """
    if not context or not query:
        raise ValueError("Context and query cannot be empty")
    
    # Implementation here
    return score
```

### TypeScript Standards

1. **Code Style**: ESLint with strict rules
2. **Type Safety**: Strict TypeScript with no implicit any
3. **Component Patterns**: React hooks and functional components

```typescript
interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
  onRetry?: () => void;
}

export default function ChatMessage({
  message,
  isStreaming = false,
  onRetry
}: ChatMessageProps) {
  // Component implementation
}
```

### Security Standards

1. **Secret Management**: Never hardcode secrets
2. **Input Validation**: Validate all external inputs
3. **Authentication**: JWT-based with proper scope checking
4. **Rate Limiting**: Implement rate limiting for external APIs

## Debugging and Monitoring

### Local Debugging

1. **Service Logs:**
```bash
# View service logs
docker-compose logs mcp-agents

# Follow logs in real-time
docker-compose logs -f mcp-context
```

2. **Debugging Python Services:**
```bash
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use debugger
import pdb; pdb.set_trace()
```

3. **Debugging Frontend:**
```typescript
// Add console logs
console.log('Debug info:', data);

// Use React DevTools
// Install React Developer Tools browser extension
```

### Performance Monitoring

1. **Metrics Collection:**
```python
# Add custom metrics
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('requests_total', 'Total requests')
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    REQUEST_COUNT.inc()
    start_time = time.time()
    response = await call_next(request)
    REQUEST_DURATION.observe(time.time() - start_time)
    return response
```

2. **Profiling:**
```bash
# Profile Python code
python -m cProfile -o profile.out script.py

# Analyze profile
python -m pstats profile.out
```

## Deployment and CI/CD

### Local Development

1. **Start Development Environment:**
```bash
# Start all services
docker-compose -f docker-compose.local.yml up -d

# Start frontend
cd apps/sophia-dashboard && npm run dev
```

2. **Hot Reloading:**
- Python services: Use `--reload` flag with uvicorn
- Frontend: Next.js automatic hot reloading

### Production Deployment

1. **Build and Deploy:**
```bash
# Build production images
docker-compose build

# Deploy to production
./scripts/fly-deploy.sh
```

2. **Environment Configuration:**
- Use environment-specific `.env` files
- Configure secrets through deployment platform
- Set proper resource limits

### CI/CD Pipeline

GitHub Actions workflows handle:
- **Testing**: Unit, integration, and E2E tests
- **Building**: Docker image creation
- **Deployment**: Staging and production deployments
- **Monitoring**: Health checks and rollback triggers

## Troubleshooting

### Common Issues

1. **Service Won't Start:**
```bash
# Check service logs
docker-compose logs <service-name>

# Check dependencies
docker-compose ps

# Restart service
docker-compose restart <service-name>
```

2. **Connection Issues:**
```bash
# Check network connectivity
docker network ls
docker network inspect sophia-network

# Check service health endpoints
curl http://localhost:<port>/health
```

3. **Performance Issues:**
```bash
# Monitor resource usage
docker stats

# Check application logs
docker-compose logs --tail 100 <service-name>
```

### Debugging Checklist

- [ ] Check service logs for errors
- [ ] Verify environment variables
- [ ] Check network connectivity between services
- [ ] Validate API keys and credentials
- [ ] Review resource limits and usage
- [ ] Check database connections
- [ ] Verify file permissions
- [ ] Review recent code changes

## Best Practices

### Code Organization

1. **Separation of Concerns:**
   - Keep business logic separate from presentation
   - Use service layers for complex operations
   - Implement proper error handling

2. **Configuration Management:**
   - Use environment variables for configuration
   - Implement graceful degradation
   - Document all configuration options

3. **Error Handling:**
   - Implement comprehensive error handling
   - Use structured logging
   - Provide meaningful error messages

### Performance Optimization

1. **Caching:**
   - Implement Redis caching for frequent operations
   - Use appropriate cache expiration times
   - Monitor cache hit rates

2. **Database Optimization:**
   - Use connection pooling
   - Implement proper indexing
   - Optimize queries

3. **API Optimization:**
   - Implement pagination for large datasets
   - Use efficient data serialization
   - Minimize network requests

### Security Best Practices

1. **Input Validation:**
   - Validate all user inputs
   - Sanitize data before processing
   - Implement rate limiting

2. **Authentication:**
   - Use JWT for stateless authentication
   - Implement proper session management
   - Regular token rotation

3. **Data Protection:**
   - Encrypt sensitive data at rest
   - Use HTTPS for all communications
   - Implement proper access controls

## Contributing

### Pull Request Process

1. **Fork and Branch:**
```bash
git checkout -b feature/new-feature-name
```

2. **Development:**
   - Write tests for new functionality
   - Follow coding standards
   - Update documentation

3. **Testing:**
   - Run full test suite
   - Verify no regressions
   - Check code quality

4. **Submit PR:**
   - Provide clear description
   - Link related issues
   - Request review from maintainers

### Code Review Guidelines

Reviewers should check:
- [ ] Code quality and standards compliance
- [ ] Test coverage and quality
- [ ] Documentation updates
- [ ] Security considerations
- [ ] Performance implications
- [ ] Backward compatibility

## Support and Resources

### Documentation
- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Secrets Management](docs/SECRETS.md)
- [Architecture Diagrams](docs/ARCHITECTURE.md)

### Community
- GitHub Issues for bug reports
- Discussions for feature requests
- Slack community for real-time help

### Enterprise Support
- SLA-based support contracts
- Dedicated engineering support
- Custom development services
- Training and onboarding
