#!/bin/bash
# Sophia AI - Check Deployment Status on Lambda Labs

INSTANCE_IP="192.222.51.223"
SSH_KEY_FILE="lambda-ssh-key"

echo "======================================"
echo "🔍 Checking Sophia AI Deployment Status"
echo "======================================"
echo "Target: $INSTANCE_IP"
echo ""

# Test SSH connection
echo "Testing SSH connection..."
if ! ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "echo 'SSH connection successful'" 2>/dev/null; then
    echo "❌ SSH connection failed"
    exit 1
fi
echo "✅ SSH connection successful"
echo ""

# Check K3s status
echo "🔍 Checking K3s cluster status..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "kubectl get nodes -o wide" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ K3s cluster is running"
else
    echo "❌ K3s cluster not responding"
fi
echo ""

# Check pods status
echo "🔍 Checking Kubernetes pods..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "kubectl get pods -o wide" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Kubernetes pods accessible"
else
    echo "❌ Kubernetes pods not accessible"
fi
echo ""

# Check services
echo "🔍 Checking Kubernetes services..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "kubectl get services -o wide" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Kubernetes services accessible"
else
    echo "❌ Kubernetes services not accessible"
fi
echo ""

# Check ingress
echo "🔍 Checking ingress controllers..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "kubectl get ingress -o wide" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Ingress accessible"
else
    echo "❌ Ingress not accessible"
fi
echo ""

# Test endpoints
echo "🔍 Testing service endpoints..."
echo ""
echo "Testing main application health..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://$INSTANCE_IP/health || echo "Main app not responding"

echo ""
echo "Testing Grafana..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://$INSTANCE_IP:3000 || echo "Grafana not responding"

echo ""
echo "Testing Prometheus..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://$INSTANCE_IP:9090 || echo "Prometheus not responding"

echo ""
echo "======================================"
echo "📊 Deployment Status Summary"
echo "======================================"
echo ""

# Check if deployment is complete
DEPLOYMENT_COMPLETE=true

# Check if main services are running
if ! curl -s http://$INSTANCE_IP/health > /dev/null 2>&1; then
    DEPLOYMENT_COMPLETE=false
    echo "❌ Main application not responding"
else
    echo "✅ Main application responding"
fi

if ! curl -s http://$INSTANCE_IP:3000 > /dev/null 2>&1; then
    echo "❌ Grafana not responding"
else
    echo "✅ Grafana responding"
fi

if ! curl -s http://$INSTANCE_IP:9090 > /dev/null 2>&1; then
    echo "❌ Prometheus not responding"
else
    echo "✅ Prometheus responding"
fi

echo ""
if [ "$DEPLOYMENT_COMPLETE" = true ]; then
    echo "🎉 DEPLOYMENT STATUS: COMPLETE"
    echo ""
    echo "🌐 Access URLs:"
    echo "- Main Application: http://$INSTANCE_IP"
    echo "- Grafana (Monitoring): http://$INSTANCE_IP:3000"
    echo "- Prometheus: http://$INSTANCE_IP:9090"
else
    echo "⏳ DEPLOYMENT STATUS: IN PROGRESS"
    echo "Please wait for deployment to complete..."
fi

echo ""
echo "======================================"