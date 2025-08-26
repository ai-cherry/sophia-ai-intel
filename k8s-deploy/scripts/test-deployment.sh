#!/bin/bash
set -euo pipefail

# Sophia AI Deployment Test Script

LAMBDA_IP="192.222.51.223"
LAMBDA_USER="ubuntu"

echo "=== Sophia AI Deployment Test ==="
echo

# Function to execute commands on remote server
remote_exec() {
    ssh -o StrictHostKeyChecking=no ${LAMBDA_USER}@${LAMBDA_IP} "$@"
}

# Test 1: Check all pods are running
echo "Test 1: Checking pod status..."
remote_exec "kubectl get pods -n sophia -o wide"
echo

# Test 2: Check all services
echo "Test 2: Checking services..."
remote_exec "kubectl get services -n sophia"
echo

# Test 3: Check ingress
echo "Test 3: Checking ingress configuration..."
remote_exec "kubectl get ingress -n sophia"
remote_exec "kubectl describe ingress sophia-ingress -n sophia"
echo

# Test 4: Check persistent volumes
echo "Test 4: Checking persistent volumes..."
remote_exec "kubectl get pv"
remote_exec "kubectl get pvc -n sophia"
echo

# Test 5: Check logs for errors
echo "Test 5: Checking logs for errors..."
echo "Redis logs:"
remote_exec "kubectl logs -n sophia deployment/redis --tail=20"
echo
echo "Dashboard logs:"
remote_exec "kubectl logs -n sophia deployment/sophia-dashboard --tail=20"
echo
echo "MCP Research logs:"
remote_exec "kubectl logs -n sophia deployment/mcp-research --tail=20"
echo

# Test 6: Test service connectivity
echo "Test 6: Testing service connectivity..."
# Test Redis connectivity
remote_exec "kubectl run -it --rm redis-test -n sophia --image=redis:alpine --restart=Never -- redis-cli -h redis-service ping" || true
echo

# Test 7: GPU availability
echo "Test 7: Checking GPU availability..."
remote_exec "kubectl describe nodes | grep -i nvidia"
echo

# Test 8: Test endpoints
echo "Test 8: Testing HTTP endpoints..."
echo "Testing ingress controller..."
remote_exec "curl -k -I https://localhost 2>/dev/null | head -n 1" || true
echo
echo "Testing from outside (requires DNS to be configured):"
curl -k -I https://www.sophia-intel.ai 2>/dev/null | head -n 1 || echo "DNS not yet configured or service not accessible"
echo

# Test 9: Resource usage
echo "Test 9: Checking resource usage..."
remote_exec "kubectl top nodes" || echo "Metrics server not installed"
remote_exec "kubectl top pods -n sophia" || echo "Metrics server not installed"
echo

# Summary
echo "=== Test Summary ==="
echo "1. Check that all pods show 'Running' status"
echo "2. Verify services have ClusterIP assigned"
echo "3. Confirm ingress has an address/IP"
echo "4. Ensure PVCs are 'Bound' status"
echo "5. Look for any errors in the logs"
echo "6. Verify Redis responds with 'PONG'"
echo "7. Confirm GPU resources are available"
echo "8. Test HTTP endpoints return valid responses"
echo
echo "To continuously monitor pods:"
echo "ssh ${LAMBDA_USER}@${LAMBDA_IP} watch kubectl get pods -n sophia"
