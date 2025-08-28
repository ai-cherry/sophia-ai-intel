#!/bin/bash
# Build all consolidated services in waterfall approach
# This script builds each service sequentially to maximize cache efficiency

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REGISTRY=${REGISTRY:-"sophia-registry"}
BUILD_DIR="services-consolidated"

# Function definitions
log_info() {
    echo -e "${BLUE}ℹ️  INFO:${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅ SUCCESS:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠️  WARNING:${NC} $1"
}

log_error() {
    echo -e "${RED}❌ ERROR:${NC} $1"
}

# Check if service directory exists
check_service() {
    local service=$1
    if [[ ! -d "$BUILD_DIR/$service" ]]; then
        log_error "Service directory not found: $BUILD_DIR/$service"
        return 1
    fi
    return 0
}

# Build single service
build_service() {
    local service=$1
    log_info "Building consolidated service: $service"
    
    if ! check_service "$service"; then
        return 1
    fi
    
    # Build with optimized caching
    docker build \
        --build-arg SERVICE_NAME="$service" \
        -f dockerfiles/Dockerfile.python-ml \
        -t "$REGISTRY/$service:latest" \
        --progress=plain \
        . || {
        log_error "Failed to build $service"
        return 1
    }
    
    # Verify build
    if docker images | grep -q "$REGISTRY/$service"; then
        local size=$(docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep "$REGISTRY/$service" | awk '{print $3}')
        log_success "$service built successfully (Size: $size)"
        return 0
    else
        log_error "$service build verification failed"
        return 1
    fi
}

# Main build function
build_all_services() {
    local services=(
        "sophia-ai-core"
        "sophia-business-intel"
        "sophia-communications" 
        "sophia-development"
        "sophia-orchestration"
        "sophia-infrastructure"
    )
    
    local built_count=0
    local failed_services=()
    
    log_info "Starting consolidated services build (waterfall approach)"
    log_info "Building ${#services[@]} services with shared ML dependencies"
    echo
    
    for service in "${services[@]}"; do
        # Check if already built
        if docker images | grep -q "$REGISTRY/$service"; then
            log_success "$service already built - skipping"
            ((built_count++))
            continue
        fi
        
        log_info "[$((built_count + 1))/${#services[@]}] Building $service..."
        
        if build_service "$service"; then
            ((built_count++))
            log_success "Progress: $built_count/${#services[@]} services completed"
        else
            failed_services+=("$service")
            log_error "Failed to build $service"
        fi
        
        echo "----------------------------------------"
    done
    
    # Summary
    echo
    log_info "=== BUILD SUMMARY ==="
    echo "✅ Successfully built: $built_count/${#services[@]} services"
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        echo "❌ Failed services: ${failed_services[*]}"
        return 1
    else
        log_success "🎉 All consolidated services built successfully!"
        
        # Show final images
        echo
        log_info "Built Images:"
        docker images | grep "$REGISTRY" | head -10
        
        echo
        log_info "Total consolidated architecture: 12→6 services (50% reduction)"
        log_success "Ready for Kubernetes deployment!"
        return 0
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [service_name|all]"
    echo
    echo "Available services:"
    echo "  sophia-ai-core        - AI agents, context, research"
    echo "  sophia-business-intel - CRM, Salesforce, HubSpot"
    echo "  sophia-communications - Slack, Gong integrations"
    echo "  sophia-development    - GitHub, Lambda services"
    echo "  sophia-orchestration  - Workflow management"
    echo "  sophia-infrastructure - System utilities"
    echo "  all                   - Build all services"
    echo
}

# Main execution
main() {
    local service_name=${1:-"all"}
    
    echo "========================================="
    echo "   SOPHIA AI CONSOLIDATED BUILD         "
    echo "========================================="
    echo
    
    case $service_name in
        "all")
            build_all_services
            ;;
        "sophia-ai-core"|"sophia-business-intel"|"sophia-communications"|"sophia-development"|"sophia-orchestration"|"sophia-infrastructure")
            build_service "$service_name"
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            log_error "Invalid service name: $service_name"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"