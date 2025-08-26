#!/bin/bash
# Comprehensive Health Check Script
# Performs detailed health checks on all Sophia AI services and infrastructure

set -e

# Configuration
NAMESPACE="${NAMESPACE:-sophia}"
SERVICES=("mcp-context" "mcp-research" "mcp-agents" "mcp-github" "mcp-business" "mcp-hubspot" "mcp-lambda" "agno-coordinator" "agno-teams" "orchestrator" "sophia-dashboard")
MONITORING_SERVICES=("prometheus" "grafana" "loki")
HEALTH_CHECK_TIMEOUT=30
HEALTH_CHECK_INTERVAL=5
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
HEALTH_REPORT_FILE="/tmp/health-check-report-$(date +%Y%m%d-%H%M%S).json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
}

# Function to check cluster connectivity
check_cluster_connectivity() {
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
}

# Function to check if a service is running
check_service_status() {
    local service="$1"
    local namespace="$2"

    log_info "Checking service status: $service"

    # Check if deployment exists
    if ! kubectl get deployment "$service" -n "$namespace" &> /dev/null; then
        log_error "Deployment $service does not exist"
        return 1
    fi

    # Check deployment status
    local ready_replicas
    local desired_replicas
    ready_replicas=$(kubectl get deployment "$service" -n "$namespace" -o jsonpath='{.status.readyReplicas}')
    desired_replicas=$(kubectl get deployment "$service" -n "$namespace" -o jsonpath='{.status.replicas}')

    if [[ -z "$ready_replicas" ]] || [[ "$ready_replicas" != "$desired_replicas" ]]; then
        log_error "Service $service is not ready. Ready: $ready_replicas/$desired_replicas"
        return 1
    fi

    # Check pod status
    local unhealthy_pods
    unhealthy_pods=$(kubectl get pods -n "$namespace" -l app="$service" -o jsonpath='{.items[*].status.phase}' | grep -v Running | wc -w)

    if [[ $unhealthy_pods -gt 0 ]]; then
        log_error "Service $service has $unhealthy_pods unhealthy pods"
        return 1
    fi

    log_success "Service $service is healthy"
    return 0
}

# Function to check service endpoints
check_service_endpoint() {
    local service="$1"
    local namespace="$2"
    local port="${3:-8080}"
    local endpoint="${4:-/health}"

    log_info "Checking endpoint for $service: $endpoint"

    # Get service cluster IP
    local service_ip
    service_ip=$(kubectl get service "$service" -n "$namespace" -o jsonpath='{.spec.clusterIP}')

    if [[ -z "$service_ip" ]] || [[ "$service_ip" == "None" ]]; then
        log_error "Service $service has no cluster IP"
        return 1
    fi

    # Use a pod to test the endpoint
    local test_pod
    test_pod=$(kubectl get pods -n "$namespace" -l app="$service" -o jsonpath='{.items[0].metadata.name}')

    if [[ -z "$test_pod" ]]; then
        log_error "No pods found for service $service"
        return 1
    fi

    # Execute health check from within the cluster
    local health_check_cmd
    health_check_cmd="curl -s -o /dev/null -w '%{http_code}' --max-time 10 http://$service:$port$endpoint"

    local http_code
    http_code=$(kubectl exec "$test_pod" -n "$namespace" -- bash -c "$health_check_cmd" 2>/dev/null || echo "000")

    if [[ "$http_code" != "200" ]]; then
        log_error "Health check failed for $service (HTTP $http_code)"
        return 1
    fi

    log_success "Endpoint check passed for $service"
    return 0
}

# Function to check resource usage
check_resource_usage() {
    local service="$1"
    local namespace="$2"

    log_info "Checking resource usage for $service"

    # Get pod resource usage
    local pod_resources
    pod_resources=$(kubectl top pods -n "$namespace" -l app="$service" --no-headers 2>/dev/null || echo "")

    if [[ -z "$pod_resources" ]]; then
        log_warn "Could not get resource usage for $service (metrics-server may not be available)"
        return 0
    fi

    # Check for high CPU usage (>80%)
    local high_cpu_pods
    high_cpu_pods=$(echo "$pod_resources" | awk '{if ($2+0 > 80) print $1}' | wc -l)

    if [[ $high_cpu_pods -gt 0 ]]; then
        log_warn "Service $service has $high_cpu_pods pods with high CPU usage"
    fi

    # Check for high memory usage (>80%)
    local high_memory_pods
    high_memory_pods=$(echo "$pod_resources" | awk '{if ($3+0 > 80) print $1}' | wc -l)

    if [[ $high_memory_pods -gt 0 ]]; then
        log_warn "Service $service has $high_memory_pods pods with high memory usage"
    fi

    log_success "Resource usage check completed for $service"
    return 0
}

# Function to check monitoring services
check_monitoring_services() {
    log_info "Checking monitoring services..."

    for service in "${MONITORING_SERVICES[@]}"; do
        if ! check_service_status "$service" "monitoring"; then
            log_error "Monitoring service $service is not healthy"
            return 1
        fi
    done

    log_success "All monitoring services are healthy"
    return 0
}

# Function to check Istio components
check_istio_components() {
    log_info "Checking Istio components..."

    # Check Istio control plane
    if ! kubectl get deployment istio-pilot -n istio-system &> /dev/null; then
        log_error "Istio control plane not found"
        return 1
    fi

    # Check ingress gateway
    if ! kubectl get deployment istio-ingressgateway -n istio-system &> /dev/null; then
        log_error "Istio ingress gateway not found"
        return 1
    fi

    # Check if control plane is ready
    local pilot_ready
    pilot_ready=$(kubectl get deployment istio-pilot -n istio-system -o jsonpath='{.status.readyReplicas}')

    if [[ "$pilot_ready" == "0" ]]; then
        log_error "Istio control plane is not ready"
        return 1
    fi

    log_success "Istio components are healthy"
    return 0
}

# Function to check network policies
check_network_policies() {
    log_info "Checking network policies..."

    local network_policies
    network_policies=$(kubectl get networkpolicies -n "$NAMESPACE" --no-headers | wc -l)

    if [[ $network_policies -eq 0 ]]; then
        log_warn "No network policies found in namespace $NAMESPACE"
    else
        log_success "Found $network_policies network policies"
    fi

    return 0
}

# Function to check certificates
check_certificates() {
    log_info "Checking SSL certificates..."

    if kubectl get certificate -n istio-system &> /dev/null; then
        local cert_count
        cert_count=$(kubectl get certificate -n istio-system --no-headers | wc -l)

        if [[ $cert_count -eq 0 ]]; then
            log_warn "No certificates found"
        else
            log_success "Found $cert_count certificates"

            # Check certificate status
            local not_ready_certs
            not_ready_certs=$(kubectl get certificate -n istio-system -o jsonpath='{.items[?(@.status.conditions[0].type=="Ready")].status.conditions[0].status}' | grep -v True | wc -l)

            if [[ $not_ready_certs -gt 0 ]]; then
                log_error "Found $not_ready_certs certificates that are not ready"
                return 1
            fi
        fi
    else
        log_warn "Certificate manager not available"
    fi

    return 0
}

# Function to check pod disruption budgets
check_pod_disruption_budgets() {
    log_info "Checking Pod Disruption Budgets..."

    local pdb_count
    pdb_count=$(kubectl get pdb -n "$NAMESPACE" --no-headers | wc -l)

    if [[ $pdb_count -eq 0 ]]; then
        log_warn "No Pod Disruption Budgets found"
    else
        log_success "Found $pdb_count Pod Disruption Budgets"

        # Check PDB status
        while IFS= read -r pdb_line; do
            local pdb_name
            local disruptions_allowed
            pdb_name=$(echo "$pdb_line" | awk '{print $1}')
            disruptions_allowed=$(kubectl get pdb "$pdb_name" -n "$NAMESPACE" -o jsonpath='{.status.disruptionsAllowed}')

            if [[ "$disruptions_allowed" == "0" ]]; then
                log_warn "PDB $pdb_name allows no disruptions"
            fi
        done < <(kubectl get pdb -n "$NAMESPACE" --no-headers)
    fi

    return 0
}

# Function to generate health report
generate_health_report() {
    local report_file="$1"
    local issues="$2"
    local recommendations="$3"

    cat > "$report_file" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "cluster": "$(kubectl config current-context)",
    "namespace": "$NAMESPACE",
    "overall_status": "$([ -n "$issues" ] && echo "unhealthy" || echo "healthy")",
    "issues": [
        $issues
    ],
    "recommendations": [
        $recommendations
    ]
}
EOF
}

# Function to send Slack notification
send_slack_notification() {
    local report_file="$1"
    local webhook_url="$2"
    local issues="$3"

    if [[ -z "$webhook_url" ]]; then
        log_info "No Slack webhook URL provided, skipping notification"
        return 0
    fi

    local message
    if [[ -n "$issues" ]]; then
        message="🚨 *Health Check Failed* 🚨\nFound health issues in namespace $NAMESPACE\nCheck the health report for details."
    else
        message="✅ *Health Check Passed* ✅\nAll services in namespace $NAMESPACE are healthy"
    fi

    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"$message\"}" \
        "$webhook_url" 2>/dev/null || log_warn "Failed to send Slack notification"
}

# Main function
main() {
    log_info "Starting comprehensive health check..."

    # Check prerequisites
    check_kubectl
    check_cluster_connectivity

    local issues=""
    local recommendations=""
    local failed_checks=0

    # Check main services
    for service in "${SERVICES[@]}"; do
        if ! check_service_status "$service" "$NAMESPACE"; then
            issues="$issues{\"type\":\"service\",\"name\":\"$service\",\"status\":\"unhealthy\"},"
            ((failed_checks++))
        fi

        # Check service endpoint
        if ! check_service_endpoint "$service" "$NAMESPACE" "8080" "/health"; then
            issues="$issues{\"type\":\"endpoint\",\"service\":\"$service\",\"status\":\"unreachable\"},"
            ((failed_checks++))
        fi

        # Check resource usage
        if ! check_resource_usage "$service" "$NAMESPACE"; then
            issues="$issues{\"type\":\"resource\",\"service\":\"$service\",\"status\":\"high_usage\"},"
        fi
    done

    # Check monitoring services
    if ! check_monitoring_services; then
        issues="$issues{\"type\":\"monitoring\",\"status\":\"unhealthy\"},"
        ((failed_checks++))
    fi

    # Check Istio components
    if ! check_istio_components; then
        issues="$issues{\"type\":\"istio\",\"status\":\"unhealthy\"},"
        ((failed_checks++))
    fi

    # Check network policies
    if ! check_network_policies; then
        recommendations="$recommendations{\"type\":\"security\",\"action\":\"consider_adding_network_policies\"},"
    fi

    # Check certificates
    if ! check_certificates; then
        issues="$issues{\"type\":\"certificates\",\"status\":\"unhealthy\"},"
        ((failed_checks++))
    fi

    # Check Pod Disruption Budgets
    if ! check_pod_disruption_budgets; then
        recommendations="$recommendations{\"type\":\"reliability\",\"action\":\"consider_adding_pdbs\"},"
    fi

    # Remove trailing commas
    issues="${issues%,}"
    recommendations="${recommendations%,}"

    # Generate report
    generate_health_report "$HEALTH_REPORT_FILE" "$issues" "$recommendations"

    # Send notification
    send_slack_notification "$HEALTH_REPORT_FILE" "$SLACK_WEBHOOK_URL" "$issues"

    # Output results
    if [[ $failed_checks -gt 0 ]]; then
        log_error "Health check completed. Found $failed_checks failed checks."
        log_info "Detailed report saved to: $HEALTH_REPORT_FILE"
        cat "$HEALTH_REPORT_FILE"
        exit 1
    else
        log_success "Health check completed. All checks passed."
        exit 0
    fi
}

# Run main function
main "$@"