#!/bin/bash
# Sophia AI - Deploy Production Ingress Configuration
# Deploys ingress controller and production ingress rules for www.sophia-intel.ai

# Configuration
INSTANCE_IP="192.222.51.223"
SSH_KEY_FILE="lambda-ssh-key"
NAMESPACE="sophia"

echo "🚀 Deploying Production Ingress for www.sophia-intel.ai"
echo "======================================================"
echo "Target: Lambda Labs K3s Cluster ($INSTANCE_IP)"
echo "Domain: www.sophia-intel.ai"
echo ""

# Test SSH connection
echo "🔍 Testing SSH connection..."
if ! ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "echo 'SSH connection successful'" 2>/dev/null; then
    echo "❌ SSH connection failed"
    exit 1
fi
echo "✅ SSH connection successful"
echo ""

# Step 1: Check cluster status
echo "Step 1: Checking cluster status..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "kubectl get nodes -o wide"
echo ""

# Step 2: Create namespace if it doesn't exist
echo "Step 2: Ensuring namespace exists..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"
echo "✅ Namespace ready"
echo ""

# Step 3: Copy ingress manifests to cluster
echo "Step 3: Copying ingress manifests..."
scp -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" k8s-deploy/manifests/sophia-ingress-production.yaml ubuntu@$INSTANCE_IP:~/sophia-ingress-production.yaml
scp -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" k8s-deploy/manifests/ingress-enhanced-ssl.yaml ubuntu@$INSTANCE_IP:~/ingress-enhanced-ssl.yaml
echo "✅ Ingress manifests copied"
echo ""

# Step 4: Install NGINX Ingress Controller
echo "Step 4: Installing NGINX Ingress Controller..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP << 'EOF'
# Check if ingress controller already exists
if kubectl get deployment -n ingress-nginx ingress-nginx-controller >/dev/null 2>&1; then
    echo "✅ NGINX Ingress Controller already deployed"
else
    echo "📦 Installing NGINX Ingress Controller..."
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx >/dev/null 2>&1
    helm repo update >/dev/null 2>&1
    helm install ingress-nginx ingress-nginx/ingress-nginx \
        --namespace ingress-nginx \
        --create-namespace \
        --set controller.service.type=LoadBalancer \
        --set controller.service.externalIPs={$INSTANCE_IP} \
        --set controller.config.use-forwarded-headers=true \
        --set controller.config.compute-full-forwarded-for=true \
        --set controller.config.use-proxy-protocol=false \
        --wait >/dev/null 2>&1
    echo "✅ NGINX Ingress Controller installed"
fi
EOF
echo ""

# Step 5: Install cert-manager for SSL
echo "Step 5: Installing cert-manager for SSL certificates..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP << 'EOF'
# Check if cert-manager already exists
if kubectl get deployment -n cert-manager cert-manager >/dev/null 2>&1; then
    echo "✅ cert-manager already deployed"
else
    echo "📦 Installing cert-manager..."
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml >/dev/null 2>&1
    echo "⏳ Waiting for cert-manager to be ready..."
    kubectl wait --for=condition=ready pod -n cert-manager --all --timeout=300s >/dev/null 2>&1
    echo "✅ cert-manager installed and ready"
fi
EOF
echo ""

# Step 6: Create Let's Encrypt ClusterIssuer
echo "Step 6: Creating Let's Encrypt ClusterIssuer..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP << 'EOF'
# Create ClusterIssuer for Let's Encrypt
cat << 'ISSUER' | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@sophia-intel.ai
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
ISSUER
EOF
echo "✅ Let's Encrypt ClusterIssuer created"
echo ""

# Step 7: Deploy production ingress
echo "Step 7: Deploying production ingress configuration..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP << 'EOF'
# Deploy the production ingress
kubectl apply -f ~/sophia-ingress-production.yaml
echo "✅ Production ingress deployed"
EOF
echo ""

# Step 8: Check ingress status
echo "Step 8: Checking ingress deployment status..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP << 'EOF'
echo "📊 Ingress Status:"
kubectl get ingress -n sophia -o wide

echo ""
echo "🔒 TLS Certificate Status:"
kubectl get certificate -n sophia -o wide 2>/dev/null || echo "No certificates found yet"

echo ""
echo "🌐 Ingress Controller Status:"
kubectl get pods -n ingress-nginx -o wide

echo ""
echo "📋 Service Endpoints:"
kubectl get services -n sophia -o wide
EOF
echo ""

# Step 9: Wait for SSL certificate
echo "Step 9: Waiting for SSL certificate provisioning..."
echo "⏳ This may take 1-5 minutes for Let's Encrypt certificate..."
sleep 30

ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP << 'EOF'
echo "🔒 Certificate Status:"
kubectl get certificate -n sophia -o wide 2>/dev/null || echo "Certificate still provisioning..."

echo ""
echo "📊 Certificate Request Status:"
kubectl get certificaterequest -n sophia -o wide 2>/dev/null || echo "No certificate requests yet"
EOF
echo ""

# Step 10: Test domain accessibility
echo "Step 10: Testing domain accessibility..."
echo "🌐 Note: DNS propagation may take 5-30 minutes initially, 24-48 hours for full propagation"
echo ""

# Test HTTP (should redirect to HTTPS)
echo "Testing HTTP access:"
curl -s -I http://www.sophia-intel.ai | head -n 1 || echo "❌ HTTP not accessible yet (DNS may still be propagating)"

# Test HTTPS (may not work until certificate is ready)
echo ""
echo "Testing HTTPS access:"
curl -s -I https://www.sophia-intel.ai 2>/dev/null | head -n 1 || echo "❌ HTTPS not accessible yet (certificate may still be provisioning)"

echo ""
echo "🎉 Production Ingress Deployment Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Wait for DNS propagation (check with: dig www.sophia-intel.ai)"
echo "2. SSL certificate should be ready within 5-10 minutes"
echo "3. Test all endpoints after DNS propagation:"
echo "   - Main site: https://www.sophia-intel.ai"
echo "   - Health check: https://www.sophia-intel.ai/health"
echo "   - API endpoints: https://www.sophia-intel.ai/api/research"
echo ""
echo "🔧 Useful commands for monitoring:"
echo "  Check ingress: kubectl get ingress -n sophia"
echo "  Check certificates: kubectl get certificate -n sophia"
echo "  Check logs: kubectl logs -n ingress-nginx deployment/ingress-nginx-controller"
echo ""
echo "✅ Sophia AI is now configured for production at www.sophia-intel.ai!"