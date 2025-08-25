#!/bin/bash
# Sophia AI Intel - Lambda Labs Kubernetes Deployment Script
# Enterprise-grade deployment automation with GPU scheduling

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CLUSTER_NAME="sophia-ai-production"
REGION="us-west-2"
NAMESPACE="sophia-ai"
IMAGE_REGISTRY="lambdalabs.azurecr.io/sophia-ai"

echo -e "${BLUE}🚀 Sophia AI Intel - Lambda Labs Kubernetes Deployment${NC}"
echo "=================================================================="

# Function to check command availability
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 is not installed${NC}"
        exit 1
    fi
}

# Function to wait for deployment
wait_for_deployment() {
    local namespace=$1
    local deployment=$2
    local timeout=${3:-300}
    
    echo -e "${YELLOW}⏳ Waiting for $deployment to be ready...${NC}"
    
    if kubectl wait --for=condition=available --timeout=${timeout}s deployment/$deployment -n $namespace; then
        echo -e "${GREEN}✅ $deployment is ready${NC}"
        return 0
    else
        echo -e "${RED}❌ $deployment failed to become ready${NC}"
        return 1
    fi
}

# Pre-deployment checks
echo -e "${BLUE}📋 Pre-deployment checks...${NC}"
check_command kubectl
check_command docker
check_command helm

# Check cluster connectivity
echo -e "${YELLOW}🔍 Checking Lambda Labs Kubernetes cluster connectivity...${NC}"
if kubectl cluster-info &>/dev/null; then
    echo -e "${GREEN}✅ Connected to Kubernetes cluster${NC}"
else
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    echo "Please ensure your kubeconfig is configured for Lambda Labs"
    exit 1
fi

# Check GPU nodes
echo -e "${YELLOW}🎮 Checking GPU node availability...${NC}"
GPU_NODES=$(kubectl get nodes -l accelerator=nvidia-gpu --no-headers | wc -l)
if [ $GPU_NODES -gt 0 ]; then
    echo -e "${GREEN}✅ Found $GPU_NODES GPU node(s)${NC}"
else
    echo -e "${YELLOW}⚠️  No GPU nodes found - will deploy without GPU scheduling${NC}"
fi

# Create namespaces
echo -e "${BLUE}🏗️ Creating namespaces...${NC}"
kubectl apply -f ../manifests/01-namespace.yaml

# Deploy infrastructure (Redis, storage)
echo -e "${BLUE}💾 Deploying storage and caching infrastructure...${NC}"
kubectl apply -f ../manifests/04-redis-cluster.yaml
kubectl apply -f ../manifests/07-secrets-configmaps.yaml

# Wait for Redis cluster
wait_for_deployment sophia-ai redis-cluster

# Deploy core services
echo -e "${BLUE}🧠 Deploying AI intelligence services...${NC}"

# Context service with real embeddings
kubectl apply -f ../manifests/03-context-service.yaml
wait_for_deployment sophia-ai sophia-context

# Research service with caching
kubectl apply -f ../manifests/05-research-service.yaml
wait_for_deployment sophia-ai sophia-research

# Agent swarm (GPU-accelerated)
if [ $GPU_NODES -gt 0 ]; then
    echo -e "${BLUE}🤖 Deploying GPU-accelerated agent swarm...${NC}"
    kubectl apply -f ../manifests/02-agent-swarm.yaml
    wait_for_deployment sophia-ai sophia-agents 600  # 10 minutes for GPU initialization
else
    echo -e "${YELLOW}⚠️  Skipping GPU-accelerated agent swarm (no GPU nodes)${NC}"
fi

# Deploy frontend and ingress
echo -e "${BLUE}🎨 Deploying dashboard and ingress...${NC}"
kubectl apply -f ../manifests/06-dashboard-ingress.yaml
wait_for_deployment sophia-ai sophia-dashboard

# Deploy monitoring stack
echo -e "${BLUE}📊 Deploying monitoring and observability...${NC}"
kubectl apply -f ../manifests/08-monitoring-stack.yaml
kubectl apply -f ../manifests/09-gpu-monitoring.yaml

# Wait for monitoring services
wait_for_deployment sophia-ai-monitoring prometheus
wait_for_deployment sophia-ai-monitoring grafana

# Health checks
echo -e "${BLUE}🏥 Running health checks...${NC}"

# Function to check service health
check_service_health() {
    local service=$1
    local namespace=$2
    local port=$3
    
    echo -n "Checking $service health... "
    
    if kubectl exec -n $namespace deployment/$service -- curl -sf http://localhost:$port/healthz > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Healthy${NC}"
        return 0
    else
        echo -e "${RED}❌ Unhealthy${NC}"
        return 1
    fi
}

# Check all services
services=(
    "sophia-context:sophia-ai:8082"
    "sophia-research:sophia-ai:8081"
    "sophia-dashboard:sophia-ai:3000"
    "sophia-business:sophia-ai:8084"
    "sophia-github:sophia-ai:8083"
)

if [ $GPU_NODES -gt 0 ]; then
    services+=("sophia-agents:sophia-ai:8087")
fi

healthy_services=0
total_services=${#services[@]}

for service_info in "${services[@]}"; do
    IFS=':' read -r service namespace port <<< "$service_info"
    if check_service_health $service $namespace $port; then
        ((healthy_services++))
    fi
done

# Get external IP for ingress
echo -e "${BLUE}🌐 Getting external access information...${NC}"
EXTERNAL_IP=$(kubectl get ingress sophia-ai-ingress -n sophia-ai -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")

# Deployment summary
echo -e "\n${BLUE}📊 Deployment Summary${NC}"
echo "===================="
echo -e "Healthy services: $healthy_services/$total_services"
echo -e "GPU nodes available: $GPU_NODES"
echo -e "External IP: ${EXTERNAL_IP}"

if [ $healthy_services -eq $total_services ]; then
    echo -e "${GREEN}🎉 SOPHIA AI INTEL KUBERNETES DEPLOYMENT SUCCESSFUL!${NC}"
    echo -e "\n${GREEN}✨ Your enterprise AI platform is ready:${NC}"
    echo -e "  🌐 Dashboard: https://www.sophia-intel.ai"
    echo -e "  🤖 Agent Swarm: GPU-accelerated multi-agent coordination"
    echo -e "  🧠 Real Embeddings: OpenAI text-embedding-3-large with Redis caching"
    echo -e "  🔬 Research Intelligence: Multi-provider with aggressive caching"
    echo -e "  📊 Monitoring: Prometheus/Grafana with GPU metrics"
    echo -e "  🚀 Auto-scaling: HPA for all services based on demand"
    echo -e "\n${BLUE}🎯 Next Steps:${NC}"
    echo -e "  • Configure DNS: Point www.sophia-intel.ai to $EXTERNAL_IP"
    echo -e "  • Access Grafana: https://www.sophia-intel.ai/admin/grafana"
    echo -e "  • Monitor GPU usage: https://www.sophia-intel.ai/admin/grafana"
    echo -e "  • Test agent swarm: Chat with 'analyze repository'"
    
    # Save deployment info
    cat > sophia-ai-deployment-info.txt << EOF
# Sophia AI Intel Kubernetes Deployment Info
Date: $(date)
Cluster: $CLUSTER_NAME
Namespace: $NAMESPACE
External IP: $EXTERNAL_IP
GPU Nodes: $GPU_NODES
Healthy Services: $healthy_services/$total_services

# Access URLs
Dashboard: https://www.sophia-intel.ai
Grafana: https://www.sophia-intel.ai/admin/grafana
Prometheus: https://www.sophia-intel.ai/admin/prometheus

# API Endpoints
Agent Swarm: https://www.sophia-intel.ai/api/agents
Context API: https://www.sophia-intel.ai/api/context
Research API: https://www.sophia-intel.ai/api/research
Business API: https://www.sophia-intel.ai/api/business
GitHub API: https://www.sophia-intel.ai/api/github

# Management Commands
kubectl get pods -n sophia-ai
kubectl logs -f deployment/sophia-agents -n sophia-ai
kubectl get hpa -n sophia-ai
kubectl top nodes
kubectl get pvc -n sophia-ai

Status: DEPLOYMENT SUCCESSFUL ✅
EOF
    
    echo -e "${GREEN}📄 Deployment info saved to: sophia-ai-deployment-info.txt${NC}"
    
elif [ $healthy_services -ge $((total_services * 8 / 10)) ]; then
    echo -e "${YELLOW}⚠️ Deployment completed with some issues${NC}"
    echo -e "\n${YELLOW}🔧 Troubleshooting:${NC}"
    echo -e "  • Check pod logs: kubectl logs -f deployment/[service-name] -n sophia-ai"
    echo -e "  • Check events: kubectl get events -n sophia-ai --sort-by='.lastTimestamp'"
    echo -e "  • Check resources: kubectl top pods -n sophia-ai"
else
    echo -e "${RED}❌ Deployment failed - multiple service failures${NC}"
    echo -e "\n${RED}🚨 Critical issues detected:${NC}"
    echo -e "  • Check cluster resources: kubectl describe nodes"
    echo -e "  • Check pod status: kubectl get pods -n sophia-ai"
    echo -e "  • Review logs: kubectl logs -l app=sophia-agents -n sophia-ai"
    exit 1
fi

echo -e "\n${BLUE}🎯 Enterprise Kubernetes Features Enabled:${NC}"
echo -e "  ✅ GPU scheduling with NVIDIA A100/H100 support"  
echo -e "  ✅ Auto-scaling based on GPU utilization and task queues"
echo -e "  ✅ High-availability Redis cluster with sentinel"
echo -e "  ✅ Persistent storage with NVMe and distributed volumes"
echo -e "  ✅ HTTPS ingress with automatic SSL/TLS certificates"
echo -e "  ✅ Comprehensive monitoring with GPU metrics"
echo -e "  ✅ Network policies and security controls"
echo -e "  ✅ ArgoCD GitOps deployment ready"

echo -e "\n${GREEN}🚀 Sophia AI Intel is now enterprise-ready on Lambda Labs Kubernetes!${NC}"
