# Sophia AI Production Deployment Guide - www.sophia-intel.ai

## Overview

This guide covers deploying Sophia AI to production at www.sophia-intel.ai using DNSimple for DNS management and Lambda Labs (192.222.51.223) for hosting.

## DNS Configuration via DNSimple

### 1. Required DNS Records

Add these records in DNSimple for sophia-intel.ai domain:

```
# A Records
@         A     192.222.51.223   # Root domain
www       A     192.222.51.223   # www subdomain
api       A     192.222.51.223   # API subdomain

# CNAME Records (optional)
dashboard CNAME www.sophia-intel.ai
app       CNAME www.sophia-intel.ai

# MX Records (for email)
@         MX    10 mail.sophia-intel.ai
```

### 2. SSL/TLS Configuration

For HTTPS, you'll need:
- Let's Encrypt certificates (free)
- Or DNSimple SSL certificates

## Deployment Script for Production

```bash
#!/bin/bash
# deploy-to-production.sh

# Configuration
DOMAIN="www.sophia-intel.ai"
LAMBDA_IP="192.222.51.223"
LAMBDA_USER="ubuntu"

echo "=== Deploying Sophia AI to ${DOMAIN} ==="

# Step 1: Update DNS Records
echo "Step 1: Updating DNS records in DNSimple..."
# DNSimple API call (requires DNSIMPLE_TOKEN)
curl -H "Authorization: Bearer ${DNSIMPLE_TOKEN}" \
     -H "Accept: application/json" \
     -H "Content-Type: application/json" \
     -X PATCH \
     "https://api.dnsimple.com/v2/${DNSIMPLE_ACCOUNT_ID}/zones/sophia-intel.ai/records" \
     -d '{
       "name": "www",
       "type": "A",
       "content": "'${LAMBDA_IP}'",
       "ttl": 300
     }'

# Step 2: Deploy to Lambda Labs
echo "Step 2: Deploying to Lambda Labs..."
ssh ${LAMBDA_USER}@${LAMBDA_IP} << 'EOF'
cd ~/sophia-ai-intel-1
git pull origin main
./k8s-deploy/scripts/deploy-all-services.sh
EOF

# Step 3: Configure SSL
echo "Step 3: Setting up SSL certificates..."
ssh ${LAMBDA_USER}@${LAMBDA_IP} << 'EOF'
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create certificate
cat <<CERT | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: sophia-ai-cert
  namespace: sophia
spec:
  secretName: sophia-ai-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - sophia-intel.ai
  - www.sophia-intel.ai
  - api.sophia-intel.ai
CERT
EOF

# Step 4: Update Ingress
echo "Step 4: Updating Kubernetes Ingress..."
ssh ${LAMBDA_USER}@${LAMBDA_IP} << 'EOF'
kubectl apply -f - <<INGRESS
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sophia-ingress
  namespace: sophia
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - www.sophia-intel.ai
    - api.sophia-intel.ai
    secretName: sophia-ai-tls
  rules:
  - host: www.sophia-intel.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: sophia-dashboard
            port:
              number: 3000
  - host: api.sophia-intel.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nginx-proxy
            port:
              number: 80
INGRESS
EOF

echo "Deployment complete!"
echo "Access your site at: https://www.sophia-intel.ai"
```

## DNSimple API Configuration

### 1. Get API Token

1. Log into DNSimple
2. Go to Account → Access Tokens
3. Create new token with permissions:
   - Zone management
   - Record management

### 2. Set Environment Variables

```bash
export DNSIMPLE_TOKEN="your-api-token"
export DNSIMPLE_ACCOUNT_ID="your-account-id"
```

### 3. Automated DNS Update Script

```python
#!/usr/bin/env python3
# update-dns.py

import os
import requests
import json

DNSIMPLE_TOKEN = os.environ.get('DNSIMPLE_TOKEN')
DNSIMPLE_ACCOUNT_ID = os.environ.get('DNSIMPLE_ACCOUNT_ID')
DOMAIN = 'sophia-intel.ai'
LAMBDA_IP = '192.222.51.223'

headers = {
    'Authorization': f'Bearer {DNSIMPLE_TOKEN}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

base_url = f'https://api.dnsimple.com/v2/{DNSIMPLE_ACCOUNT_ID}'

# Records to create/update
records = [
    {'name': '', 'type': 'A', 'content': LAMBDA_IP, 'ttl': 300},  # @
    {'name': 'www', 'type': 'A', 'content': LAMBDA_IP, 'ttl': 300},
    {'name': 'api', 'type': 'A', 'content': LAMBDA_IP, 'ttl': 300},
]

# Get existing records
response = requests.get(f'{base_url}/zones/{DOMAIN}/records', headers=headers)
existing = {(r['name'], r['type']): r for r in response.json()['data']}

for record in records:
    key = (record['name'], record['type'])
    
    if key in existing:
        # Update existing record
        record_id = existing[key]['id']
        print(f"Updating {record['name'] or '@'} {record['type']} record...")
        requests.patch(
            f'{base_url}/zones/{DOMAIN}/records/{record_id}',
            headers=headers,
            json=record
        )
    else:
        # Create new record
        print(f"Creating {record['name'] or '@'} {record['type']} record...")
        requests.post(
            f'{base_url}/zones/{DOMAIN}/records',
            headers=headers,
            json=record
        )

print("DNS records updated successfully!")
```

## Complete Production Deployment Steps

### 1. Pre-deployment Checklist

- [ ] All services tested locally
- [ ] Environment variables configured
- [ ] SSL certificates ready
- [ ] Backup current deployment
- [ ] DNS propagation time considered (up to 48 hours)

### 2. Deploy to Production

```bash
# 1. Update DNS records
python3 update-dns.py

# 2. Deploy to Lambda Labs
ssh ubuntu@192.222.51.223
cd sophia-ai-intel-1
git pull origin main

# 3. Create production .env
cp .env.production.template .env.production
# Edit and fill in all values
nano .env.production

# 4. Deploy services
./k8s-deploy/scripts/deploy-to-lambda.sh

# 5. Setup SSL
kubectl apply -f k8s-deploy/manifests/ssl-issuer.yaml
kubectl apply -f k8s-deploy/manifests/ssl-certificate.yaml

# 6. Apply production ingress
kubectl apply -f k8s-deploy/manifests/production-ingress.yaml
```

### 3. Verify Deployment

```bash
# Check DNS propagation
dig www.sophia-intel.ai
nslookup www.sophia-intel.ai

# Check services
curl -I https://www.sophia-intel.ai
curl https://www.sophia-intel.ai/healthz

# Check SSL certificate
openssl s_client -connect www.sophia-intel.ai:443 -servername www.sophia-intel.ai
```

## Production Configuration Files

### nginx-production.conf

```nginx
server {
    listen 80;
    server_name sophia-intel.ai www.sophia-intel.ai;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name www.sophia-intel.ai;

    ssl_certificate /etc/letsencrypt/live/sophia-intel.ai/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sophia-intel.ai/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://sophia-dashboard:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://nginx-proxy:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### production-ingress.yaml

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sophia-production-ingress
  namespace: sophia
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/ssl-protocols: "TLSv1.2 TLSv1.3"
spec:
  tls:
  - hosts:
    - sophia-intel.ai
    - www.sophia-intel.ai
    - api.sophia-intel.ai
    secretName: sophia-ai-tls
  rules:
  - host: www.sophia-intel.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: sophia-dashboard
            port:
              number: 3000
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: nginx-proxy
            port:
              number: 80
  - host: api.sophia-intel.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nginx-proxy
            port:
              number: 80
```

## Monitoring Production

### 1. Health Checks

```bash
# Create health check script
cat > check-production.sh << 'EOF'
#!/bin/bash
echo "Checking www.sophia-intel.ai..."

# Check main site
curl -sI https://www.sophia-intel.ai | head -n 1

# Check API
curl -s https://api.sophia-intel.ai/healthz

# Check services
for service in research context github business lambda hubspot agents; do
    echo -n "Checking $service: "
    curl -s https://api.sophia-intel.ai/api/$service/healthz | jq -r '.status' || echo "Failed"
done
EOF

chmod +x check-production.sh
./check-production.sh
```

### 2. Monitoring URLs

- Main Site: https://www.sophia-intel.ai
- API: https://api.sophia-intel.ai
- Grafana: https://www.sophia-intel.ai/grafana
- Prometheus: https://www.sophia-intel.ai/prometheus

## Rollback Plan

If issues occur:

```bash
# 1. Quick rollback DNS to previous IP
python3 update-dns.py --ip OLD_IP

# 2. Or switch to maintenance mode
kubectl apply -f k8s-deploy/manifests/maintenance-mode.yaml

# 3. Restore from backup
kubectl apply -f backups/previous-deployment.yaml
```

## Security Considerations

1. **API Keys**: Never commit production keys
2. **SSL**: Always use HTTPS in production
3. **Firewall**: Configure Lambda Labs firewall
4. **Monitoring**: Set up alerts for downtime
5. **Backups**: Regular database and config backups

## Support

- DNS Issues: support@dnsimple.com
- Lambda Labs: support@lambdalabs.com
- Kubernetes: Check pod logs with `kubectl logs`

---

Ready to deploy to production at www.sophia-intel.ai!
