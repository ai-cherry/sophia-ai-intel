#!/bin/bash

# Sophia AI Monitoring Deployment Script
# This script deploys Prometheus, Grafana, AlertManager, and Loki stack

set -e

echo "🚀 Starting Sophia AI Monitoring Deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "k8s-deploy/manifests/prometheus.yaml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

cd k8s-deploy

print_status "Creating monitoring namespace..."
kubectl apply -f manifests/prometheus.yaml || print_warning "Prometheus deployment may have issues"

print_status "Deploying AlertManager..."
kubectl apply -f manifests/alertmanager.yaml || print_warning "AlertManager deployment may have issues"

print_status "Deploying Grafana..."
kubectl apply -f manifests/grafana.yaml || print_warning "Grafana deployment may have issues"

print_status "Deploying enhanced Grafana dashboards..."
kubectl apply -f manifests/grafana-enhanced-dashboard.yaml || print_warning "Enhanced dashboards may have issues"

print_status "Deploying Grafana alerting configuration..."
kubectl apply -f manifests/grafana-alerting.yaml || print_warning "Alerting configuration may have issues"

print_status "Deploying Loki for log aggregation..."
kubectl apply -f manifests/loki.yaml || print_warning "Loki deployment may have issues"

print_status "Deploying Promtail for log shipping..."
kubectl apply -f manifests/promtail.yaml || print_warning "Promtail deployment may have issues"

print_status "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n monitoring || print_warning "Prometheus deployment timeout"
kubectl wait --for=condition=available --timeout=300s deployment/alertmanager -n monitoring || print_warning "AlertManager deployment timeout"
kubectl wait --for=condition=available --timeout=300s deployment/grafana -n monitoring || print_warning "Grafana deployment timeout"

print_success "Monitoring stack deployment completed!"

echo ""
print_status "Next Steps:"
echo "1. Configure monitoring secrets:"
echo "   kubectl create secret generic monitoring-secrets -n monitoring \\"
echo "     --from-literal=SMTP_USERNAME='your-smtp-username' \\"
echo "     --from-literal=SMTP_PASSWORD='your-smtp-password' \\"
echo "     --from-literal=SLACK_WEBHOOK_URL='your-slack-webhook-url' \\"
echo "     --from-literal=WEBHOOK_URL='your-external-webhook-url' \\"
echo "     --from-literal=WEBHOOK_USERNAME='your-webhook-username' \\"
echo "     --from-literal=WEBHOOK_PASSWORD='your-webhook-password'"

echo ""
echo "2. Access Grafana:"
echo "   kubectl port-forward -n monitoring svc/grafana 3000:3000"
echo "   URL: http://localhost:3000"
echo "   Default credentials: admin / sophia2024!"

echo ""
echo "3. Access Prometheus:"
echo "   kubectl port-forward -n monitoring svc/prometheus 9090:9090"
echo "   URL: http://localhost:9090"

echo ""
echo "4. Access AlertManager:"
echo "   kubectl port-forward -n monitoring svc/alertmanager 9093:9093"
echo "   URL: http://localhost:9093"

echo ""
echo "5. Update your services with Prometheus annotations:"
echo "   Add these annotations to your service pods:"
echo "   - prometheus.io/scrape: 'true'"
echo "   - prometheus.io/port: '8080'"
echo "   - prometheus.io/path: '/metrics'"

echo ""
print_warning "IMPORTANT: Update the monitoring secrets with your actual credentials!"
print_warning "The default Grafana password should be changed in production!"

echo ""
print_success "Monitoring deployment complete! 🎉"