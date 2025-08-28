#!/bin/bash

# ===========================================
# Sophia AI Advanced Health Check & Recovery
# ===========================================
# Comprehensive health monitoring with automated service discovery,
# intelligent recovery mechanisms, and dependency management

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HEALTH_DIR="$PROJECT_ROOT/.health"
PIDS_DIR="$PROJECT_ROOT/.pids"

# Create necessary directories
mkdir -p "$HEALTH_DIR" "$PIDS_DIR"

# Health check configuration
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-30}"
MAX_RETRY_ATTEMPTS="${MAX_RETRY_ATTEMPTS:-3}"
RECOVERY_COOLDOWN="${RECOVERY_COOLDOWN:-300}"
NOTIFICATION_WEBHOOK="${NOTIFICATION_WEBHOOK:-}"

# Service definitions with health check endpoints and dependencies
declare -A SERVICES=(
    ["postgres"]="localhost:5432:tcp::database"
    ["redis"]="localhost:6380:tcp::cache"
    ["agno-coordinator"]="localhost:8080:http:/health:postgres,redis:core"
    ["mcp-agents"]="localhost:8000:http:/healthz:postgres,redis:mcp"
    ["mcp-context"]="localhost:8081:http:/healthz:postgres,redis:mcp"
    ["mcp-github"]="localhost:8082:http:/healthz:postgres,redis:mcp"
    ["mcp-hubspot"]="localhost:8083:http:/healthz:postgres,redis:mcp"
    ["mcp-lambda"]="localhost:8084:http:/healthz:postgres,redis:mcp"
    ["mcp-research"]="localhost:8085:http:/healthz:postgres,redis:mcp"
    ["mcp-business"]="localhost:8086:http:/healthz:postgres,redis:mcp"
    ["agno-teams"]="localhost:8087:http:/healthz:postgres,redis:core"
    ["orchestrator"]="localhost:8088:http:/healthz:postgres,redis,agno-teams:core"
    ["agno-wrappers"]="localhost:8089:http:/healthz:postgres,redis:core"
    ["mcp-apollo"]="localhost:8090:http:/healthz:postgres,redis:mcp"
    ["mcp-gong"]="localhost:8091:http:/healthz:postgres,redis:mcp"
    ["mcp-salesforce"]="localhost:8092:http:/healthz:postgres,redis:mcp"
    ["mcp-slack"]="localhost:8093:http:/healthz:postgres,redis:mcp"
    ["portkey-llm"]="localhost:8007:http:/health:postgres,redis:llm"
    ["agents-swarm"]="localhost:8008:http:/health:postgres,redis,portkey-llm:agents"
    ["prometheus"]="localhost:9090:http:/-/healthy::monitoring"
    ["grafana"]="localhost:3000:http:/api/health::monitoring"
    ["adminer"]="localhost:8080:http:/:postgres:dev-tools"
    ["redis-commander"]="localhost:8081:http:/:redis:dev-tools"
    ["jaeger"]="localhost:16686:http:/:prometheus:monitoring"
)

# Service groups for coordinated operations
declare -A SERVICE_GROUPS=(
    ["database"]="postgres"
    ["cache"]="redis"
    ["core"]="agno-coordinator agno-teams orchestrator agno-wrappers"
    ["mcp"]="mcp-agents mcp-context mcp-github mcp-hubspot mcp-lambda mcp-research mcp-business mcp-apollo mcp-gong mcp-salesforce mcp-slack"
    ["llm"]="portkey-llm"
    ["agents"]="agents-swarm"
    ["monitoring"]="prometheus grafana jaeger"
    ["dev-tools"]="adminer redis-commander"
)

# Health status tracking
declare -A SERVICE_STATUS=()
declare -A SERVICE_RETRY_COUNT=()
declare -A SERVICE_LAST_RECOVERY=()
declare -A SERVICE_DOWNTIME_START=()

print_header() {
    echo -e "${CYAN}============================================${NC}"
    echo -e "${CYAN} Sophia AI - Advanced Health Monitor${NC}"
    echo -e "${CYAN}============================================${NC}"
    echo
}

print_step() {
    echo -e "${YELLOW}➤ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${PURPLE}⚠ $1${NC}"
}

# Get service configuration
get_service_config() {
    local service="$1"
    local config="${SERVICES[$service]}"
    
    IFS=':' read -r host port check_type endpoint dependencies group <<< "$config"
    
    echo "$host" "$port" "$check_type" "$endpoint" "$dependencies" "$group"
}

# Check if service is healthy
check_service_health() {
    local service="$1"
    
    if [[ -z "${SERVICES[$service]:-}" ]]; then
        return 1
    fi
    
    local config
    config=$(get_service_config "$service")
    read -r host port check_type endpoint dependencies group <<< "$config"
    
    case "$check_type" in
        "tcp")
            # TCP connection check
            timeout 5 bash -c "echo >/dev/tcp/$host/$port" 2>/dev/null
            ;;
        "http")
            # HTTP health check
            local url="http://$host:$port$endpoint"
            timeout 10 curl -sf "$url" >/dev/null 2>&1
            ;;
        *)
            # Default to TCP check
            timeout 5 bash -c "echo >/dev/tcp/$host/$port" 2>/dev/null
            ;;
    esac
}

# Check service dependencies
check_service_dependencies() {
    local service="$1"
    
    local config
    config=$(get_service_config "$service")
    read -r host port check_type endpoint dependencies group <<< "$config"
    
    if [[ -z "$dependencies" ]]; then
        return 0
    fi
    
    IFS=',' read -ra DEPS <<< "$dependencies"
    for dep in "${DEPS[@]}"; do
        if [[ "${SERVICE_STATUS[$dep]:-unknown}" != "healthy" ]]; then
            return 1
        fi
    done
    
    return 0
}

# Perform health check on a service
perform_health_check() {
    local service="$1"
    local timestamp=$(date -Iseconds)
    
    if check_service_health "$service"; then
        if [[ "${SERVICE_STATUS[$service]:-unknown}" != "healthy" ]]; then
            print_success "Service recovered: $service"
            
            # Calculate downtime if service was down
            if [[ -n "${SERVICE_DOWNTIME_START[$service]:-}" ]]; then
                local downtime_start="${SERVICE_DOWNTIME_START[$service]}"
                local downtime=$(($(date +%s) - downtime_start))
                log_event "$service" "recovery" "Service recovered after ${downtime}s downtime"
                unset SERVICE_DOWNTIME_START[$service]
            else
                log_event "$service" "healthy" "Service is healthy"
            fi
        fi
        
        SERVICE_STATUS[$service]="healthy"
        SERVICE_RETRY_COUNT[$service]=0
        
        # Update health status file
        echo "$timestamp:healthy" > "$HEALTH_DIR/$service.status"
        
        return 0
    else
        # Check if dependencies are the issue
        if ! check_service_dependencies "$service"; then
            SERVICE_STATUS[$service]="waiting_dependencies"
            echo "$timestamp:waiting_dependencies" > "$HEALTH_DIR/$service.status"
            return 1
        fi
        
        # Service is unhealthy
        local retry_count=${SERVICE_RETRY_COUNT[$service]:-0}
        SERVICE_RETRY_COUNT[$service]=$((retry_count + 1))
        SERVICE_STATUS[$service]="unhealthy"
        
        # Record downtime start if this is the first failure
        if [[ -z "${SERVICE_DOWNTIME_START[$service]:-}" ]]; then
            SERVICE_DOWNTIME_START[$service]=$(date +%s)
            print_error "Service went down: $service"
            log_event "$service" "failure" "Service health check failed"
        fi
        
        echo "$timestamp:unhealthy:$retry_count" > "$HEALTH_DIR/$service.status"
        
        return 1
    fi
}

# Attempt to recover a service
recover_service() {
    local service="$1"
    local retry_count=${SERVICE_RETRY_COUNT[$service]:-0}
    local last_recovery=${SERVICE_LAST_RECOVERY[$service]:-0}
    local current_time=$(date +%s)
    
    # Check if we're in cooldown period
    if [[ $((current_time - last_recovery)) -lt $RECOVERY_COOLDOWN ]]; then
        return 1
    fi
    
    # Check if we've exceeded max retry attempts
    if [[ $retry_count -gt $MAX_RETRY_ATTEMPTS ]]; then
        print_error "Max recovery attempts reached for $service"
        log_event "$service" "max_retries" "Maximum recovery attempts exceeded"
        return 1
    fi
    
    print_step "Attempting to recover service: $service (attempt $retry_count/$MAX_RETRY_ATTEMPTS)"
    
    # Try different recovery strategies
    local recovery_success=false
    
    # Strategy 1: Docker restart
    if docker-compose ps "$service" 2>/dev/null | grep -q "$service"; then
        print_info "Restarting Docker service: $service"
        if docker-compose restart "$service" >/dev/null 2>&1; then
            print_info "Docker restart initiated for $service"
            sleep 10  # Give service time to start
            
            if perform_health_check "$service"; then
                recovery_success=true
                log_event "$service" "recovery_success" "Recovered via Docker restart"
            fi
        fi
    fi
    
    # Strategy 2: Full container recreation (if restart failed)
    if [[ "$recovery_success" == "false" ]]; then
        print_info "Recreating container: $service"
        if docker-compose up -d "$service" >/dev/null 2>&1; then
            print_info "Container recreation initiated for $service"
            sleep 15  # Give more time for full recreation
            
            if perform_health_check "$service"; then
                recovery_success=true
                log_event "$service" "recovery_success" "Recovered via container recreation"
            fi
        fi
    fi
    
    # Strategy 3: Dependency recovery (if service has dependencies)
    if [[ "$recovery_success" == "false" ]]; then
        local config
        config=$(get_service_config "$service")
        read -r host port check_type endpoint dependencies group <<< "$config"
        
        if [[ -n "$dependencies" ]]; then
            print_info "Checking and recovering dependencies for $service"
            IFS=',' read -ra DEPS <<< "$dependencies"
            
            for dep in "${DEPS[@]}"; do
                if [[ "${SERVICE_STATUS[$dep]:-unknown}" != "healthy" ]]; then
                    print_info "Recovering dependency: $dep"
                    recover_service "$dep"
                fi
            done
            
            # Try service recovery again after dependency recovery
            sleep 5
            if perform_health_check "$service"; then
                recovery_success=true
                log_event "$service" "recovery_success" "Recovered after dependency recovery"
            fi
        fi
    fi
    
    SERVICE_LAST_RECOVERY[$service]=$current_time
    
    if [[ "$recovery_success" == "true" ]]; then
        print_success "Successfully recovered service: $service"
        SERVICE_RETRY_COUNT[$service]=0
        send_notification "🟢 Service Recovered" "$service is now healthy after recovery attempt"
        return 0
    else
        print_error "Failed to recover service: $service"
        send_notification "🔴 Recovery Failed" "Failed to recover $service (attempt $retry_count/$MAX_RETRY_ATTEMPTS)"
        return 1
    fi
}

# Log health events
log_event() {
    local service="$1"
    local event_type="$2"
    local message="$3"
    local timestamp=$(date -Iseconds)
    
    local log_entry="$timestamp|$service|$event_type|$message"
    echo "$log_entry" >> "$HEALTH_DIR/health.log"
    
    # Keep only last 1000 log entries
    tail -n 1000 "$HEALTH_DIR/health.log" > "$HEALTH_DIR/health.log.tmp" && mv "$HEALTH_DIR/health.log.tmp" "$HEALTH_DIR/health.log"
}

# Send notification
send_notification() {
    local title="$1"
    local message="$2"
    
    if [[ -n "$NOTIFICATION_WEBHOOK" ]]; then
        local payload=$(cat << EOF
{
    "title": "$title",
    "message": "$message",
    "timestamp": "$(date -Iseconds)",
    "source": "Sophia AI Health Monitor"
}
EOF
        )
        
        curl -X POST -H "Content-Type: application/json" -d "$payload" "$NOTIFICATION_WEBHOOK" >/dev/null 2>&1 || true
    fi
    
    # macOS notification
    if command -v osascript &> /dev/null; then
        osascript -e "display notification \"$message\" with title \"$title\"" 2>/dev/null || true
    fi
}

# Get service health status
get_service_status() {
    local service="$1"
    local status_file="$HEALTH_DIR/$service.status"
    
    if [[ -f "$status_file" ]]; then
        tail -n 1 "$status_file"
    else
        echo "unknown"
    fi
}

# Generate health report
generate_health_report() {
    local timestamp=$(date -Iseconds)
    local report_file="$HEALTH_DIR/health_report_$(date +%Y%m%d_%H%M%S).json"
    
    # Build JSON report
    cat > "$report_file" << EOF
{
    "timestamp": "$timestamp",
    "overall_status": "$(get_overall_status)",
    "services": {
EOF
    
    local first=true
    for service in "${!SERVICES[@]}"; do
        if [[ "$first" == "false" ]]; then
            echo "," >> "$report_file"
        fi
        first=false
        
        local status="${SERVICE_STATUS[$service]:-unknown}"
        local retry_count=${SERVICE_RETRY_COUNT[$service]:-0}
        local last_recovery=${SERVICE_LAST_RECOVERY[$service]:-0}
        local config
        config=$(get_service_config "$service")
        read -r host port check_type endpoint dependencies group <<< "$config"
        
        cat >> "$report_file" << EOF
        "$service": {
            "status": "$status",
            "retry_count": $retry_count,
            "last_recovery": $last_recovery,
            "endpoint": "$host:$port",
            "check_type": "$check_type",
            "dependencies": "$dependencies",
            "group": "$group"
        }
EOF
    done
    
    cat >> "$report_file" << EOF
    },
    "service_groups": {
EOF
    
    first=true
    for group in "${!SERVICE_GROUPS[@]}"; do
        if [[ "$first" == "false" ]]; then
            echo "," >> "$report_file"
        fi
        first=false
        
        local group_services="${SERVICE_GROUPS[$group]}"
        local group_status=$(get_group_status "$group")
        
        cat >> "$report_file" << EOF
        "$group": {
            "status": "$group_status",
            "services": "$group_services"
        }
EOF
    done
    
    cat >> "$report_file" << EOF
    }
}
EOF
    
    echo "$report_file"
}

# Get overall system status
get_overall_status() {
    local unhealthy_count=0
    local total_count=0
    
    for service in "${!SERVICES[@]}"; do
        total_count=$((total_count + 1))
        if [[ "${SERVICE_STATUS[$service]:-unknown}" != "healthy" ]]; then
            unhealthy_count=$((unhealthy_count + 1))
        fi
    done
    
    if [[ $unhealthy_count -eq 0 ]]; then
        echo "healthy"
    elif [[ $unhealthy_count -lt 3 ]]; then
        echo "degraded"
    else
        echo "unhealthy"
    fi
}

# Get service group status
get_group_status() {
    local group="$1"
    local group_services="${SERVICE_GROUPS[$group]}"
    
    local unhealthy_in_group=0
    local total_in_group=0
    
    IFS=' ' read -ra SERVICES_ARRAY <<< "$group_services"
    for service in "${SERVICES_ARRAY[@]}"; do
        total_in_group=$((total_in_group + 1))
        if [[ "${SERVICE_STATUS[$service]:-unknown}" != "healthy" ]]; then
            unhealthy_in_group=$((unhealthy_in_group + 1))
        fi
    done
    
    if [[ $unhealthy_in_group -eq 0 ]]; then
        echo "healthy"
    elif [[ $unhealthy_in_group -lt $total_in_group ]]; then
        echo "degraded"
    else
        echo "unhealthy"
    fi
}

# Display real-time status
display_status() {
    clear
    print_header
    
    local overall_status
    overall_status=$(get_overall_status)
    
    case "$overall_status" in
        "healthy")
            echo -e "${GREEN}🟢 Overall Status: HEALTHY${NC}"
            ;;
        "degraded")
            echo -e "${YELLOW}🟡 Overall Status: DEGRADED${NC}"
            ;;
        "unhealthy")
            echo -e "${RED}🔴 Overall Status: UNHEALTHY${NC}"
            ;;
    esac
    
    echo
    echo "Last updated: $(date)"
    echo
    
    # Display service groups
    for group in "${!SERVICE_GROUPS[@]}"; do
        local group_services="${SERVICE_GROUPS[$group]}"
        local group_status
        group_status=$(get_group_status "$group")
        
        case "$group_status" in
            "healthy")
                echo -e "${GREEN}[$group] HEALTHY${NC}"
                ;;
            "degraded")
                echo -e "${YELLOW}[$group] DEGRADED${NC}"
                ;;
            "unhealthy")
                echo -e "${RED}[$group] UNHEALTHY${NC}"
                ;;
        esac
        
        IFS=' ' read -ra SERVICES_ARRAY <<< "$group_services"
        for service in "${SERVICES_ARRAY[@]}"; do
            local status="${SERVICE_STATUS[$service]:-unknown}"
            local retry_count=${SERVICE_RETRY_COUNT[$service]:-0}
            
            case "$status" in
                "healthy")
                    echo -e "  ${GREEN}✓${NC} $service"
                    ;;
                "unhealthy")
                    echo -e "  ${RED}✗${NC} $service (retries: $retry_count)"
                    ;;
                "waiting_dependencies")
                    echo -e "  ${YELLOW}⏳${NC} $service (waiting for dependencies)"
                    ;;
                *)
                    echo -e "  ${PURPLE}?${NC} $service (unknown)"
                    ;;
            esac
        done
        echo
    done
}

# Start health monitoring daemon
start_monitoring() {
    print_step "Starting health monitoring daemon..."
    
    # Initialize all services as unknown
    for service in "${!SERVICES[@]}"; do
        SERVICE_STATUS[$service]="unknown"
        SERVICE_RETRY_COUNT[$service]=0
    done
    
    # Create PID file
    echo $$ > "$PIDS_DIR/health_monitor.pid"
    
    print_success "Health monitoring started (PID: $$)"
    print_info "Check interval: ${HEALTH_CHECK_INTERVAL}s"
    print_info "Max retry attempts: $MAX_RETRY_ATTEMPTS"
    print_info "Recovery cooldown: ${RECOVERY_COOLDOWN}s"
    echo
    
    # Main monitoring loop
    while true; do
        local check_start_time=$(date +%s)
        
        # Perform health checks on all services
        for service in "${!SERVICES[@]}"; do
            if ! perform_health_check "$service"; then
                # Service is unhealthy, attempt recovery
                if [[ ${SERVICE_RETRY_COUNT[$service]:-0} -le $MAX_RETRY_ATTEMPTS ]]; then
                    recover_service "$service" &
                fi
            fi
        done
        
        # Wait for recovery attempts to complete
        wait
        
        # Display status in interactive mode
        if [[ "${1:-}" == "--interactive" ]]; then
            display_status
        fi
        
        # Generate periodic reports
        local current_hour=$(date +%H)
        if [[ "$current_hour" == "00" ]] && [[ ! -f "$HEALTH_DIR/report_$(date +%Y%m%d).json" ]]; then
            generate_health_report > "$HEALTH_DIR/report_$(date +%Y%m%d).json"
        fi
        
        # Calculate sleep time to maintain consistent interval
        local check_duration=$(($(date +%s) - check_start_time))
        local sleep_time=$((HEALTH_CHECK_INTERVAL - check_duration))
        if [[ $sleep_time -gt 0 ]]; then
            sleep $sleep_time
        fi
    done
}

# Stop monitoring daemon
stop_monitoring() {
    local pid_file="$PIDS_DIR/health_monitor.pid"
    
    if [[ -f "$pid_file" ]]; then
        local pid
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            print_info "Stopping health monitor (PID: $pid)"
            kill "$pid"
            rm -f "$pid_file"
            print_success "Health monitor stopped"
        else
            print_warning "Health monitor process not running"
            rm -f "$pid_file"
        fi
    else
        print_warning "Health monitor PID file not found"
    fi
}

# Show current status
show_status() {
    if [[ ! -f "$PIDS_DIR/health_monitor.pid" ]]; then
        print_error "Health monitor is not running"
        exit 1
    fi
    
    display_status
}

# Show recent events
show_events() {
    local count="${1:-20}"
    
    if [[ -f "$HEALTH_DIR/health.log" ]]; then
        print_step "Recent health events (last $count):"
        echo
        
        tail -n "$count" "$HEALTH_DIR/health.log" | while IFS='|' read -r timestamp service event_type message; do
            case "$event_type" in
                "healthy"|"recovery"|"recovery_success")
                    echo -e "${GREEN}[$timestamp]${NC} $service: $message"
                    ;;
                "failure"|"max_retries")
                    echo -e "${RED}[$timestamp]${NC} $service: $message"
                    ;;
                *)
                    echo -e "${BLUE}[$timestamp]${NC} $service: $message"
                    ;;
            esac
        done
    else
        print_info "No health events logged yet"
    fi
}

# Manual recovery trigger
trigger_recovery() {
    local service="$1"
    
    if [[ -z "${SERVICES[$service]:-}" ]]; then
        print_error "Unknown service: $service"
        echo "Available services:"
        for s in "${!SERVICES[@]}"; do
            echo "  - $s"
        done
        exit 1
    fi
    
    print_step "Manually triggering recovery for: $service"
    
    # Reset retry count and cooldown
    SERVICE_RETRY_COUNT[$service]=0
    SERVICE_LAST_RECOVERY[$service]=0
    
    if recover_service "$service"; then
        print_success "Recovery triggered successfully"
    else
        print_error "Recovery attempt failed"
        exit 1
    fi
}

# Show help
show_help() {
    cat << EOF
Sophia AI Advanced Health Monitor & Recovery System

Usage: $0 <command> [options]

Commands:
  start [--interactive]    Start health monitoring daemon
  stop                     Stop health monitoring daemon
  status                   Show current service status
  events [count]           Show recent health events (default: 20)
  recover <service>        Manually trigger recovery for service
  report                   Generate health report
  test <service>           Test specific service health

Interactive Mode:
  $0 start --interactive   # Real-time status dashboard

Examples:
  $0 start                           # Start monitoring daemon
  $0 status                          # Show current status
  $0 events 50                       # Show last 50 events
  $0 recover agno-coordinator        # Manually recover service
  $0 test postgres                   # Test PostgreSQL health

Configuration:
  HEALTH_CHECK_INTERVAL       Check interval in seconds (default: 30)
  MAX_RETRY_ATTEMPTS          Maximum recovery attempts (default: 3)
  RECOVERY_COOLDOWN           Cooldown between recoveries in seconds (default: 300)
  NOTIFICATION_WEBHOOK        Webhook URL for notifications

Service Groups:
  - database: PostgreSQL
  - cache: Redis  
  - core: Main AI coordination services
  - mcp: Model Context Protocol services
  - llm: Large Language Model services
  - agents: AI agent services
  - monitoring: Prometheus, Grafana, Jaeger
  - dev-tools: Adminer, Redis Commander

EOF
}

# Main execution
main() {
    case "${1:-}" in
        "start")
            start_monitoring "${2:-}"
            ;;
        "stop")
            stop_monitoring
            ;;
        "status")
            show_status
            ;;
        "events")
            show_events "${2:-20}"
            ;;
        "recover")
            if [[ -z "${2:-}" ]]; then
                print_error "Service name required"
                exit 1
            fi
            trigger_recovery "$2"
            ;;
        "report")
            report_file=$(generate_health_report)
            print_success "Health report generated: $report_file"
            ;;
        "test")
            if [[ -z "${2:-}" ]]; then
                print_error "Service name required"
                exit 1
            fi
            
            service="$2"
            if [[ -z "${SERVICES[$service]:-}" ]]; then
                print_error "Unknown service: $service"
                exit 1
            fi
            
            if perform_health_check "$service"; then
                print_success "Service $service is healthy"
            else
                print_error "Service $service is unhealthy"
                exit 1
            fi
            ;;
        "help"|"-h"|"--help"|"")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Cleanup on exit
cleanup() {
    if [[ -f "$PIDS_DIR/health_monitor.pid" ]]; then
        stop_monitoring
    fi
}

trap cleanup EXIT

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi