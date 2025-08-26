#!/bin/bash
set -euo pipefail

# Sophia AI Complete Ecosystem Deployment Script
# Deploys all Sophia AI services with comprehensive monitoring and validation

LAMBDA_IP="192.222.51.223"
LAMBDA_USER="ubuntu"
GITHUB_REGISTRY="ghcr.io/ai-cherry"

echo "=== Sophia AI Complete Ecosystem Deployment ==="
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

# Step 1: Copy updated deployment files
echo "Step 1: Updating deployment files on Lambda Labs..."
remote_exec "mkdir -p ~/k8s-deploy"
remote_copy "k8s-deploy/*" "~/k8s-deploy/"

# Step 2: Create namespace and RBAC
echo "Step 2: Setting up namespace and RBAC..."
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/namespace.yaml"
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/rbac.yaml"

# Step 3: Create secrets from .env.production
echo "Step 3: Creating Kubernetes secrets..."
remote_copy ".env.production" "~/k8s-deploy/.env.production"
remote_exec "cd ~/k8s-deploy && bash scripts/create-all-secrets.sh"

# Step 4: Deploy infrastructure components
echo "Step 4: Deploying infrastructure components..."
echo "  - Redis..."
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/redis.yaml"
echo "  - External Secrets Operator..."
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/external-secrets.yaml"

# Wait for Redis
echo "Waiting for Redis to be ready..."
sleep 30
remote_exec "kubectl wait --namespace sophia --for=condition=ready pod -l app=redis --timeout=300s" || echo "Redis may still be starting..."

# Step 5: Deploy MCP Services
echo "Step 5: Deploying MCP Services..."
services=(
    "mcp-research:~/k8s-deploy/manifests/mcp-research.yaml"
    "mcp-context:~/k8s-deploy/manifests/mcp-context.yaml"
    "mcp-agents:~/k8s-deploy/manifests/mcp-agents.yaml"
    "mcp-hubspot:~/k8s-deploy/manifests/mcp-hubspot.yaml"
    "mcp-business:~/k8s-deploy/manifests/mcp-business.yaml"
    "mcp-github:~/k8s-deploy/manifests/mcp-github.yaml"
)

for service in "${services[@]}"; do
    service_name=$(echo $service | cut -d: -f1)
    manifest_path=$(echo $service | cut -d: -f2)
    echo "  - $service_name..."
    remote_exec "kubectl apply -f $manifest_path"
    sleep 10
done

# Step 6: Deploy Agno Services
echo "Step 6: Deploying Agno Services..."
echo "  - agno-coordinator..."
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/agno-coordinator.yaml"
sleep 10

echo "  - agno-teams..."
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/agno-teams.yaml"
sleep 10

# Step 7: Deploy Orchestrator
echo "Step 7: Deploying Orchestrator..."
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/orchestrator.yaml"
sleep 10

# Step 8: Deploy Sonic AI

# Step 9: Set up ingress controller
echo "Step 9: Setting up ingress controller..."
remote_exec "kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml"
echo "Waiting for ingress controller to be ready..."
sleep 30
remote_exec "kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=300s"

# Step 10: Configure ingress rules
echo "Step 10: Configuring ingress rules..."
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/single-ingress.yaml"

# Step 11: Deploy comprehensive monitoring stack
echo "Step 11: Deploying monitoring stack..."
echo "  - Prometheus..."
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/prometheus.yaml"
echo "  - Grafana..."
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/grafana.yaml"
echo "  - Loki..."
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/loki.yaml"
echo "  - Promtail..."
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/promtail.yaml"
echo "  - AlertManager..."
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/alertmanager.yaml"

# Step 12: Configure HPA and VPA
echo "Step 12: Setting up auto-scaling..."
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/hpa.yaml"
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/vpa.yaml"

# Step 13: Set up network policies
echo "Step 13: Configuring network policies..."
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/network-policies.yaml"
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/mtls-network-policies.yaml"

# Step 14: Deploy persistent volume claims
echo "Step 14: Setting up persistent storage..."
remote_exec "kubectl apply -f ~/k8s-deploy/manifests/pvcs.yaml"

# Step 15: Wait for all services to be ready
echo "Step 15: Waiting for all services to be ready..."
sleep 60

# Wait for deployments
remote_exec "kubectl wait --namespace sophia --for=condition=available --timeout=600s deployment/mcp-research deployment/mcp-context deployment/mcp-agents deployment/mcp-hubspot deployment/mcp-business deployment/mcp-github deployment/agno-coordinator deployment/agno-teams deployment/orchestrator" || echo "Some deployments may still be starting..."

# Step 16: Verify deployment status
echo "Step 16: Verifying deployment status..."
echo "Pods status:"
remote_exec "kubectl get pods -n sophia"
echo
echo "Services status:"
remote_exec "kubectl get services -n sophia"
echo
echo "Ingress status:"
remote_exec "kubectl get ingress -n sophia"
echo
echo "Persistent volumes:"
remote_exec "kubectl get pvc -n sophia"

# Step 17: Run health checks
echo "Step 17: Running health checks..."
remote_exec "cd ~/k8s-deploy && bash scripts/health-check.sh"

# Step 18: Get monitoring access information
echo "Step 18: Getting monitoring access information..."
echo "Grafana admin password:"
remote_exec "kubectl get secret --namespace monitoring grafana -o jsonpath='{.data.admin-password}' | base64 --decode"

# Step 19: Run comprehensive testing
echo "Step 19: Running comprehensive tests..."
remote_exec "cd ~/k8s-deploy && bash scripts/run-integration-tests.sh"

echo
echo "=== Sophia AI Ecosystem Deployment Complete ==="
echo "🎉 All services deployed successfully!"
echo
echo "📊 Access URLs:"
echo "  - Sophia AI Dashboard: https://www.sophia-intel.ai"
echo "  - Grafana Monitoring: https://${LAMBDA_IP}:3000"
echo "  - Kubernetes Dashboard: https://${LAMBDA_IP}:31443"
echo
echo "🔧 Service Endpoints:"
echo "  - Agno Coordinator: http://agno-coordinator.sophia:3002"
echo "  - Agno Teams: http://agno-teams.sophia:3003"
echo "  - Orchestrator: http://orchestrator.sophia:3001"
echo "  - MCP Research: http://mcp-research.sophia:8000"
echo "  - MCP Context: http://mcp-context.sophia:8001"
echo "  - MCP Agents: http://mcp-agents.sophia:8002"
echo "  - MCP HubSpot: http://mcp-hubspot.sophia:8004"
echo "  - MCP Business: http://mcp-business.sophia:8003"
echo "  - MCP GitHub: http://mcp-github.sophia:8005"
echo
echo "📋 Next Steps:"
echo "1. Update DNS to point www.sophia-intel.ai to ${LAMBDA_IP}"
echo "2. Configure monitoring alerts in Grafana"
echo "3. Set up log aggregation with Loki"
echo "4. Run load testing with the provided scripts"
echo "5. Configure backup policies for persistent data"
echo
echo "To check deployment status:"
echo "ssh ${LAMBDA_USER}@${LAMBDA_IP} kubectl get pods -n sophia"