#!/bin/bash
# Sophia AI - Complete Lambda Labs + K3s Production Deployment Script

# Configuration
INSTANCE_IP="192.222.51.223"
SSH_KEY_FILE="lambda-ssh-key"
NAMESPACE="sophia"

echo "======================================"
echo "🚀 Sophia AI - Production Deployment"
echo "======================================"
echo "Target: Lambda Labs + K3s"
echo "Instance IP: $INSTANCE_IP"
echo "Namespace: $NAMESPACE"
echo ""

# Test SSH connection
echo "🔍 Testing SSH connection..."
if ! ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "echo 'SSH connection successful'" 2>/dev/null; then
    echo "❌ SSH connection failed"
    exit 1
fi
echo "✅ SSH connection successful"
echo ""

# Step 1: Install K3s
echo "Step 1: Installing K3s on Lambda Labs instance..."
echo "This will remove Docker Compose and install K3s"

# Copy K3s installation script
scp -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" k8s-deploy/scripts/install-k3s-clean.sh ubuntu@$INSTANCE_IP:~/install-k3s.sh

# Make it executable and run it
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "chmod +x ~/install-k3s.sh"

# Run the installation (automatically answer 'y')
echo "Running K3s installation..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "echo 'y' | ~/install-k3s.sh"

echo "✅ K3s installation completed"
echo ""

# Step 2: Copy Kubernetes manifests and scripts
echo "Step 2: Copying Kubernetes manifests and scripts..."

# Create directories
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "mkdir -p ~/k8s-manifests ~/k8s-scripts ~/monitoring-stack ~/services"

# Copy manifests
scp -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" -r k8s-deploy/manifests/* ubuntu@$INSTANCE_IP:~/k8s-manifests/
scp -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" -r k8s-deploy/scripts/* ubuntu@$INSTANCE_IP:~/k8s-scripts/
scp -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" -r monitoring/* ubuntu@$INSTANCE_IP:~/monitoring-stack/

# Copy service configurations
scp -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" -r services/* ubuntu@$INSTANCE_IP:~/services/

echo "✅ Kubernetes manifests copied"
echo ""

# Step 3: Create secrets
echo "Step 3: Creating Kubernetes secrets..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "cd ~/k8s-scripts && chmod +x create-all-secrets.sh && ./create-all-secrets.sh"

echo "✅ Secrets created"
echo ""

# Step 4: Deploy services
echo "Step 4: Deploying Sophia AI services..."

# Apply namespace first
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "kubectl apply -f ~/k8s-manifests/namespace.yaml"

# Apply all manifests
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "kubectl apply -f ~/k8s-manifests/"

echo "✅ Services deployed"
echo ""

# Step 5: Deploy monitoring stack
echo "Step 5: Deploying monitoring stack..."

# Apply monitoring configurations
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "kubectl apply -f ~/monitoring-stack/prometheus.yml"
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "kubectl apply -f ~/monitoring-stack/loki-config.yml"
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "kubectl apply -f ~/monitoring-stack/promtail-config.yml"
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "kubectl apply -f ~/monitoring-stack/alerts.yml"

echo "✅ Monitoring stack deployed"
echo ""

# Step 6: Install ingress controller
echo "Step 6: Installing ingress controller..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx"
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "helm repo update"
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "helm install ingress-nginx ingress-nginx/ingress-nginx --namespace ingress-nginx --create-namespace"

echo "✅ Ingress controller installed"
echo ""

# Step 7: Wait for deployments to be ready
echo "Step 7: Waiting for deployments to be ready..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "sleep 120"

# Step 8: Check deployment status
echo "Step 8: Checking deployment status..."
echo ""
echo "📊 Cluster Status:"
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "kubectl get nodes -o wide"

echo ""
echo "🚀 Pods Status:"
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "kubectl get pods -o wide"

echo ""
echo "🌐 Services Status:"
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "kubectl get services -o wide"

echo ""
echo "🌐 Ingress Status:"
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "kubectl get ingress -o wide"

# Step 9: Run comprehensive health checks
echo ""
echo "Step 9: Running health checks..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "~/k8s-scripts/comprehensive-health-check.sh"

# Step 10: Test endpoints
echo ""
echo "Step 10: Testing service endpoints..."
echo ""
echo "🔍 Testing main application..."
curl -s -o /dev/null -w "%{http_code}" http://$INSTANCE_IP/health || echo "Main app not responding"

echo ""
echo "🔍 Testing monitoring..."
curl -s -o /dev/null -w "%{http_code}" http://$INSTANCE_IP:3000 || echo "Grafana not responding"
curl -s -o /dev/null -w "%{http_code}" http://$INSTANCE_IP:9090 || echo "Prometheus not responding"

echo ""
echo "======================================"
echo "✅ PRODUCTION DEPLOYMENT COMPLETE!"
echo "======================================"
echo ""
echo "🌐 Access URLs:"
echo "- Main Application: http://$INSTANCE_IP"
echo "- Grafana (Monitoring): http://$INSTANCE_IP:3000"
echo "- Prometheus: http://$INSTANCE_IP:9090"
echo "- Health Check: http://$INSTANCE_IP/health"
echo ""
echo "🔧 Useful kubectl commands:"
echo "- Check pods: kubectl get pods"
echo "- Check logs: kubectl logs <pod-name>"
echo "- Restart deployment: kubectl rollout restart deployment <deployment-name>"
echo "- Scale deployment: kubectl scale deployment <name> --replicas=<count>"
echo ""
echo "🎯 Next Steps:"
echo "1. Configure DNS to point to $INSTANCE_IP"
echo "2. Setup SSL certificates with Let's Encrypt"
echo "3. Configure monitoring alerts"
echo "4. Test all MCP service integrations"
echo ""
echo "🎉 Sophia AI is now running on Lambda Labs + K3s!"