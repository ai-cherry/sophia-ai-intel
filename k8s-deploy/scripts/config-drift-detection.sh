#!/bin/bash
# Configuration Drift Detection Script
# This script detects configuration drift between desired state and current state

set -e

# Configuration
NAMESPACE="${NAMESPACE:-sophia}"
CONFIG_MAPS=("sophia-config" "sophia-config-production" "sophia-config-staging")
SECRETS=("sophia-secrets" "database-secrets" "infrastructure-secrets")
DEPLOYMENT_DIR="./manifests"
DRIFT_REPORT_FILE="/tmp/config-drift-report-$(date +%Y%m%d-%H%M%S).json"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
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

# Function to compare ConfigMaps
check_configmap_drift() {
    local configmap="$1"
    local namespace="$2"
    local file_path="$3"

    log_info "Checking ConfigMap: $configmap in namespace: $namespace"

    if ! kubectl get configmap "$configmap" -n "$namespace" &> /dev/null; then
        log_warn "ConfigMap $configmap does not exist in cluster"
        return 1
    fi

    # Get current ConfigMap data
    local current_data
    current_data=$(kubectl get configmap "$configmap" -n "$namespace" -o jsonpath='{.data}')

    # Read desired ConfigMap data from file
    if [[ ! -f "$file_path" ]]; then
        log_warn "ConfigMap file $file_path does not exist"
        return 1
    fi

    # Extract data section from YAML file
    local desired_data
    desired_data=$(grep -A 1000 '^data:' "$file_path" | tail -n +2 | sed '/^[^ ]/q' | head -n -1)

    # Compare data (simplified comparison)
    if [[ "$current_data" != "$desired_data" ]]; then
        log_warn "Configuration drift detected in ConfigMap: $configmap"
        return 1
    else
        log_info "ConfigMap $configmap is in sync"
        return 0
    fi
}

# Function to check Secrets
check_secret_drift() {
    local secret="$1"
    local namespace="$2"

    log_info "Checking Secret: $secret in namespace: $namespace"

    if ! kubectl get secret "$secret" -n "$namespace" &> /dev/null; then
        log_warn "Secret $secret does not exist in cluster"
        return 1
    fi

    # Get current secret metadata
    local current_metadata
    current_metadata=$(kubectl get secret "$secret" -n "$namespace" -o jsonpath='{.metadata.creationTimestamp}')

    # Check if secret is older than threshold (e.g., 30 days)
    local secret_age_days
    secret_age_days=$(($(date +%s) - $(date -d "$current_metadata" +%s))) / 86400

    if [[ $secret_age_days -gt 30 ]]; then
        log_warn "Secret $secret is $secret_age_days days old - consider rotation"
        return 1
    fi

    log_info "Secret $secret age check passed"
    return 0
}

# Function to check resource limits and requests
check_resource_limits() {
    local deployment="$1"
    local namespace="$2"

    log_info "Checking resource limits for deployment: $deployment"

    local resources
    resources=$(kubectl get deployment "$deployment" -n "$namespace" -o jsonpath='{.spec.template.spec.containers[*].resources}')

    if [[ -z "$resources" ]]; then
        log_warn "No resource limits set for deployment: $deployment"
        return 1
    fi

    log_info "Resource limits check passed for $deployment"
    return 0
}

# Function to check for missing labels
check_labels() {
    local deployment="$1"
    local namespace="$2"
    local required_labels=("app" "version" "environment")

    log_info "Checking required labels for deployment: $deployment"

    for label in "${required_labels[@]}"; do
        local label_value
        label_value=$(kubectl get deployment "$deployment" -n "$namespace" -o jsonpath="{.metadata.labels.$label}")

        if [[ -z "$label_value" ]]; then
            log_warn "Missing required label '$label' on deployment: $deployment"
            return 1
        fi
    done

    log_info "Label check passed for $deployment"
    return 0
}

# Function to generate drift report
generate_drift_report() {
    local drift_items="$1"
    local report_file="$2"

    cat > "$report_file" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "cluster": "$(kubectl config current-context)",
    "namespace": "$NAMESPACE",
    "drift_detected": $([ -n "$drift_items" ] && echo "true" || echo "false"),
    "items": [
        $drift_items
    ]
}
EOF
}

# Function to send Slack notification
send_slack_notification() {
    local report_file="$1"
    local webhook_url="$2"

    if [[ -z "$webhook_url" ]]; then
        log_info "No Slack webhook URL provided, skipping notification"
        return 0
    fi

    local drift_count
    drift_count=$(jq '.items | length' "$report_file")

    local message
    if [[ $drift_count -gt 0 ]]; then
        message="🚨 *Configuration Drift Detected* 🚨\nFound $drift_count configuration drift(s) in namespace $NAMESPACE\nCheck the drift report for details."
    else
        message="✅ *Configuration Check Complete* ✅\nNo configuration drift detected in namespace $NAMESPACE"
    fi

    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"$message\"}" \
        "$webhook_url"
}

# Main function
main() {
    log_info "Starting configuration drift detection..."

    # Check prerequisites
    check_kubectl
    check_cluster_connectivity

    local drift_items=""
    local drift_count=0

    # Check ConfigMaps
    for configmap in "${CONFIG_MAPS[@]}"; do
        local config_file="$DEPLOYMENT_DIR/configmap.yaml"
        if [[ "$configmap" == *"production"* ]]; then
            config_file="$DEPLOYMENT_DIR/configmap-production.yaml"
        elif [[ "$configmap" == *"staging"* ]]; then
            config_file="$DEPLOYMENT_DIR/configmap-staging.yaml"
        fi

        if check_configmap_drift "$configmap" "$NAMESPACE" "$config_file"; then
            log_info "ConfigMap $configmap is in sync"
        else
            drift_items="$drift_items{\"type\":\"configmap\",\"name\":\"$configmap\",\"status\":\"drift_detected\"},"
            ((drift_count++))
        fi
    done

    # Check Secrets
    for secret in "${SECRETS[@]}"; do
        if check_secret_drift "$secret" "$NAMESPACE"; then
            log_info "Secret $secret check passed"
        else
            drift_items="$drift_items{\"type\":\"secret\",\"name\":\"$secret\",\"status\":\"drift_detected\"},"
            ((drift_count++))
        fi
    done

    # Check deployments for resource limits
    local deployments
    deployments=$(kubectl get deployments -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}')

    for deployment in $deployments; do
        if ! check_resource_limits "$deployment" "$NAMESPACE"; then
            drift_items="$drift_items{\"type\":\"deployment\",\"name\":\"$deployment\",\"issue\":\"missing_resource_limits\"},"
            ((drift_count++))
        fi

        if ! check_labels "$deployment" "$NAMESPACE"; then
            drift_items="$drift_items{\"type\":\"deployment\",\"name\":\"$deployment\",\"issue\":\"missing_labels\"},"
            ((drift_count++))
        fi
    done

    # Remove trailing comma
    drift_items="${drift_items%,}"

    # Generate report
    generate_drift_report "$drift_items" "$DRIFT_REPORT_FILE"

    # Send notification
    send_slack_notification "$DRIFT_REPORT_FILE" "$SLACK_WEBHOOK_URL"

    # Output results
    if [[ $drift_count -gt 0 ]]; then
        log_warn "Configuration drift detection completed. Found $drift_count drift(s)."
        log_info "Detailed report saved to: $DRIFT_REPORT_FILE"
        cat "$DRIFT_REPORT_FILE"
        exit 1
    else
        log_info "Configuration drift detection completed. No drifts detected."
        exit 0
    fi
}

# Run main function
main "$@"