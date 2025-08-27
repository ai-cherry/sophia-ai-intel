#!/bin/bash

# Configuration
NAMESPACE="sophia"
SECRET_NAME="github-registry"
DOCKER_SERVER="ghcr.io" # Assuming your images are on GitHub Container Registry

# Replace with your actual Docker Hub/GitHub Container Registry credentials
DOCKER_USERNAME="your-docker-username"
DOCKER_PASSWORD="your-docker-personal-access-token"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_info "Ensuring namespace ${NAMESPACE} exists..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

log_info "Deleting existing secret ${SECRET_NAME} in ${NAMESPACE} if it exists..."
kubectl delete secret "$SECRET_NAME" -n "$NAMESPACE" --ignore-not-found

log_info "Creating image pull secret '${SECRET_NAME}' for ${DOCKER_SERVER} in namespace ${NAMESPACE}..."

if kubectl create secret docker-registry "$SECRET_NAME" \
    --docker-server="$DOCKER_SERVER" \
    --docker-username="$DOCKER_USERNAME" \
    --docker-password="$DOCKER_PASSWORD" \
    -n "$NAMESPACE"; then
    log_success "Image pull secret '${SECRET_NAME}' created successfully!"
else
    log_error "Failed to create image pull secret '${SECRET_NAME}'."
    exit 1
fi

log_info "Verification:"
kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o yaml

log_success "Image pull secret handling complete."
