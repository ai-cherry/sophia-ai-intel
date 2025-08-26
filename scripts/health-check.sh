#!/bin/bash
# Sophia AI - Comprehensive Health Check Script
# Tests all services and provides detailed health status

echo "========================================="
echo "🏥 Sophia AI Health Check"
echo "========================================="

# Configuration
SERVICES=(
    "localhost:8080:agno-coordinator"
    "localhost:8000:agno-teams"
    "localhost:8001:mcp-agents"
    "localhost:8005:mcp-context"
    "localhost:8004:mcp-github"
    "localhost:8002:mcp-hubspot"
    "localhost:8003:mcp-business"
    "localhost:8000:orchestrator"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to test service health
test_service() {
    local endpoint="$1"
    local name="$2"

    echo ""
    echo "Testing $name ($endpoint)..."

    # Test basic connectivity
    if curl -s -f "$endpoint/health" >/dev/null 2>&1; then
        log_success "$name health endpoint responding"
        return 0
    elif curl -s -f "$endpoint/" >/dev/null 2>&1; then
        log_warning "$name responding (no health endpoint)"
        return 0
    else
        log_error "$name not responding"
        return 1
    fi
}

# Function to test monitoring stack
test_monitoring() {
    echo ""
    echo "Testing monitoring stack..."

    # Test Grafana
    if curl -s -f http://localhost:3000 >/dev/null 2>&1; then
        log_success "Grafana responding on port 3000"
    else
        log_warning "Grafana not responding on port 3000"
    fi

    # Test Prometheus
    if curl -s -f http://localhost:9090 >/dev/null 2>&1; then
        log_success "Prometheus responding on port 9090"
    else
        log_warning "Prometheus not responding on port 9090"
    fi
}

# Function to test database connectivity
test_databases() {
    echo ""
    echo "Testing database connectivity..."

    # Test Redis
    if redis-cli ping >/dev/null 2>&1; then
        log_success "Redis connection successful"
    else
        log_error "Redis connection failed"
    fi

    # Test Qdrant
    if curl -s -f http://localhost:6333/health >/dev/null 2>&1; then
        log_success "Qdrant connection successful"
    else
        log_error "Qdrant connection failed"
    fi

    # Note: Neon would require actual connection string
    log_info "Neon PostgreSQL test requires actual connection string"
}

# Function to test system resources
test_system_resources() {
    echo ""
    echo "Testing system resources..."

    # CPU usage
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    if (( $(echo "$CPU_USAGE < 80" | bc -l) )); then
        log_success "CPU usage: ${CPU_USAGE}%"
    else
        log_warning "High CPU usage: ${CPU_USAGE}%"
    fi

    # Memory usage
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$1 * 100.0}')
    if (( $(echo "$MEM_USAGE < 90" | bc -l) )); then
        log_success "Memory usage: ${MEM_USAGE}%"
    else
        log_error "High memory usage: ${MEM_USAGE}%"
    fi

    # Disk usage
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -lt 85 ]; then
        log_success "Disk usage: ${DISK_USAGE}%"
    else
        log_error "High disk usage: ${DISK_USAGE}%"
    fi
}

# Main execution
echo "🔍 Starting comprehensive health check..."

TOTAL_SERVICES=0
HEALTHY_SERVICES=0

# Test all services
for service in "${SERVICES[@]}"; do
    IFS=':' read -r host port name <<< "$service"
    endpoint="http://$host:$port"

    ((TOTAL_SERVICES++))
    if test_service "$endpoint" "$name"; then
        ((HEALTHY_SERVICES++))
    fi
done

# Test monitoring stack
test_monitoring

# Test databases
test_databases

# Test system resources
test_system_resources

# Summary
echo ""
echo "========================================="
echo "📋 HEALTH CHECK SUMMARY"
echo "========================================="
echo "Services Healthy: $HEALTHY_SERVICES/$TOTAL_SERVICES"

if [ $HEALTHY_SERVICES -eq $TOTAL_SERVICES ]; then
    log_success "All services are healthy!"
    exit 0
else
    log_error "Some services need attention."
    exit 1
fi