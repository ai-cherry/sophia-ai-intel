# Sophia AI AGNO Coordinator Service

**Phase 1A: Foundation Implementation**

The AGNO Coordinator Service provides a hybrid orchestration layer that intelligently routes requests between the existing Sophia AI pipeline orchestrator and future AGNO capabilities. This service establishes the foundation for advanced AI orchestration while ensuring zero disruption to current operations.

## Overview

The AGNO Coordinator implements a **hybrid integration approach** that:

- **Preserves existing functionality** - All current Sophia AI capabilities remain unchanged
- **Enables gradual AGNO adoption** - Feature flags control the rollout of new capabilities
- **Provides intelligent routing** - Automatically determines the best handler for each request
- **Ensures high reliability** - Comprehensive health checks and fallback mechanisms

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AGNO Coordinator Service                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Feature Flag System │ Configuration Manager          │  │
│  │  Health Monitoring   │ Request Routing Logic          │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Routing Decision                        │
│  ┌─────────────┬─────────────────┬─────────────────┐       │
│  │ Complexity  │ Confidence      │ Feature Flags   │       │
│  │ Analysis    │ Scoring         │ Evaluation      │       │
│  └─────────────┴─────────────────┴─────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Handler Selection                       │
│  ┌─────────────────────────┬─────────────────────────┐     │
│  │ Existing Orchestrator   │ AGNO Teams (Future)     │     │
│  │ (Current Default)       │ (Phase 2A+)             │     │
│  └─────────────────────────┴─────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### 🔄 Intelligent Request Routing
- **Complexity Analysis**: Evaluates request complexity based on length, constraints, and context
- **Confidence Scoring**: Determines routing confidence using multiple factors
- **Feature Flag Control**: Gradual rollout with environment-based feature toggles

### 🏥 Comprehensive Health Monitoring
- **Multi-level Health Checks**: Service, configuration, and dependency health
- **Detailed Diagnostics**: Comprehensive health reports with actionable recommendations
- **Automatic Recovery**: Circuit breaker patterns and fallback mechanisms

### ⚙️ Flexible Configuration
- **Environment-based Config**: All settings configurable via environment variables
- **Runtime Configuration**: Update settings without service restart
- **Validation**: Comprehensive configuration validation with detailed error reporting

### 📊 Observability & Monitoring
- **Structured Logging**: Consistent logging format with configurable levels
- **Metrics Collection**: Performance and usage metrics for monitoring
- **Request Tracing**: End-to-end request tracking and correlation

## API Endpoints

### Core Endpoints

#### `POST /route`
Route a request through the coordinator.

**Request Body:**
```json
{
  "userPrompt": "Analyze the market trends in enterprise software",
  "sessionId": "session-123",
  "userId": "user-456",
  "context": {
    "conversationHistory": [...],
    "metadata": {...},
    "preferences": {...}
  },
  "constraints": {
    "maxExecutionTime": 30000,
    "maxToolCalls": 5
  }
}
```

**Response:**
```json
{
  "success": true,
  "response": "Analysis completed...",
  "executionId": "exec-123",
  "routingDecision": {
    "source": "existing",
    "confidence": 0.85,
    "reasoning": "Request complexity meets threshold",
    "estimatedComplexity": "medium"
  },
  "executionTimeMs": 1250,
  "source": "existing",
  "metadata": {...}
}
```

#### `GET /healthz`
Basic health check endpoint.

**Response:**
```json
{
  "service": "agno-coordinator",
  "status": "healthy",
  "timestamp": "2025-08-25T23:00:00.000Z",
  "version": "1.0.0"
}
```

#### `GET /health/detailed`
Comprehensive health report.

**Response:**
```json
{
  "status": {
    "service": "agno-coordinator",
    "status": "healthy",
    "timestamp": "2025-08-25T23:00:00.000Z",
    "version": "1.0.0",
    "checks": {...},
    "metrics": {...}
  },
  "checks": [...],
  "recommendations": [...]
}
```

### Management Endpoints

#### `GET /flags`
Get all feature flags.

#### `PUT /flags/:flag`
Update a feature flag.

```json
{
  "enabled": true
}
```

#### `GET /config`
Get current configuration.

#### `GET /stats`
Get service statistics.

## Configuration

### Environment Variables

#### Feature Flags
```bash
ENABLE_AGNO_ROUTING=false          # Enable AGNO routing (Phase 1A: false)
ENABLE_AGNO_LOGGING=true           # Enable detailed logging
ENABLE_AGNO_MONITORING=true        # Enable monitoring
ENABLE_AGNO_FALLBACK=true          # Enable fallback mechanisms
ENABLE_AGNO_CIRCUIT_BREAKER=true   # Enable circuit breaker
ENABLE_AGNO_METRICS=true           # Enable metrics collection
ENABLE_AGNO_HEALTH_CHECKS=true     # Enable health checks
```

#### Routing Configuration
```bash
AGNO_COMPLEXITY_THRESHOLD=10       # Minimum words for complexity analysis
AGNO_CONFIDENCE_THRESHOLD=0.8       # Minimum confidence for AGNO routing
AGNO_FALLBACK_TIMEOUT=30000         # Fallback timeout in milliseconds
AGNO_RETRY_ATTEMPTS=2              # Number of retry attempts
AGNO_METRICS_INTERVAL=60000        # Metrics collection interval
```

#### Service Configuration
```bash
EXISTING_ORCHESTRATOR_URL=http://sophia-orchestrator:3000
REDIS_URL=redis://redis:6379
MAX_RETRIES=3
REQUEST_TIMEOUT=30000
ALLOWED_ORIGINS=http://localhost:3000,http://sophia-dashboard:3000
```

## Deployment

### Docker Compose

```yaml
version: '3.8'
services:
  agno-coordinator:
    build: .
    ports:
      - "3001:3001"
    environment:
      - ENABLE_AGNO_ROUTING=false
      - EXISTING_ORCHESTRATOR_URL=http://sophia-orchestrator:3000
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/healthz"]
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agno-coordinator
spec:
  replicas: 2
  selector:
    matchLabels:
      app: agno-coordinator
  template:
    metadata:
      labels:
        app: agno-coordinator
    spec:
      containers:
      - name: agno-coordinator
        image: sophia/agno-coordinator:latest
        env:
        - name: ENABLE_AGNO_ROUTING
          value: "false"
        ports:
        - containerPort: 3001
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Development

### Prerequisites

```bash
npm install
```

### Building

```bash
npm run build
```

### Running

```bash
# Development
npm run dev

# Production
npm start
```

### Testing

```bash
# Unit tests
npm test

# Integration tests
npm run test:integration

# Load testing
npm run test:load
```

## Phase 1A Implementation Status

### ✅ Completed Components

- [x] **Core Coordinator Service** - Request routing and decision logic
- [x] **Feature Flag System** - Gradual rollout control
- [x] **Configuration Management** - Environment-based configuration
- [x] **Health Check System** - Comprehensive health monitoring
- [x] **HTTP Server** - REST API with security middleware
- [x] **Docker Configuration** - Containerization and deployment
- [x] **Documentation** - Comprehensive API and deployment docs

### 🔄 Current Status

- **Routing Logic**: ✅ Implemented (routes all requests to existing orchestrator)
- **AGNO Integration**: 🔄 Placeholder (ready for Phase 2A implementation)
- **Feature Flags**: ✅ Implemented (AGNO routing disabled by default)
- **Health Checks**: ✅ Implemented (comprehensive monitoring)
- **Configuration**: ✅ Implemented (environment-based with validation)

### 📋 Next Steps (Phase 1B)

- [ ] Create MCP service wrappers for existing services
- [ ] Implement integration layer with existing orchestrator
- [ ] Add comprehensive monitoring and alerting
- [ ] Set up testing and validation pipeline

## Integration with Existing Services

### Current Architecture Integration

The AGNO Coordinator is designed to integrate seamlessly with the existing Sophia AI architecture:

```
Existing Orchestrator (sophia-orchestrator:3000)
    ↑
    │ HTTP calls
    ↓
AGNO Coordinator (agno-coordinator:3001)
    ↑
    │ Dashboard/API requests
    ↓
Sophia Dashboard/API Gateway
```

### MCP Service Compatibility

The coordinator is designed to work with existing MCP services:

- **mcp-agents**: Agent swarm capabilities
- **mcp-context**: Context and memory management
- **mcp-research**: Research and data analysis
- **mcp-business**: Business intelligence and CRM integration
- **mcp-github**: Code analysis and repository management

## Monitoring & Observability

### Metrics Collected

- **Request Metrics**: Count, latency, success rate by routing decision
- **Health Metrics**: Service health, dependency status, error rates
- **Performance Metrics**: Memory usage, CPU utilization, response times
- **Feature Metrics**: Feature flag usage, A/B test performance

### Logging

Structured logging with configurable levels:

```json
{
  "timestamp": "2025-08-25T23:00:00.000Z",
  "level": "info",
  "service": "agno-coordinator",
  "requestId": "req-123",
  "routingDecision": {
    "source": "existing",
    "confidence": 0.85,
    "complexity": "medium"
  },
  "executionTimeMs": 1250,
  "status": "success"
}
```

## Security Considerations

### Authentication & Authorization
- API key authentication for service-to-service communication
- Request validation and sanitization
- Rate limiting and abuse protection

### Data Protection
- No sensitive data storage in the coordinator
- Secure communication with existing services
- Audit logging for compliance

### Operational Security
- Non-root container execution
- Minimal attack surface
- Regular security updates

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check configuration
curl http://localhost:3001/health/detailed

# Check logs
docker-compose logs agno-coordinator

# Validate configuration
curl http://localhost:3001/config
```

#### Routing Issues
```bash
# Check feature flags
curl http://localhost:3001/flags

# Check service statistics
curl http://localhost:3001/stats

# Test routing endpoint
curl -X POST http://localhost:3001/route \
  -H "Content-Type: application/json" \
  -d '{"userPrompt": "test", "sessionId": "test"}'
```

#### Health Check Failures
```bash
# Detailed health report
curl http://localhost:3001/health/detailed

# Check dependencies
curl http://localhost:6379  # Redis
curl http://sophia-orchestrator:3000/healthz  # Existing orchestrator
```

## Contributing

### Development Guidelines

1. **Code Style**: Follow TypeScript best practices
2. **Testing**: Write tests for all new features
3. **Documentation**: Update documentation for API changes
4. **Security**: Follow security best practices
5. **Performance**: Monitor and optimize performance

### Testing Strategy

- **Unit Tests**: Test individual components and functions
- **Integration Tests**: Test service interactions and API endpoints
- **Load Tests**: Validate performance under load
- **Chaos Tests**: Test failure scenarios and recovery

## Roadmap

### Phase 1A: Foundation ✅
- [x] AGNO Coordinator Service implementation
- [x] Feature flag system
- [x] Health monitoring and configuration
- [x] Docker deployment configuration

### Phase 1B: MCP Integration 🔄
- [ ] MCP service wrappers
- [ ] Integration layer with existing orchestrator
- [ ] Comprehensive monitoring and alerting

### Phase 2A: Research Teams 📋
- [ ] Multi-agent research team implementation
- [ ] Web research with context integration
- [ ] Performance comparison and optimization

### Phase 2B: Business Intelligence 📋
- [ ] Sales intelligence team
- [ ] CRM integration enhancements
- [ ] Business workflow automation

## Support

For support and questions:

- **Documentation**: See this README and inline code documentation
- **Issues**: Create GitHub issues with detailed reproduction steps
- **Health Checks**: Use `/healthz` and `/health/detailed` endpoints
- **Logs**: Check service logs for detailed error information

## License

This service is part of the Sophia AI Intelligence Team's internal tooling and is not intended for external distribution.