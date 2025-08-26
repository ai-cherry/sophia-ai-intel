#!/bin/bash
set -euo pipefail

# Sophia AI Production Deployment Script
# Deploy to www.sophia-intel.ai via DNSimple

echo "=== Sophia AI Production Deployment ==="
echo "Target: www.sophia-intel.ai"
echo "Server: Lambda Labs (192.222.51.223)"
echo

# Configuration
DOMAIN="www.sophia-intel.ai"
LAMBDA_IP="192.222.51.223"
LAMBDA_USER="ubuntu"

# Check environment variables
if [ -z "${DNSIMPLE_TOKEN:-}" ]; then
    echo "⚠️  DNSIMPLE_TOKEN not set. DNS updates will be skipped."
    echo "   Set it with: export DNSIMPLE_TOKEN='your-token'"
fi

if [ -z "${DNSIMPLE_ACCOUNT_ID:-}" ]; then
    echo "⚠️  DNSIMPLE_ACCOUNT_ID not set. DNS updates will be skipped."
    echo "   Set it with: export DNSIMPLE_ACCOUNT_ID='your-account-id'"
fi

# Step 1: Update DNS Records
if [ -n "${DNSIMPLE_TOKEN:-}" ] && [ -n "${DNSIMPLE_ACCOUNT_ID:-}" ]; then
    echo "Step 1: Updating DNS records in DNSimple..."
    
    # Update www record
    curl -s -H "Authorization: Bearer ${DNSIMPLE_TOKEN}" \
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
    
    # Update root record
    curl -s -H "Authorization: Bearer ${DNSIMPLE_TOKEN}" \
         -H "Accept: application/json" \
         -H "Content-Type: application/json" \
         -X PATCH \
         "https://api.dnsimple.com/v2/${DNSIMPLE_ACCOUNT_ID}/zones/sophia-intel.ai/records" \
         -d '{
           "name": "",
           "type": "A",
           "content": "'${LAMBDA_IP}'",
           "ttl": 300
         }'
    
    # Update api subdomain
    curl -s -H "Authorization: Bearer ${DNSIMPLE_TOKEN}" \
         -H "Accept: application/json" \
         -H "Content-Type: application/json" \
         -X PATCH \
         "https://api.dnsimple.com/v2/${DNSIMPLE_ACCOUNT_ID}/zones/sophia-intel.ai/records" \
         -d '{
           "name": "api",
           "type": "A",
           "content": "'${LAMBDA_IP}'",
           "ttl": 300
         }'
    
    echo "✓ DNS records updated"
else
    echo "Step 1: Skipping DNS update (credentials not set)"
fi

# Step 2: Deploy to Lambda Labs
echo
echo "Step 2: Deploying to Lambda Labs..."
echo "Connecting to ${LAMBDA_USER}@${LAMBDA_IP}..."

# Check SSH connectivity
if ! ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ${LAMBDA_USER}@${LAMBDA_IP} "echo 'SSH connection successful'" 2>/dev/null; then
    echo "❌ Cannot connect to Lambda Labs server"
    echo "   Please ensure:"
    echo "   1. The server is running"
    echo "   2. Your SSH key is configured"
    echo "   3. The IP address is correct: ${LAMBDA_IP}"
    exit 1
fi

# Deploy via SSH
ssh -o StrictHostKeyChecking=no ${LAMBDA_USER}@${LAMBDA_IP} << 'ENDSSH'
set -e

echo "Checking for repository..."
if [ ! -d "sophia-ai-intel-1" ]; then
    echo "Cloning repository..."
    git clone https://github.com/ai-cherry/sophia-ai-intel.git sophia-ai-intel-1
fi

cd sophia-ai-intel-1

echo "Pulling latest changes..."
git pull origin main

echo "Checking Kubernetes..."
if ! kubectl version --short 2>/dev/null; then
    echo "Installing K3s..."
    curl -sfL https://get.k3s.io | sh -
    sudo chmod 644 /etc/rancher/k3s/k3s.yaml
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
fi

echo "Creating namespace..."
kubectl create namespace sophia 2>/dev/null || true

echo "Deploying services..."
if [ -f "k8s-deploy/scripts/deploy-all-services.sh" ]; then
    bash k8s-deploy/scripts/deploy-all-services.sh
else
    # Manual deployment if script doesn't exist
    kubectl apply -f k8s-deploy/manifests/namespace.yaml
    kubectl apply -f k8s-deploy/manifests/
fi

echo "Deployment complete on Lambda Labs!"
ENDSSH

# Step 3: Configure SSL
echo
echo "Step 3: Setting up SSL certificates..."
ssh -o StrictHostKeyChecking=no ${LAMBDA_USER}@${LAMBDA_IP} << 'ENDSSH'
# Install cert-manager if not present
if ! kubectl get namespace cert-manager 2>/dev/null; then
    echo "Installing cert-manager..."
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
    sleep 30
fi

# Create Let's Encrypt issuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@sophia-intel.ai
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Update ingress with TLS
kubectl apply -f - <<EOF
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
EOF

echo "SSL configuration complete!"
ENDSSH

# Step 4: Verify deployment
echo
echo "Step 4: Verifying deployment..."
echo

# Check DNS
echo "DNS Status:"
echo -n "  www.sophia-intel.ai: "
dig +short www.sophia-intel.ai || echo "Not resolved yet"
echo -n "  api.sophia-intel.ai: "
dig +short api.sophia-intel.ai || echo "Not resolved yet"

# Check services (if DNS is resolved)
if [ "$(dig +short www.sophia-intel.ai)" = "${LAMBDA_IP}" ]; then
    echo
    echo "Service Status:"
    echo -n "  Main site: "
    curl -sI https://www.sophia-intel.ai | head -n 1 || echo "Not accessible yet"
    echo -n "  API: "
    curl -s https://api.sophia-intel.ai/healthz || echo "Not accessible yet"
else
    echo
    echo "⚠️  DNS not propagated yet. Services will be available once DNS updates."
fi

echo
echo "=== Deployment Summary ==="
echo
echo "✅ Code deployed to Lambda Labs"
echo "✅ Kubernetes services started"
echo "✅ SSL certificates configured"
echo
echo "Access URLs (once DNS propagates):"
echo "  - Main site: https://www.sophia-intel.ai"
echo "  - API: https://api.sophia-intel.ai"
echo
echo "Direct access (before DNS):"
echo "  - http://${LAMBDA_IP}"
echo
echo "Monitor deployment:"
echo "  ssh ${LAMBDA_USER}@${LAMBDA_IP} kubectl get pods -n sophia"
echo
echo "DNS propagation can take up to 48 hours, but usually completes within 15 minutes."
echo
