# Sophia AI Ingress Routing Configuration

## Overview

This document describes the ingress routing configuration for www.sophia-intel.ai domain, providing comprehensive routing rules for all Sophia AI services.

## Architecture

The ingress configuration uses **NGINX Ingress Controller** with the following components:

- **Main Ingress**: `sophia-main-ingress` - Primary routing configuration
- **SSL/TLS**: Automatic certificate management via Let's Encrypt
- **Security**: Comprehensive security headers and rate limiting
- **Health Checks**: Multiple health check endpoints
- **CORS**: Cross-origin resource sharing configuration

## Service Routing Map

### Frontend Routes
| Path | Service | Port | Description |
|------|---------|------|-------------|
| `/` | sophia-dashboard | 8080 | Main dashboard application |
| `/health` | sophia-dashboard | 8080 | Health check endpoint |
| `/healthz` | sophia-dashboard | 8080 | Kubernetes health check |

### API Routes
| Path | Service | Port | Description |
|------|---------|------|-------------|
| `/api/research` | mcp-research | 8080 | Research service API |
| `/api/context` | sophia-context-green | 8081 | Context management API |
| `/api/github` | sophia-github-green | 8082 | GitHub integration API |
| `/api/business` | sophia-business-green | 8083 | Business intelligence API |
| `/api/lambda` | sophia-lambda-green | 8084 | Lambda functions API |
| `/api/hubspot` | sophia-hubspot-green | 8085 | HubSpot integration API |
| `/api/agents` | mcp-agents | 8002 | AI agents API |
| `/api/orchestrator` | orchestrator-green | 3001 | Service orchestration API |
| `/api/sonic` | sophia-research-green | 8080 | Sonic AI API |
| `/api/health` | mcp-research | 8080 | API health check |

### System Routes
| Path | Service | Port | Description |
|------|---------|------|-------------|
| `/.well-known/acme-challenge/` | cert-manager-acme-challenge | 8089 | Let's Encrypt challenges |

## Configuration Details

### Security Features

#### Headers
```yaml
X-Frame-Options: "DENY"
X-Content-Type-Options: "nosniff"
X-XSS-Protection: "1; mode=block"
Referrer-Policy: "strict-origin-when-cross-origin"
Strict-Transport-Security: "max-age=31536000; includeSubDomains; preload"
Content-Security-Policy: "default-src 'self'; script-src 'self' 'unsafe-inline'; ..."
```

#### Rate Limiting
- **Rate Limit**: 10 requests per minute per IP
- **Burst**: 100 requests
- **Average**: 50 requests/minute

#### CORS Configuration
- **Allowed Origin**: `https://www.sophia-intel.ai`
- **Allowed Methods**: `GET, POST, PUT, DELETE, OPTIONS`
- **Allowed Headers**: `DNT,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization`
- **Max Age**: 86400 seconds (24 hours)

### SSL/TLS Configuration

#### Certificate Management
- **Issuer**: Let's Encrypt Production (`letsencrypt-prod`)
- **Certificate**: `sophia-tls-secret`
- **Domains**: `www.sophia-intel.ai`
- **Auto-renewal**: Enabled

#### SSL Settings
- **Protocols**: TLS 1.2, TLS 1.3
- **Redirect**: All HTTP traffic automatically redirected to HTTPS
- **HSTS**: Enabled with 1 year max-age

## Service Architecture

### Kubernetes Services
- **mcp-research**: Research and analysis service
- **mcp-agents**: AI agents coordination service
- **sophia-dashboard**: Frontend dashboard application

### External Services (Docker Compose)
- **sophia-context-green**: Context management service
- **sophia-github-green**: GitHub integration service
- **sophia-business-green**: Business intelligence service
- **sophia-lambda-green**: Lambda functions service
- **sophia-hubspot-green**: HubSpot integration service
- **orchestrator-green**: Service orchestration

## Monitoring and Troubleshooting

### Health Check Endpoints
- **Application Health**: `https://www.sophia-intel.ai/health`
- **Kubernetes Health**: `https://www.sophia-intel.ai/healthz`
- **API Health**: `https://www.sophia-intel.ai/api/health`

### Common Issues

#### 404 Errors
- **Cause**: Service not running or misconfigured
- **Solution**: Check service status and logs
- **Command**: `kubectl get pods -n sophia`

#### 502 Bad Gateway
- **Cause**: Backend service not responding
- **Solution**: Check service endpoints and restart if needed
- **Command**: `kubectl describe ingress sophia-main-ingress -n sophia`

#### SSL Certificate Issues
- **Cause**: Certificate not issued or expired
- **Solution**: Check cert-manager status
- **Command**: `kubectl get certificates -n sophia`

### Logs and Debugging

#### View Ingress Logs
```bash
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

#### Check Certificate Status
```bash
kubectl get certificates -n sophia
kubectl describe certificate sophia-tls-secret -n sophia
```

#### Test Routing
```bash
# Test main endpoint
curl -I https://www.sophia-intel.ai/

# Test API endpoint
curl -I https://www.sophia-intel.ai/api/research

# Test health endpoint
curl https://www.sophia-intel.ai/health
```

## Deployment and Maintenance

### Files
- **Main Configuration**: `k8s-deploy/manifests/sophia-ingress-production.yaml`
- **ACME Challenge Service**: `k8s-deploy/manifests/cert-manager-acme-challenge.yaml`
- **Traefik Configuration**: `k8s-deploy/manifests/traefik-ingress.yaml` (alternative)

### Deployment Commands
```bash
# Deploy main ingress
kubectl apply -f k8s-deploy/manifests/sophia-ingress-production.yaml

# Deploy ACME challenge service
kubectl apply -f k8s-deploy/manifests/cert-manager-acme-challenge.yaml

# Check status
kubectl get ingress -n sophia
kubectl describe ingress sophia-main-ingress -n sophia
```

### Maintenance Tasks

#### Certificate Renewal
- Automatic renewal is handled by cert-manager
- Manual renewal: Delete the certificate secret to trigger re-issuance

#### Service Updates
- Update service ports in the ingress configuration
- Test routing after service updates
- Monitor logs for any routing issues

#### Security Updates
- Regularly update nginx ingress controller
- Review and update security headers as needed
- Monitor rate limiting effectiveness

## Performance Optimization

### Current Optimizations
- **Rate Limiting**: Prevents abuse and DoS attacks
- **SSL Termination**: Offloads SSL processing to ingress controller
- **Request/Response Compression**: Enabled for better performance
- **Timeout Configuration**: Optimized for API workloads

### Monitoring Recommendations
- Set up monitoring for ingress metrics
- Track response times and error rates
- Monitor SSL certificate expiration dates
- Alert on rate limit violations

## Future Enhancements

### Potential Improvements
1. **Advanced Routing**: Implement A/B testing capabilities
2. **Circuit Breaker**: Add circuit breaker patterns for resilience
3. **Authentication**: Integrate authentication middleware
4. **Caching**: Implement response caching for static content
5. **Load Balancing**: Advanced load balancing algorithms

### Migration Path
- Consider migrating to Traefik for advanced features
- Implement service mesh (Istio) for enhanced traffic management
- Add API gateway for centralized API management

## Support

For issues or questions regarding the ingress configuration:

1. Check the troubleshooting section above
2. Review the ingress controller logs
3. Verify service availability and configuration
4. Contact the platform team for complex issues

## Version History

- **v1.0**: Initial production deployment
- **v1.1**: Added comprehensive security headers
- **v1.2**: Implemented rate limiting and CORS configuration
- **v1.3**: Added advanced health check endpoints
- **v1.4**: Enhanced SSL/TLS configuration and monitoring

---

**Last Updated**: 2025-08-26
**Configuration Version**: v1.4
**Maintainer**: Sophia AI Platform Team