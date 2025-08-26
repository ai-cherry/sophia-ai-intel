# Sophia AI Kubernetes Deployment

This directory contains the unified Kubernetes deployment structure for Sophia AI platform, providing a production-ready, secure, and scalable infrastructure.

## Directory Structure

```
k8s-deploy/
├── README.md                    # This file
├── deploy.sh                    # Unified deployment script
├── manifests/                   # Kubernetes manifests
│   ├── namespace.yaml          # Namespace definition
│   └── configmap.yaml          # Non-sensitive configuration
├── secrets/                     # Kubernetes secrets (base64 encoded)
│   ├── README.md               # Secrets management guide
│   ├── database-secrets.yaml   # Database credentials
│   ├── llm-secrets.yaml        # LLM API keys
│   ├── business-secrets.yaml   # Business integration keys
│   └── infrastructure-secrets.yaml # Infrastructure secrets
└── scripts/                     # Deployment automation scripts
    └── install-k3s-clean.sh    # K3s installation script
```

## Quick Start

### Prerequisites

1. **Kubernetes Cluster**: Running K3s, EKS, GKE, or AKS
2. **kubectl**: Configured to access your cluster
3. **Base64 Encoded Secrets**: All sensitive values must be base64 encoded

### Basic Deployment

```bash
# Make deployment script executable
chmod +x k8s-deploy/deploy.sh

# Deploy all services
cd k8s-deploy && ./deploy.sh deploy

# Check deployment status
./deploy.sh status
```

## Configuration Management

### Secrets Management

Secrets are organized by category for better management:

1. **Database Secrets** (`database-secrets.yaml`)
   - PostgreSQL/Neon connections
   - Redis credentials
   - Qdrant API keys

2. **LLM Secrets** (`llm-secrets.yaml`)
   - OpenAI, Anthropic, DeepSeek keys
   - All LLM provider API keys

3. **Business Secrets** (`business-secrets.yaml`)
   - HubSpot, Salesforce, Gong integrations
   - Business application API keys

4. **Infrastructure Secrets** (`infrastructure-secrets.yaml`)
   - Lambda Labs, DNSimple credentials
   - Docker Hub, monitoring passwords

### Environment Variables

Non-sensitive configuration is managed through ConfigMaps:

- Service ports and URLs
- Feature flags
- Logging and monitoring settings
- Performance tuning parameters

## Deployment Process

### 1. Prepare Secrets

Before deployment, encode all secret values:

```bash
# Example: Encode API key
echo -n "your-openai-api-key" | base64

# Update the YAML files with encoded values
# Replace <BASE64_ENCODED_OPENAI_API_KEY> with actual value
```

### 2. Deploy Configuration

```bash
# Apply namespace and basic configuration
kubectl apply -f manifests/namespace.yaml
kubectl apply -f manifests/configmap.yaml

# Apply secrets
kubectl apply -f secrets/
```

### 3. Deploy Services

The unified deployment script handles service deployment in the correct order:

```bash
./deploy.sh deploy
```

### 4. Verify Deployment

```bash
# Check all resources
./deploy.sh status

# View logs
kubectl logs -n sophia deployment/your-service

# Check service endpoints
kubectl get services -n sophia
```

## Service Architecture

### Core Services

- **Dashboard**: React-based frontend (`sophia-dashboard:3000`)
- **MCP Services**: Context, Research, Business, GitHub integrations
- **AGNO Teams**: Sales Intelligence, Client Health teams
- **Coordinator**: Service orchestration and coordination

### Supporting Services

- **PostgreSQL/Neon**: Primary database
- **Redis**: Caching and session storage
- **Qdrant**: Vector database for embeddings
- **Monitoring Stack**: Prometheus, Grafana, Loki, Promtail

## Security Features

### Secret Management
- Kubernetes Secrets for sensitive data
- Base64 encoding for all credentials
- Separate secrets by category and access level

### Network Security
- Namespace isolation
- Network policies (when implemented)
- Service-to-service authentication

### Access Control
- RBAC for pod and API access
- Service account management
- Least privilege principle

## Monitoring and Observability

### Health Checks
- Liveness and readiness probes
- Service dependency monitoring
- Automated health verification

### Logging
- Centralized logging with Loki
- Structured JSON logging
- Log retention policies

### Metrics
- Prometheus metrics collection
- Grafana dashboards
- Alerting with predefined thresholds

## Scaling and Performance

### Resource Management
- Configurable resource limits
- Horizontal Pod Autoscaling
- Resource optimization

### Performance Tuning
- Connection pooling
- Caching strategies
- Database optimization

## Backup and Recovery

### Automated Backups
- Scheduled database backups
- Configuration backups
- Recovery time objectives (RTO) and recovery point objectives (RPO)

### Disaster Recovery
- Multi-zone deployment support
- Automated failover procedures
- Data consistency verification

## Troubleshooting

### Common Issues

1. **Pod Startup Failures**
   ```bash
   kubectl describe pod <pod-name> -n sophia
   kubectl logs <pod-name> -n sophia
   ```

2. **Service Discovery Issues**
   ```bash
   kubectl get endpoints -n sophia
   kubectl describe service <service-name> -n sophia
   ```

3. **Secret Access Issues**
   ```bash
   kubectl describe secret <secret-name> -n sophia
   # Verify base64 encoding
   echo -n "encoded-value" | base64 -d
   ```

### Debug Commands

```bash
# Get all resources in namespace
kubectl get all -n sophia

# Check events
kubectl get events -n sophia --sort-by='.lastTimestamp'

# Debug specific pod
kubectl exec -it <pod-name> -n sophia -- /bin/bash
```

## Development and Staging

### Environment Separation
- Separate namespaces for dev/staging/prod
- Environment-specific configurations
- Isolated secrets per environment

### CI/CD Integration
- GitHub Actions workflows
- Automated testing and deployment
- Rollback capabilities

## Contributing

### Adding New Services
1. Create service-specific manifests
2. Update ConfigMaps for non-sensitive config
3. Add secrets to appropriate secret file
4. Update deployment script if needed
5. Test deployment in staging environment

### Manifest Standards
- Use consistent labeling
- Include resource limits
- Add health checks
- Document service dependencies

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review deployment logs
3. Consult the service-specific documentation
4. Check GitHub issues for known problems

## Version History

- **v1.0.0**: Initial unified Kubernetes deployment
- **v1.1.0**: Enhanced secrets management and security
- **v1.2.0**: Improved monitoring and observability
- **v1.3.0**: Performance optimizations and scaling improvements