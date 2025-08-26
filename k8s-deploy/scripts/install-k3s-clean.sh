#!/bin/bash
set -e

# Sophia AI - Clean Slate K3s Installation Script
# This script removes Docker Compose and installs K3s on Lambda Labs

echo "======================================"
echo "🧹 Sophia AI - Clean K3s Installation"
echo "======================================"
echo ""

# Configuration
INSTANCE_IP="192.222.51.223"
K3S_VERSION="v1.29.0+k3s1"
NAMESPACE="sophia"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Stop and remove Docker Compose services
cleanup_docker_compose() {
    log_info "Step 1: Cleaning up Docker Compose services..."
    
    if command -v docker-compose &> /dev/null; then
        log_info "Stopping all Docker Compose services..."
        docker-compose down -v --remove-orphans 2>/dev/null || true
        
        log_info "Pruning Docker resources..."
        docker system prune -af --volumes || true
        
        log_success "Docker Compose cleanup completed"
    else
        log_warning "Docker Compose not found, skipping cleanup"
    fi
}

# Step 2: Install K3s
install_k3s() {
    log_info "Step 2: Installing K3s..."
    
    # Check if K3s already installed
    if command -v k3s &> /dev/null; then
        log_warning "K3s already installed, upgrading..."
        curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="$K3S_VERSION" sh -
    else
        log_info "Installing K3s version $K3S_VERSION..."
        curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="$K3S_VERSION" sh -s - \
            --write-kubeconfig-mode 644 \
            --disable traefik \
            --disable servicelb
    fi
    
    # Wait for K3s to be ready
    log_info "Waiting for K3s to be ready..."
    sleep 30
    
    # Verify installation
    if kubectl get nodes &> /dev/null; then
        log_success "K3s installed successfully"
        kubectl get nodes
    else
        log_error "K3s installation failed"
        exit 1
    fi
}

# Step 3: Install NVIDIA device plugin for GPU support
install_nvidia_plugin() {
    log_info "Step 3: Installing NVIDIA device plugin for GPU support..."
    
    # Check if NVIDIA GPU is available
    if nvidia-smi &> /dev/null; then
        log_info "NVIDIA GPU detected, installing device plugin..."
        
        # Install NVIDIA device plugin
        kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml || true
        
        # Wait for plugin to be ready
        sleep 20
        
        # Verify GPU is available
        if kubectl get nodes -o json | grep -q "nvidia.com/gpu"; then
            log_success "NVIDIA GPU plugin installed successfully"
            kubectl describe nodes | grep -A 5 "nvidia.com/gpu"
        else
            log_warning "GPU plugin installed but GPU not detected in K8s"
        fi
    else
        log_warning "No NVIDIA GPU detected, skipping GPU plugin"
    fi
}

# Step 4: Create Sophia namespace and basic resources
setup_namespace() {
    log_info "Step 4: Setting up Sophia namespace..."
    
    # Create namespace
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Set default namespace
    kubectl config set-context --current --namespace=$NAMESPACE
    
    log_success "Namespace '$NAMESPACE' created and set as default"
}

# Step 5: Install Helm package manager
install_helm() {
    log_info "Step 5: Installing Helm package manager..."
    
    if command -v helm &> /dev/null; then
        log_warning "Helm already installed"
    else
        curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    fi
    
    # Add common repositories
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm repo add jetstack https://charts.jetstack.io
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm repo update
    
    log_success "Helm installed and repositories added"
}

# Step 6: Create local storage class
setup_storage() {
    log_info "Step 6: Setting up local storage class..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-path
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: rancher.io/local-path
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
EOF
    
    log_success "Local storage class configured"
}

# Step 7: Save kubeconfig for easy access
save_kubeconfig() {
    log_info "Step 7: Saving kubeconfig..."
    
    # Copy kubeconfig to user directory
    mkdir -p ~/.kube
    sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
    sudo chown $(id -u):$(id -g) ~/.kube/config
    
    # Also save in k8s-deploy directory
    cp ~/.kube/config k8s-deploy/kubeconfig
    
    log_success "Kubeconfig saved to ~/.kube/config and k8s-deploy/kubeconfig"
}

# Step 8: Verify cluster health
verify_cluster() {
    log_info "Step 8: Verifying cluster health..."
    
    echo ""
    echo "🔍 Cluster Status:"
    kubectl cluster-info
    
    echo ""
    echo "📦 Nodes:"
    kubectl get nodes -o wide
    
    echo ""
    echo "🚀 Namespaces:"
    kubectl get namespaces
    
    echo ""
    echo "💾 Storage Classes:"
    kubectl get storageclass
    
    if nvidia-smi &> /dev/null; then
        echo ""
        echo "🎮 GPU Status:"
        kubectl describe nodes | grep -A 5 "nvidia.com/gpu" || echo "GPU not yet visible in K8s"
    fi
    
    log_success "K3s cluster is ready!"
}

# Main execution
main() {
    log_info "Starting clean K3s installation on Lambda Labs..."
    log_info "This will remove Docker Compose and install K3s"
    echo ""
    
    # Confirm with user
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "Installation cancelled"
        exit 1
    fi
    
    # Run installation steps
    cleanup_docker_compose
    install_k3s
    install_nvidia_plugin
    setup_namespace
    install_helm
    setup_storage
    save_kubeconfig
    verify_cluster
    
    echo ""
    echo "======================================"
    log_success "🎉 K3s installation completed!"
    echo "======================================"
    echo ""
    echo "Next steps:"
    echo "1. Run: export KUBECONFIG=~/.kube/config"
    echo "2. Test: kubectl get pods -A"
    echo "3. Continue with PROMPT 2: Convert services to K8s manifests"
    echo ""
}

# Run main function
main "$@"
