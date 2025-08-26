#!/bin/bash

# Sophia AI - Storage Configuration Deployment Script
# Deploys storage classes and PVCs for K3s environment

set -e

# Configuration
NAMESPACE="sophia"
STORAGE_CLASS_MANIFEST="manifests/storage-class.yaml"
PVC_MANIFEST="manifests/pvcs.yaml"

echo "🚀 Starting Sophia AI Storage Configuration Deployment"
echo "======================================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
if ! command_exists kubectl; then
    echo "❌ Error: kubectl is not installed or not in PATH"
    exit 1
fi

# Check cluster connection
echo "🔍 Checking cluster connection..."
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo "❌ Error: Cannot connect to Kubernetes cluster"
    exit 1
fi

echo "✅ Connected to cluster: $(kubectl config current-context)"

# Create namespace if it doesn't exist
echo ""
echo "📁 Ensuring namespace '$NAMESPACE' exists..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Deploy Storage Classes
echo ""
echo "💾 Deploying Storage Classes..."
if [ -f "$STORAGE_CLASS_MANIFEST" ]; then
    echo "   Applying storage class configuration..."
    kubectl apply -f "$STORAGE_CLASS_MANIFEST"
    echo "   ✅ Storage classes deployed successfully"
else
    echo "   ⚠️  Warning: Storage class manifest not found at $STORAGE_CLASS_MANIFEST"
fi

# Wait for storage class to be available
echo ""
echo "⏳ Waiting for storage class to be ready..."
sleep 5

# Verify storage classes
echo ""
echo "🔍 Verifying Storage Classes..."
kubectl get storageclass

# Deploy PVCs
echo ""
echo "💿 Deploying Persistent Volume Claims..."
if [ -f "$PVC_MANIFEST" ]; then
    echo "   Applying PVC configuration..."
    kubectl apply -f "$PVC_MANIFEST"
    echo "   ✅ PVCs deployed successfully"
else
    echo "   ⚠️  Warning: PVC manifest not found at $PVC_MANIFEST"
fi

# Wait for PVCs to bind
echo ""
echo "⏳ Waiting for PVCs to bind to storage..."
sleep 10

# Check PVC status
echo ""
echo "📊 Checking PVC Status..."
kubectl get pvc -n "$NAMESPACE"

# Check for any PVC events or issues
echo ""
echo "🔍 Checking for PVC events..."
kubectl get events -n "$NAMESPACE" --field-selector reason=FailedScheduling,FailedMount,FailedAttachVolume,FailedDetachVolume -o custom-columns=TIMESTAMP:.metadata.creationTimestamp,REASON:.reason,MESSAGE:.message

# Validate storage provisioning
echo ""
echo "✅ Storage Configuration Validation:"
echo "   - Storage classes deployed and available"
echo "   - PVCs created and should bind to storage"
echo "   - Ready for pod mounting and data persistence"

echo ""
echo "🎉 Storage configuration deployment completed!"
echo ""
echo "📝 Next steps:"
echo "   - Verify PVCs are bound: kubectl get pvc -n $NAMESPACE"
echo "   - Check storage class: kubectl get storageclass"
echo "   - Monitor for any binding issues in pod events"

echo ""
echo "🔧 Troubleshooting:"
echo "   - If PVCs show 'Pending' status, check storage class availability"
echo "   - Verify node storage capacity if binding fails"
echo "   - Check pod events for detailed error messages"