#!/bin/bash
set -euo pipefail

# Sophia AI Kubernetes Deployment Script for Lambda Labs
# IP: 192.222.51.223

LAMBDA_IP="192.222.51.223"
LAMBDA_USER="ubuntu"  # Adjust if different
GITHUB_REGISTRY="ghcr.io/ai-cherry"

echo "=== Sophia AI Kubernetes Deployment to Lambda Labs ==="
echo "Target server: ${LAMBDA_IP}"
echo

# Function to execute commands on remote server
remote_exec() {
    ssh -o StrictHostKeyChecking=no ${LAMBDA_USER}@${LAMBDA_IP} "$@"
}

# Function to copy files to remote server
remote_copy() {
    scp -r -o StrictHostKeyChecking=no "$1" ${LAMBDA_USER}@${LAMBDA_IP}:"$2"
}

# Step 1: Copy deployment files to Lambda Labs
echo "Step 1: Copying deployment files to Lambda Labs..."
remote_exec "mkdir -p ~/k8s-deploy"
remote_copy "k8s-deploy/*" "~/k8s-deploy/"

# Step 2: Install K3s on Lambda Labs
echo "Step 2: Installing K3s with GPU support..."
remote_exec "cd ~/k8s-deploy && bash scripts/install-k3s-clean.sh"

# Step 3: Create secrets from .env.production
echo "Step 3: Creating Kubernetes secrets..."
# First, copy .env.production to remote
remote_copy ".env.production" "~/k8s-deploy/.env.production"
remote_exec "cd ~/k8s-deploy && bash scripts/create-all-secrets.sh"

# Step 4: Apply Kubernetes manifests
echo "Step 4: Deploying services..."
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/namespace.yaml"
# Deploy Redis first as other services depend on it
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/redis.yaml"
echo "Waiting for Redis to be ready..."
sleep 20
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/sophia-dashboard.yaml"
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/mcp-research.yaml"
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/mcp-context.yaml"
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/mcp-agents.yaml"

# Step 5: Deploy ingress controller
echo "Step 5: Setting up ingress controller..."
remote_exec "kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml"
echo "Waiting for ingress controller to be ready..."
sleep 30
remote_exec "kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=120s"
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/single-ingress.yaml"

# Step 6: Deploy monitoring (optional)
echo "Step 6: Deploying Kubernetes Dashboard..."
remote_exec "kubectl apply -f ~/k8s-deploy/monitoring/dashboard-only.yaml"

# Step 7: Verify deployment
echo "Step 7: Verifying deployment..."
echo "Pods status:"
remote_exec "kubectl get pods -n sophia"
echo
echo "Services status:"
remote_exec "kubectl get services -n sophia"
echo
echo "Ingress status:"
remote_exec "kubectl get ingress -n sophia"

# Step 8: Get dashboard token
echo "Step 8: Getting dashboard access token..."
remote_exec "kubectl -n kubernetes-dashboard create token admin-user"

echo
echo "=== Deployment Complete ==="
echo "1. Update DNS to point www.sophia-intel.ai to ${LAMBDA_IP}"
echo "2. Access Kubernetes Dashboard at https://${LAMBDA_IP}:31443"
echo "3. Services will be available at https://www.sophia-intel.ai once DNS propagates"
echo
echo "To check deployment status:"
echo "ssh ${LAMBDA_USER}@${LAMBDA_IP} kubectl get pods -n sophia"
