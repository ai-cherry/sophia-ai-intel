#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 **DEPLOYING COMPLETE SOPHIA AI APPLICATION TO www.sophia-intel.ai**${NC}"
echo -e "${BLUE}================================================================${NC}"

# Configuration
REGISTRY="sophia-registry"
DASHBOARD_IMAGE="$REGISTRY/sophia-dashboard:latest"

# Step 1: Build Frontend Dashboard
echo -e "\n${YELLOW}📦 Building Frontend Dashboard...${NC}"
cd apps/sophia-dashboard

# Install dependencies
echo -e "${BLUE}Installing npm dependencies...${NC}"
npm ci

# Build the application
echo -e "${BLUE}Building Next.js application...${NC}"
npm run build

# Build Docker image
echo -e "${BLUE}Building Docker image...${NC}"
docker build -t $DASHBOARD_IMAGE .

echo -e "${GREEN}✅ Frontend dashboard built successfully!${NC}"

# Step 2: Save and transfer image to Lambda Labs k3s
echo -e "\n${BLUE}📤 Preparing image for Lambda Labs deployment...${NC}"
docker save $DASHBOARD_IMAGE -o sophia-dashboard-image.tar
echo -e "${GREEN}✅ Dashboard image saved for deployment!${NC}"

# Transfer to Lambda Labs and load into k3s
echo -e "${BLUE}Transferring and loading image into remote k3s...${NC}"
scp -o StrictHostKeyChecking=no -i lambda_ssh_key.pem sophia-dashboard-image.tar ubuntu@192.222.51.223:/tmp/
ssh -o StrictHostKeyChecking=no -i lambda_ssh_key.pem ubuntu@192.222.51.223 "sudo k3s ctr images import /tmp/sophia-dashboard-image.tar && rm /tmp/sophia-dashboard-image.tar"
rm sophia-dashboard-image.tar
echo -e "${GREEN}✅ Dashboard image loaded into Lambda Labs k3s!${NC}"

# Return to root directory
cd ../..

# Step 3: Deploy all services including dashboard
echo -e "\n${YELLOW}🔧 Deploying Complete Application Stack...${NC}"

# Set kubeconfig for Lambda Labs
export KUBECONFIG=./kubeconfig_lambda.yaml

# Create namespace if it doesn't exist
kubectl create namespace sophia --dry-run=client -o yaml | kubectl apply -f -

# Deploy consolidated backend services
echo -e "${BLUE}Deploying backend services...${NC}"
kubectl apply -f k8s-deploy/manifests/consolidated/sophia-ai-core.yaml
kubectl apply -f k8s-deploy/manifests/consolidated/sophia-business-intel.yaml
kubectl apply -f k8s-deploy/manifests/consolidated/sophia-communications.yaml
kubectl apply -f k8s-deploy/manifests/consolidated/sophia-development.yaml
kubectl apply -f k8s-deploy/manifests/consolidated/sophia-orchestration.yaml
kubectl apply -f k8s-deploy/manifests/consolidated/sophia-infrastructure.yaml

# Deploy frontend dashboard
echo -e "${BLUE}Deploying frontend dashboard...${NC}"
kubectl apply -f k8s-deploy/manifests/consolidated/sophia-dashboard.yaml

# Deploy ingress for www.sophia-intel.ai
echo -e "${BLUE}Deploying application ingress...${NC}"
kubectl apply -f k8s-deploy/manifests/consolidated/www-sophia-intel-ai-ingress.yaml

# Step 4: Wait for deployments
echo -e "\n${YELLOW}⏳ Waiting for deployments to be ready...${NC}"

# Wait for backend services
for service in sophia-ai-core sophia-business-intel sophia-communications sophia-development sophia-orchestration sophia-infrastructure; do
    echo -e "${BLUE}Waiting for $service...${NC}"
    kubectl wait --for=condition=available --timeout=300s deployment/$service -n sophia
done

# Wait for frontend
echo -e "${BLUE}Waiting for sophia-dashboard...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/sophia-dashboard -n sophia

# Step 5: Display status
echo -e "\n${GREEN}🎉 **DEPLOYMENT COMPLETE!**${NC}"
echo -e "${GREEN}================================${NC}"

echo -e "\n${BLUE}📊 Deployment Status:${NC}"
kubectl get deployments -n sophia
echo
kubectl get services -n sophia
echo
kubectl get ingress -n sophia

echo -e "\n${YELLOW}🌐 **APPLICATION ACCESS:**${NC}"
echo -e "${GREEN}Main Application: https://www.sophia-intel.ai${NC}"
echo -e "${GREEN}Dashboard:       https://www.sophia-intel.ai${NC}"
echo -e "${GREEN}Chat Interface:  https://www.sophia-intel.ai/chat${NC}"
echo -e "${GREEN}Agent Factory:   https://www.sophia-intel.ai/agent-factory${NC}"
echo -e "${GREEN}Jobs Panel:      https://www.sophia-intel.ai/jobs${NC}"

echo -e "\n${YELLOW}🔧 **API ENDPOINTS:**${NC}"
echo -e "${GREEN}AI Core API:           https://www.sophia-intel.ai/api/ai${NC}"
echo -e "${GREEN}Chat API:              https://www.sophia-intel.ai/api/chat${NC}"
echo -e "${GREEN}Business Intelligence: https://www.sophia-intel.ai/api/business${NC}"
echo -e "${GREEN}Communications:        https://www.sophia-intel.ai/api/communications${NC}"
echo -e "${GREEN}Development:           https://www.sophia-intel.ai/api/development${NC}"
echo -e "${GREEN}Health Check:          https://www.sophia-intel.ai/health${NC}"

echo -e "\n${BLUE}📝 **NEXT STEPS:**${NC}"
echo "1. Configure DNS to point www.sophia-intel.ai to 192.222.51.223 (Lambda Labs IP)"
echo "2. Install cert-manager and configure SSL certificates"
echo "3. Test all application components"
echo "4. Configure monitoring and alerting"

echo -e "\n${YELLOW}🌟 **LAMBDA LABS DEPLOYMENT:**${NC}"
echo -e "Server: ${GREEN}192.222.51.223${NC} (GH200 GPU Instance)"
echo -e "K3s Cluster: ${GREEN}Running on Lambda Labs${NC}"
echo -e "Services: ${GREEN}6 Consolidated Backend + 1 Frontend${NC}"

echo -e "\n${GREEN}🎯 **SOPHIA AI PLATFORM DEPLOYED SUCCESSFULLY TO LAMBDA LABS!**${NC}"
echo -e "Visit ${YELLOW}https://www.sophia-intel.ai${NC} to access your AI platform!"
echo -e "Direct IP access (for testing): ${YELLOW}http://192.222.51.223${NC}"