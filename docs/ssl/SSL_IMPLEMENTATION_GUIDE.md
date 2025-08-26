# Enterprise SSL/TLS Implementation Guide

## Overview

This document provides comprehensive guidance for the SSL/TLS implementation in the Sophia AI platform, covering both Kubernetes and Docker Compose deployments with enterprise-grade security configurations.

## Architecture

### SSL Certificate Management

**Certificate Authority**: Let's Encrypt
- Production certificates: Valid for 90 days
- Staging certificates: For testing and development
- Auto-renewal: Configured with cron jobs and cert-manager

### Domains and Certificates

**Primary Domain**: `www.sophia-intel.ai`
**Certificate Coverage**:
- `sophia-intel.ai` (root domain)
- `www.sophia-intel.ai` (main application)
- `api.sophia-intel.ai` (API endpoints)
- `monitoring.sophia-intel.ai` (monitoring stack)
- `*.sophia-intel.ai` (wildcard for subdomains)

### Security Features

**SSL/TLS Configuration**:
- TLS 1.2 and 1.3 support
- Modern cipher suites with perfect forward secrecy
- HSTS (HTTP Strict Transport Security)
- OCSP stapling for faster certificate validation
- Session resumption for improved performance

**Security Headers**:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: ...` (restrictive policy)

## Deployment Options

### Option 1: Kubernetes with Cert-Manager

**Prerequisites**:
- Kubernetes cluster with NGINX Ingress Controller
- cert-manager installed
- DNSimple API token configured

**Deployment Steps**:
```bash
# Apply SSL configurations
kubectl apply -f k8s-deploy/manifests/cert-manager.yaml
kubectl apply -f k8s-deploy/manifests/ingress-enhanced-ssl.yaml

# Wait for certificates
kubectl wait --for=condition=ready certificate/sophia-intel-ai-tls -n sophia --timeout=300s
```

**Verification**:
```bash
kubectl get certificates -n sophia
kubectl get ingress -n sophia
```

### Option 2: Docker Compose

**Prerequisites**:
- Docker and Docker Compose installed
- Domain DNS pointing to server IP
- Port 80 and 443 accessible

**Deployment Steps**:
```bash
# Run SSL setup
bash scripts/setup_ssl_letsencrypt.sh local

# Update docker-compose.yml to use SSL configuration
# (nginx.conf.ssl.production will be created)

# Deploy with SSL
docker-compose up -d
```

**Verification**:
```bash
docker-compose ps
curl -I https://www.sophia-intel.ai/health
```

## Configuration Files

### Core SSL Configuration Files

**Kubernetes**:
- `k8s-deploy/manifests/cert-manager.yaml` - Certificate management
- `k8s-deploy/manifests/ingress-enhanced-ssl.yaml` - Enhanced ingress with security
- `k8s-deploy/manifests/single-ingress.yaml` - Basic ingress configuration

**Docker Compose**:
- `nginx.conf.ssl` - Production SSL configuration
- `nginx.conf` - Basic configuration
- `ssl/` - Certificate storage directory

### SSL Scripts

**Management Scripts**:
- `scripts/setup_ssl_letsencrypt.sh` - Initial SSL setup
- `scripts/ssl-deployment-and-testing.sh` - Deployment and testing
- `scripts/monitor_ssl_health.sh` - Certificate monitoring

## Security Hardening

### SSL/TLS Settings

**Protocol Support**:
```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305;
ssl_prefer_server_ciphers off;
```

**Session Management**:
```nginx
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_session_tickets off;
```

### Rate Limiting and Security

**API Protection**:
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=health:10m rate=1r/s;
```

**CORS Configuration**:
```nginx
nginx.ingress.kubernetes.io/cors-allow-origin: "https://www.sophia-intel.ai"
nginx.ingress.kubernetes.io/cors-allow-methods: "GET, POST, PUT, DELETE, OPTIONS"
```

## Certificate Management

### Auto-Renewal Mechanisms

**Cert-Manager (Kubernetes)**:
- Automatic renewal 30 days before expiry
- DNS-01 challenge via DNSimple
- Certificate rotation with zero downtime

**Cron Jobs (Docker Compose)**:
```bash
# Daily renewal check at 3 AM
0 3 * * * /usr/local/bin/ssl-renewal.sh
```

### Monitoring and Alerts

**Certificate Expiry Monitoring**:
```bash
# Check certificate expiry
bash scripts/monitor_ssl_health.sh

# Alerts configured for:
# - Certificate expiry < 30 days
# - Certificate expiry < 7 days (critical)
# - SSL connection failures
```

## Testing and Validation

### SSL Testing Commands

**Basic Connectivity**:
```bash
# Test HTTPS connection
curl -I https://www.sophia-intel.ai/health

# Test SSL certificate
openssl s_client -connect www.sophia-intel.ai:443 -servername www.sophia-intel.ai
```

**Security Assessment**:
```bash
# SSL Labs assessment
curl -s "https://api.ssllabs.com/api/v4/analyze?host=www.sophia-intel.ai&publish=off"

# Check security headers
curl -I https://www.sophia-intel.ai/health | grep -E "(Strict-Transport-Security|X-Frame-Options|X-Content-Type-Options)"
```

**Protocol Testing**:
```bash
# Test TLS versions
openssl s_client -connect www.sophia-intel.ai:443 -tls1_2
openssl s_client -connect www.sophia-intel.ai:443 -tls1_3

# Verify certificate chain
openssl verify -CAfile /etc/ssl/certs/www.sophia-intel.ai.crt /etc/ssl/certs/www.sophia-intel.ai.crt
```

### Comprehensive Testing Script

```bash
# Run full SSL test suite
bash scripts/ssl-deployment-and-testing.sh test

# Run SSL Labs test
bash scripts/ssl-deployment-and-testing.sh labs

# Run health monitoring
bash scripts/ssl-deployment-and-testing.sh monitor
```

## Troubleshooting

### Common Issues

**Certificate Not Issued**:
```bash
# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager

# Check certificate status
kubectl describe certificate sophia-intel-ai-tls -n sophia

# Verify DNS challenge
kubectl get challenges -n sophia
```

**SSL Connection Failures**:
```bash
# Test certificate validity
openssl x509 -in /etc/ssl/certs/www.sophia-intel.ai.crt -text -noout

# Check nginx configuration
nginx -t

# Check nginx logs
tail -f /var/log/nginx/error.log
```

**DNS Issues**:
```bash
# Verify DNS records
dig www.sophia-intel.ai

# Check DNSimple configuration
kubectl describe secret dnsimple-secret -n cert-manager
```

### Emergency Certificate Replacement

**Quick Certificate Replacement**:
```bash
# For Docker Compose
bash scripts/setup_ssl_letsencrypt.sh local

# For Kubernetes
kubectl delete certificate sophia-intel-ai-tls -n sophia
kubectl apply -f k8s-deploy/manifests/cert-manager.yaml
```

## Performance Optimization

### SSL/TLS Performance

**Session Resumption**:
- SSL session cache enabled (10MB shared)
- Session timeout: 10 minutes
- Session tickets disabled for security

**OCSP Stapling**:
- Reduces certificate validation latency
- Cached OCSP responses
- Fallback to online validation

**SSL/TLS Handshake Optimization**:
- Modern cipher suites prioritized
- Perfect forward secrecy enabled
- Compression disabled for security

## Monitoring and Compliance

### SSL Metrics

**Prometheus Metrics**:
```yaml
# SSL certificate expiry metric
- job_name: 'ssl-exporter'
  static_configs:
    - targets: ['ssl-exporter:9219']
```

**Grafana Dashboards**:
- SSL certificate expiry tracking
- TLS connection metrics
- Security header compliance

### Compliance Standards

**Target Compliance**:
- SSL Labs A+ rating
- PCI DSS compliance for payment processing
- HIPAA compliance for healthcare data
- GDPR compliance for EU data

**Regular Audits**:
- Monthly SSL Labs assessment
- Quarterly security header review
- Annual SSL configuration audit

## Deployment Checklist

### Pre-Deployment
- [ ] Domain DNS configured and propagated
- [ ] SSL certificate requirements reviewed
- [ ] Security headers configured
- [ ] Rate limiting policies defined
- [ ] Monitoring alerts configured

### Deployment
- [ ] SSL certificates obtained
- [ ] Configuration files deployed
- [ ] Services restarted with new configuration
- [ ] HTTPS redirects verified
- [ ] Certificate chains validated

### Post-Deployment
- [ ] SSL Labs score verified (target: A+)
- [ ] Security headers confirmed
- [ ] TLS versions validated
- [ ] Monitoring alerts tested
- [ ] Documentation updated

## Emergency Contacts

**SSL Certificate Issues**:
- Primary: DevOps Team
- Secondary: Security Team
- Emergency: Infrastructure On-Call

**Let's Encrypt Rate Limits**:
- Certificates per domain: 20 per week
- Failed validation attempts: 5 per hour
- Duplicate certificate limit: 5 per week

## References

**Documentation Links**:
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Cert-Manager Documentation](https://cert-manager.io/docs/)
- [NGINX SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [SSL Labs Best Practices](https://github.com/ssllabs/research/wiki/SSL-and-TLS-Deployment-Best-Practices)

**Tools**:
- [SSL Labs Tester](https://www.ssllabs.com/ssltest/)
- [SSL Certificate Checker](https://www.sslchecker.com/)
- [Certificate Decoder](https://certificatedecoder.io/)

---

## Version History

- v1.0 - Initial enterprise SSL implementation
- v1.1 - Enhanced security headers and monitoring
- v1.2 - Added comprehensive testing suite
- v1.3 - Kubernetes cert-manager integration

## Support

For SSL-related issues or questions, please contact the DevOps team or create an issue in the infrastructure repository.