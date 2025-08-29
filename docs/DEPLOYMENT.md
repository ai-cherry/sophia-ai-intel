# Sophia AI Deployment Guide

## Overview

This guide covers the deployment setup for the Sophia AI platform, including CI/CD pipelines, container orchestration, and multi-environment deployment strategies.

## CI/CD Pipeline

### GitHub Actions Workflows

The project uses GitHub Actions for continuous integration and deployment with the following workflows:

1. **test.yml** - Runs the complete test suite including unit, integration, and end-to-end tests
2. **deploy.yml** - Handles deployment of the MCP platform
3. **production-deployment.yml** - Manages production deployments with proper safeguards
4. **sophia_infra.yml** - Infrastructure provisioning and management
5. **sophia_infra_rollback.yml** - Rollback procedures for infrastructure changes
6. **neon-migrations.yml** - Database migration workflows
7. **nightly_health_proofs.yml** - Automated health checks and system proofs
8. **no-mocks.yml** - Ensures no mock implementations are deployed to production

### Workflow Triggers

- **Push to main/develop branches**: Automatic testing and staging deployment
- **Pull Requests**: Pre-merge testing and validation
- **Scheduled (cron)**: Nightly health checks and maintenance tasks
- **Manual triggers**: Production deployments and infrastructure changes

## Container Orchestration

### Docker Compose Setup

The platform uses Docker Compose for local development and testing with the following service architecture:

#### Core Services
- **agno-coordinator**: Main AI orchestration layer
- **mcp-agents**: Agent management and orchestration
- **mcp-context**: Context and memory management
- **orchestrator**: Service coordination and routing

#### Business Integration Services
- **mcp-github**: GitHub integration
- **mcp-hubspot**: HubSpot CRM integration
- **mcp-salesforce**: Salesforce integration
- **mcp-gong**: Gong call analytics integration
- **mcp-slack**: Slack integration
- **mcp-apollo**: Apollo.io integration
- **mcp-business**: General business services
- **mcp-lambda**: Lambda cloud services

#### AI and LLM Services
- **portkey-llm**: LLM routing and management
- **agents-swarm**: Multi-agent swarm orchestration

#### Infrastructure Services
- **redis**: Caching and session management
- **postgres**: Primary database
- **prometheus**: Metrics collection
- **grafana**: Monitoring and visualization
- **loki**: Log aggregation
- **promtail**: Log shipping
- **nginx**: Reverse proxy and load balancing

### Deployment Commands

```bash
# Local development
docker-compose up -d

# Production deployment
docker-compose -f docker-compose.production.yml up -d

# Scaling services
docker-compose up -d --scale mcp-agents=3
```

## Multi-Environment Deployment

### Environment Configuration

Each environment uses specific configuration files:
- **Development**: `.env.development`
- **Staging**: `.env.staging`
- **Production**: `.env.production`

### Secrets Management

Secrets are managed through multiple backends:
1. **GitHub Actions Secrets** - CI/CD pipeline secrets
2. **Pulumi ESC** - Infrastructure configuration secrets
3. **Fly.io Secrets** - Production runtime secrets
4. **Environment Variables** - Development and local testing

## Fly.io Deployment

### Prerequisites
- Fly.io CLI installed (`flyctl`)
- Authenticated with Fly.io account
- App created in Fly.io dashboard

### Deployment Scripts

Located in `scripts/` directory:
- `fly-deploy.sh` - Main deployment script with multiple strategies
- `fly-sync-secrets.sh` - Secret synchronization script
- `fly-rollback.sh` - Rollback procedures
- `fly-monitor.sh` - Health monitoring

### Deployment Strategies

1. **Rolling Deployment** (default): Gradual rollout with zero downtime
2. **Blue-Green Deployment**: Complete environment swap for zero-downtime deployments
3. **Canary Deployment**: Gradual rollout with health monitoring

### Example Usage

```bash
# Rolling deployment
./scripts/fly-deploy.sh rolling

# Blue-green deployment
./scripts/fly-deploy.sh blue-green

# Canary deployment
./scripts/fly-deploy.sh canary
```

## Pulumi Infrastructure as Code

### Configuration

Pulumi configuration is managed in `infrastructure/pulumi/` with:
- **Pulumi.yaml**: Project configuration
- **Stack configurations**: Environment-specific settings

### Managed Resources

- Cloud infrastructure provisioning
- Service discovery setup
- Network security configuration
- Auto-scaling policies
- Monitoring and alerting

### Deployment Commands

```bash
# Initialize Pulumi
pulumi up

# Deploy specific stack
pulumi up -s production

# Destroy infrastructure
pulumi destroy
```

## Health Monitoring and Observability

### Service Health Checks

All services include health check endpoints:
- `/healthz` - Basic health status
- `/metrics` - Prometheus metrics
- `/health` - Detailed health information

### Monitoring Stack

- **Prometheus**: Metrics collection and storage
- **Grafana**: Dashboard and visualization
- **Loki**: Log aggregation
- **Promtail**: Log shipping

### Alerting

Configured alerts for:
- Service downtime
- High resource usage
- Performance degradation
- Error rate thresholds

## Security and Compliance

### Network Security

- Service-to-service communication encryption
- Network segmentation
- Firewall rules
- Access control policies

### Secret Rotation

- Automated secret rotation policies
- Manual rotation procedures
- Backup and recovery processes

### Compliance

- Data encryption at rest and in transit
- Audit logging
- Access control
- Regular security scanning

## Troubleshooting

### Common Issues

1. **Deployment Failures**
   - Check GitHub Actions logs
   - Verify secrets and configuration
   - Review service dependencies

2. **Health Check Failures**
   - Check service logs
   - Verify database connections
   - Review resource limits

3. **Performance Issues**
   - Monitor resource usage
   - Check scaling policies
   - Review database queries

### Debugging Commands

```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs <service-name>

# Monitor resource usage
docker stats

# Check health endpoints
curl http://localhost:<port>/healthz
```

## Rollback Procedures

### Automated Rollbacks

GitHub Actions workflows include automatic rollback on:
- Failed health checks
- Test suite failures
- Deployment timeouts

### Manual Rollbacks

```bash
# Fly.io rollback
./scripts/fly-rollback.sh

# Pulumi rollback
pulumi stack history
pulumi stack select <previous-version>
```

## Best Practices

### Deployment Best Practices

1. **Zero-Downtime Deployments**
   - Use rolling updates
   - Implement health checks
   - Configure proper load balancing

2. **Configuration Management**
   - Use environment-specific configs
   - Manage secrets securely
   - Version control configurations

3. **Monitoring and Observability**
   - Implement comprehensive logging
   - Set up meaningful metrics
   - Configure appropriate alerts

4. **Security**
   - Regular security scanning
   - Secret rotation policies
   - Access control reviews

### Testing Best Practices

1. **Pre-deployment Testing**
   - Unit tests
   - Integration tests
   - End-to-end tests

2. **Post-deployment Testing**
   - Smoke tests
   - Health checks
   - Performance validation

## Future Improvements

Planned enhancements:
- Kubernetes deployment support
- Advanced auto-scaling policies
- Enhanced monitoring and alerting
- Improved rollback automation
- Multi-region deployment support
