#!/bin/bash
# Sophia AI - Fix Kubeconfig Permissions on Lambda Labs

INSTANCE_IP="192.222.51.223"
SSH_KEY_FILE="lambda-ssh-key"

echo "======================================"
echo "🔧 Fixing Kubeconfig Permissions"
echo "======================================"
echo "Target: $INSTANCE_IP"
echo ""

# Fix kubeconfig permissions
echo "🔍 Fixing kubeconfig permissions..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "sudo chmod 644 /etc/rancher/k3s/k3s.yaml"

# Copy kubeconfig to user directory
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "mkdir -p ~/.kube"
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config"
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "sudo chown ubuntu:ubuntu ~/.kube/config"

# Verify kubectl works
echo "🔍 Verifying kubectl access..."
ssh -o StrictHostKeyChecking=no -i "$SSH_KEY_FILE" ubuntu@$INSTANCE_IP "kubectl get nodes"

if [ $? -eq 0 ]; then
    echo "✅ Kubeconfig permissions fixed successfully"
else
    echo "❌ Kubeconfig fix failed"
    exit 1
fi

echo ""
echo "======================================"
echo "✅ Kubeconfig permissions fixed!"
echo "======================================"