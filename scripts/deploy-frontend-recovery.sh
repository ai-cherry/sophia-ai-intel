#!/bin/bash

# Sophia AI Frontend Deployment Recovery Script
# Lambda Labs GH200 Instance: 192.222.51.223
# Created: 2025-08-28 05:04 UTC

set -e

echo "=== Sophia AI Frontend Deployment Recovery ==="
echo "Target: Lambda Labs GH200 (192.222.51.223)"
echo "Frontend Docker Image: sophia-dashboard:latest (49.9MB)"
echo

# Test connectivity
echo "1. Testing Lambda Labs connectivity..."
if ssh -i lambda_kube_ssh_key.pem -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@192.222.51.223 "echo 'Connection successful'" 2>/dev/null; then
    echo "✅ SSH connection successful"
else
    echo "❌ SSH connection failed - instance may be down or network issue"
    exit 1
fi

# Test kubectl connectivity
echo "2. Testing k3s cluster connectivity..."
if KUBECONFIG=kubeconfig_lambda.yaml kubectl cluster-info --request-timeout=10s >/dev/null 2>&1; then
    echo "✅ Kubernetes cluster accessible"
else
    echo "❌ k3s cluster not accessible - may need restart"
    echo "Run: ssh -i lambda_kube_ssh_key.pem root@192.222.51.223 'systemctl restart k3s'"
fi

# Deploy frontend
echo "3. Deploying Sophia AI frontend..."
echo "Frontend image: sophia-dashboard:latest (210MB with manifest)"

# Apply manifests
KUBECONFIG=kubeconfig_lambda.yaml kubectl apply -f k8s-deploy/manifests/consolidated/sophia-dashboard.yaml --validate=false
echo "✅ Frontend deployment applied"

# Apply ingress
KUBECONFIG=kubeconfig_lambda.yaml kubectl apply -f k8s-deploy/manifests/consolidated/www-sophia-intel-ai-ingress.yaml --validate=false
echo "✅ Ingress configuration applied"

# Check status
echo "4. Checking deployment status..."
KUBECONFIG=kubeconfig_lambda.yaml kubectl get pods -l app=sophia-dashboard
KUBECONFIG=kubeconfig_lambda.yaml kubectl get services -l app=sophia-dashboard
KUBECONFIG=kubeconfig_lambda.yaml kubectl get ingress

echo
echo "=== Deployment URLs ==="
echo "Frontend: http://192.222.51.223/ (internal)"
echo "Public: www.sophia-intel.ai (requires DNS/SSL setup)"
echo
echo "To monitor deployment:"
echo "KUBECONFIG=kubeconfig_lambda.yaml kubectl logs -f deployment/sophia-dashboard"
echo
echo "To access dashboard:"
echo "ssh -i lambda_kube_ssh_key.pem -L 8080:localhost:80 root@192.222.51.223"
echo "Then open: http://localhost:8080"