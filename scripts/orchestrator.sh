#!/bin/bash

# ==================================================
# Sophia AI Service Dependency & Orchestration Manager
# ==================================================
# Intelligent service dependency management, coordinated startup/shutdown,
# and automated orchestration for the complete 17-microservice platform

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
ORCHESTRATION_DIR="$PROJECT_ROOT/.orchestration"
STATE_DIR="$PROJECT_ROOT/.state"

# Create necessary directories
mkdir -p "$ORCHESTRATION_DIR" "$STATE_DIR"

# Service dependency graph
declare -A SERVICE_DEPENDENCIES=(
    # Infrastructure services (no dependencies)
    ["postgres"]=""
    ["redis"]=""
    ["qdrant"]=""
    
    # Core AI services (depend on infrastructure)
    ["agno-coordinator"]="postgres,redis"
    ["agno-teams"]="postgres,redis,agno-coordinator"
    ["orchestrator"]="postgres,redis,agno-teams"
    ["agno-wrappers"]="postgres,redis,agno-coordinator"
    
    # MCP services (depend on infrastructure)
    ["mcp-agents"]="postgres,redis"
    ["mcp-context"]="postgres,redis"
    ["mcp-research"]="postgres,redis"
    ["mcp-business"]="postgres,redis"
    
    # Integration services (depend on MCP core)
    ["mcp-github"]="postgres,redis,mcp-agents"
    ["mcp-hubspot"]="postgres,redis,mcp-agents"
    ["mcp-lambda"]="postgres,redis,mcp-agents"
    ["mcp-salesforce"]="postgres,redis,mcp-agents"
    ["mcp-slack"]="postgres,redis,mcp-agents"
    ["mcp-apollo"]="postgres,redis,mcp-agents"
    ["mcp-gong"]="postgres,redis,mcp-agents"
    
    # LLM and Agent services (depend on core services)
    ["portkey-llm"]="postgres,redis"
    ["agents-swarm"]="postgres,redis,portkey-llm,agno-coordinator"
    
    # Monitoring services (independent but useful)
    ["prometheus"]=""
    ["grafana"]="prometheus"
    ["loki"]=""
    ["jaeger"]=""
    ["promtail"]="loki"
    
    # Development tools
    ["adminer"]="postgres"
    ["redis-commander"]="redis"
    ["file-watcher"]=""
)

# Service startup priorities (lower number = higher priority)
declare -A SERVICE_PRIORITIES=(
    # Infrastructure layer - Priority 1
    ["postgres"]="1"
    ["redis"]="1"
    ["qdrant"]="1"
    
    # Monitoring infrastructure - Priority 2
    ["prometheus"]="2"
    ["loki"]="2"
    ["jaeger"]="2"
    
    # Core services - Priority 3
    ["agno-coordinator"]="3"
    ["mcp-agents"]="3"
    ["mcp-context"]="3"
    ["portkey-llm"]="3"
    
    # Secondary services - Priority 4
    ["agno-teams"]="4"
    ["mcp-research"]="4"
    ["mcp-business"]="4"
    ["grafana"]="4"
    ["promtail"]="4"
    
    # Orchestration layer - Priority 5
    ["orchestrator"]="5"
    ["agno-wrappers"]="5"
    ["agents-swarm"]="5"
    
    # Integration services - Priority 6
    ["mcp-github"]="6"
    ["mcp-hubspot"]="6"
    ["mcp-lambda"]="6"
    ["mcp-salesforce"]="6"
    ["mcp-slack"]="6"
    ["mcp-apollo"]="6"
    ["mcp-gong"]="6"
    
    # Development tools - Priority 7
    ["adminer"]="7"
    ["redis-commander"]="7"
    ["file-watcher"]="7"
)

# Service health check configurations
declare -A SERVICE_HEALTH_CHECKS=(
    ["postgres"]="pg_isready -h localhost -p 5432"
    ["redis"]="redis-cli -h localhost -p 6380 ping"
    ["agno-coordinator"]="curl -sf http://localhost:8080/health"
    ["mcp-agents"]="curl -sf http://localhost:8000/healthz"
    ["portkey-llm"]="curl -sf http://localhost:8007/health"
    ["prometheus"]="curl -sf http://localhost:9090/-/healthy"
    ["grafana"]="curl -sf http://localhost:3000/api/health"
)

# Service startup timeout (seconds)
declare -A SERVICE_TIMEOUTS=(
    ["postgres"]="60"
    ["redis"]="30"
    ["agno-coordinator"]="120"
    ["mcp-agents"]="90"
    ["portkey-llm"]="180"  # LLM services take longer
    ["agents-swarm"]="150"
    ["prometheus"]="45"
    ["grafana"]="60"
)

print_header() {
    echo -e "${CYAN}==================================================${NC}"
    echo -e "${CYAN} Sophia AI - Service Orchestration Manager${NC}"
    echo -e "${CYAN}==================================================${NC}"
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

# Save service state
save_service_state() {
    local service="$1"
    local state="$2"
    local timestamp=$(date -Iseconds)
    
    echo "$state:$timestamp" > "$STATE_DIR/${service}.state"
    
    # Also log to orchestration log
    echo "$timestamp|$service|$state" >> "$ORCHESTRATION_DIR/orchestration.log"
}

# Get service state
get_service_state() {
    local service="$1"
    local state_file="$STATE_DIR/${service}.state"
    
    if [[ -f "$state_file" ]]; then
        cut -d':' -f1 "$state_file"
    else
        echo "unknown"
    fi
}

# Check if service is running
is_service_running() {
    local service="$1"
    
    # Check Docker container status
    if docker-compose ps "$service" 2>/dev/null | grep -q "Up"; then
        return 0
    else
        return 1
    fi
}

# Wait for service to be healthy
wait_for_service_health() {
    local service="$1"
    local timeout="${SERVICE_TIMEOUTS[$service]:-60}"
    local health_check="${SERVICE_HEALTH_CHECKS[$service]:-}"
    local start_time=$(date +%s)
    local end_time=$((start_time + timeout))
    
    print_step "Waiting for $service to be healthy (timeout: ${timeout}s)"
    
    while [ $(date +%s) -lt $end_time ]; do
        # First check if container is running
        if ! is_service_running "$service"; then
            print_warning "$service container is not running"
            sleep 2
            continue
        fi
        
        # Then check health if health check is defined
        if [[ -n "$health_check" ]]; then
            if eval "$health_check" >/dev/null 2>&1; then
                local elapsed=$(($(date +%s) - start_time))
                print_success "$service is healthy (${elapsed}s)"
                save_service_state "$service" "healthy"
                return 0
            fi
        else
            # No health check defined, assume healthy if running
            local elapsed=$(($(date +%s) - start_time))
            print_success "$service is running (${elapsed}s)"
            save_service_state "$service" "running"
            return 0
        fi
        
        sleep 2
        echo -n "."
    done
    
    echo
    print_error "$service failed to become healthy within ${timeout}s"
    save_service_state "$service" "unhealthy"
    return 1
}

# Check service dependencies
check_dependencies() {
    local service="$1"
    local dependencies="${SERVICE_DEPENDENCIES[$service]:-}"
    
    if [[ -z "$dependencies" ]]; then
        return 0
    fi
    
    print_info "Checking dependencies for $service: $dependencies"
    
    IFS=',' read -ra DEPS <<< "$dependencies"
    for dep in "${DEPS[@]}"; do
        local dep_state
        dep_state=$(get_service_state "$dep")
        
        if [[ "$dep_state" != "healthy" && "$dep_state" != "running" ]]; then
            if ! is_service_running "$dep"; then
                print_error "Dependency $dep is not running for $service"
                return 1
            else
                print_warning "Dependency $dep is running but not confirmed healthy for $service"
            fi
        fi
    done
    
    print_success "All dependencies satisfied for $service"
    return 0
}

# Start service with dependency checking
start_service() {
    local service="$1"
    local force="${2:-false}"
    
    # Check if already running
    if is_service_running "$service" && [[ "$force" != "true" ]]; then
        print_info "$service is already running"
        return 0
    fi
    
    print_step "Starting $service"
    
    # Check dependencies first
    if ! check_dependencies "$service"; then
        print_error "Cannot start $service due to missing dependencies"
        save_service_state "$service" "dependency_failed"
        return 1
    fi
    
    # Start the service
    save_service_state "$service" "starting"
    
    if docker-compose up -d "$service" >/dev/null 2>&1; then
        print_info "$service container started, waiting for health check..."
        
        if wait_for_service_health "$service"; then
            print_success "Successfully started $service"
            return 0
        else
            print_error "Failed to start $service (health check failed)"
            save_service_state "$service" "start_failed"
            return 1
        fi
    else
        print_error "Failed to start $service container"
        save_service_state "$service" "start_failed"
        return 1
    fi
}

# Stop service gracefully
stop_service() {
    local service="$1"
    local timeout="${2:-30}"
    
    if ! is_service_running "$service"; then
        print_info "$service is not running"
        return 0
    fi
    
    print_step "Stopping $service (graceful shutdown)"
    save_service_state "$service" "stopping"
    
    # Try graceful stop first
    if docker-compose stop -t "$timeout" "$service" >/dev/null 2>&1; then
        print_success "Gracefully stopped $service"
        save_service_state "$service" "stopped"
        return 0
    else
        print_warning "Graceful stop failed, forcing stop for $service"
        
        if docker-compose kill "$service" >/dev/null 2>&1; then
            print_warning "Force stopped $service"
            save_service_state "$service" "force_stopped"
            return 0
        else
            print_error "Failed to stop $service"
            save_service_state "$service" "stop_failed"
            return 1
        fi
    fi
}

# Get services sorted by priority
get_services_by_priority() {
    local ascending="${1:-true}"
    
    # Create a temporary file with service:priority pairs
    local temp_file=$(mktemp)
    
    for service in "${!SERVICE_PRIORITIES[@]}"; do
        echo "${SERVICE_PRIORITIES[$service]}:$service" >> "$temp_file"
    done
    
    # Sort by priority
    if [[ "$ascending" == "true" ]]; then
        sort -n "$temp_file" | cut -d':' -f2
    else
        sort -nr "$temp_file" | cut -d':' -f2
    fi
    
    rm -f "$temp_file"
}

# Start all services in dependency order
start_all_services() {
    local parallel="${1:-false}"
    local max_parallel="${2:-5}"
    
    print_header
    print_step "Starting all services in dependency order"
    
    if [[ "$parallel" == "true" ]]; then
        print_info "Using parallel startup (max $max_parallel concurrent services)"
        start_services_parallel "$max_parallel"
    else
        print_info "Using sequential startup for maximum reliability"
        start_services_sequential
    fi
}

# Sequential service startup
start_services_sequential() {
    local failed_services=()
    local started_services=()
    
    # Get services sorted by priority (ascending)
    local services
    services=$(get_services_by_priority true)
    
    for service in $services; do
        if start_service "$service"; then
            started_services+=("$service")
        else
            failed_services+=("$service")
            print_warning "Continuing with remaining services despite $service failure"
        fi
    done
    
    # Summary
    echo
    print_success "Started services: ${started_services[*]}"
    
    if [ ${#failed_services[@]} -gt 0 ]; then
        print_error "Failed services: ${failed_services[*]}"
        return 1
    else
        print_success "All services started successfully!"
        return 0
    fi
}

# Parallel service startup with dependency management
start_services_parallel() {
    local max_parallel="$1"
    local current_parallel=0
    local pids=()
    local failed_services=()
    local started_services=()
    
    # Group services by priority level
    declare -A priority_groups
    
    for service in "${!SERVICE_PRIORITIES[@]}"; do
        local priority="${SERVICE_PRIORITIES[$service]}"
        if [[ -z "${priority_groups[$priority]:-}" ]]; then
            priority_groups[$priority]="$service"
        else
            priority_groups[$priority]="${priority_groups[$priority]} $service"
        fi
    done
    
    # Start each priority group sequentially, but services within group in parallel
    for priority in $(printf '%s\n' "${!priority_groups[@]}" | sort -n); do
        print_step "Starting priority $priority services"
        
        local services_in_group="${priority_groups[$priority]}"
        local group_pids=()
        
        for service in $services_in_group; do
            # Wait if we've hit the parallel limit
            while [ ${#group_pids[@]} -ge $max_parallel ]; do
                # Wait for any job to complete
                wait -n
                # Remove completed jobs from array
                local new_pids=()
                for pid in "${group_pids[@]}"; do
                    if kill -0 $pid 2>/dev/null; then
                        new_pids+=($pid)
                    fi
                done
                group_pids=("${new_pids[@]}")
            done
            
            # Start service in background
            {
                if start_service "$service"; then
                    echo "$service:success" >> "$ORCHESTRATION_DIR/parallel_results.tmp"
                else
                    echo "$service:failed" >> "$ORCHESTRATION_DIR/parallel_results.tmp"
                fi
            } &
            
            group_pids+=($!)
        done
        
        # Wait for all services in this priority group to complete
        for pid in "${group_pids[@]}"; do
            wait $pid
        done
        
        print_info "Priority $priority group completed"
    done
    
    # Process results
    if [[ -f "$ORCHESTRATION_DIR/parallel_results.tmp" ]]; then
        while IFS=':' read -r service result; do
            if [[ "$result" == "success" ]]; then
                started_services+=("$service")
            else
                failed_services+=("$service")
            fi
        done < "$ORCHESTRATION_DIR/parallel_results.tmp"
        
        rm -f "$ORCHESTRATION_DIR/parallel_results.tmp"
    fi
    
    # Summary
    echo
    print_success "Started services: ${started_services[*]}"
    
    if [ ${#failed_services[@]} -gt 0 ]; then
        print_error "Failed services: ${failed_services[*]}"
        return 1
    else
        print_success "All services started successfully!"
        return 0
    fi
}

# Stop all services in reverse dependency order
stop_all_services() {
    local force="${1:-false}"
    local timeout="${2:-30}"
    
    print_header
    print_step "Stopping all services in reverse dependency order"
    
    local failed_services=()
    local stopped_services=()
    
    # Get services sorted by priority (descending for shutdown)
    local services
    services=$(get_services_by_priority false)
    
    for service in $services; do
        if [[ "$force" == "true" ]]; then
            print_step "Force stopping $service"
            if docker-compose kill "$service" >/dev/null 2>&1; then
                stopped_services+=("$service")
                save_service_state "$service" "force_stopped"
            else
                failed_services+=("$service")
            fi
        else
            if stop_service "$service" "$timeout"; then
                stopped_services+=("$service")
            else
                failed_services+=("$service")
            fi
        fi
    done
    
    # Summary
    echo
    print_success "Stopped services: ${stopped_services[*]}"
    
    if [ ${#failed_services[@]} -gt 0 ]; then
        print_error "Failed to stop services: ${failed_services[*]}"
        return 1
    else
        print_success "All services stopped successfully!"
        return 0
    fi
}

# Restart services in proper order
restart_all_services() {
    local parallel="${1:-false}"
    
    print_header
    print_step "Restarting all services"
    
    # Stop all services first
    stop_all_services false 30
    
    # Wait a bit for cleanup
    sleep 5
    
    # Start all services
    start_all_services "$parallel"
}

# Show service dependency graph
show_dependency_graph() {
    print_header
    print_step "Service Dependency Graph"
    echo
    
    printf "%-20s %-10s %-30s %-10s\n" "SERVICE" "PRIORITY" "DEPENDENCIES" "STATUS"
    echo "-------------------- ---------- ------------------------------ ----------"
    
    for service in "${!SERVICE_DEPENDENCIES[@]}"; do
        local priority="${SERVICE_PRIORITIES[$service]:-999}"
        local dependencies="${SERVICE_DEPENDENCIES[$service]:-none}"
        local state
        state=$(get_service_state "$service")
        
        # Color code the status
        local colored_state
        case "$state" in
            "healthy"|"running") colored_state="${GREEN}$state${NC}" ;;
            "starting"|"stopping") colored_state="${YELLOW}$state${NC}" ;;
            "unhealthy"|"failed"|"*_failed") colored_state="${RED}$state${NC}" ;;
            *) colored_state="${PURPLE}$state${NC}" ;;
        esac
        
        printf "%-20s %-10s %-30s %-20s\n" "$service" "$priority" "${dependencies:-none}" "$colored_state"
    done
    
    echo
    print_info "Priority levels: 1=Infrastructure, 2=Monitoring, 3=Core, 4=Secondary, 5=Orchestration, 6=Integrations, 7=Dev-tools"
}

# Validate dependencies
validate_dependencies() {
    print_header
    print_step "Validating service dependency configuration"
    
    local validation_errors=0
    
    # Check for circular dependencies
    print_info "Checking for circular dependencies..."
    
    for service in "${!SERVICE_DEPENDENCIES[@]}"; do
        local visited=()
        if check_circular_dependency "$service" "$service" visited; then
            print_error "Circular dependency detected involving $service"
            ((validation_errors++))
        fi
    done
    
    # Check for missing dependency definitions
    print_info "Checking for missing dependency definitions..."
    
    for service in "${!SERVICE_DEPENDENCIES[@]}"; do
        local dependencies="${SERVICE_DEPENDENCIES[$service]:-}"
        if [[ -n "$dependencies" ]]; then
            IFS=',' read -ra DEPS <<< "$dependencies"
            for dep in "${DEPS[@]}"; do
                if [[ -z "${SERVICE_DEPENDENCIES[$dep]:-}" ]]; then
                    print_warning "$service depends on $dep, but $dep is not defined in dependency graph"
                    ((validation_errors++))
                fi
            done
        fi
    done
    
    # Check priority consistency
    print_info "Checking priority consistency..."
    
    for service in "${!SERVICE_DEPENDENCIES[@]}"; do
        local service_priority="${SERVICE_PRIORITIES[$service]:-999}"
        local dependencies="${SERVICE_DEPENDENCIES[$service]:-}"
        
        if [[ -n "$dependencies" ]]; then
            IFS=',' read -ra DEPS <<< "$dependencies"
            for dep in "${DEPS[@]}"; do
                local dep_priority="${SERVICE_PRIORITIES[$dep]:-999}"
                if [[ $dep_priority -gt $service_priority ]]; then
                    print_warning "$service (priority $service_priority) depends on $dep (priority $dep_priority) - dependency should have lower priority number"
                fi
            done
        fi
    done
    
    if [[ $validation_errors -eq 0 ]]; then
        print_success "Dependency validation passed!"
        return 0
    else
        print_error "Dependency validation found $validation_errors issues"
        return 1
    fi
}

# Check for circular dependencies (recursive)
check_circular_dependency() {
    local current="$1"
    local target="$2"
    local -n visited_ref=$3
    
    # Add current service to visited list
    visited_ref+=("$current")
    
    local dependencies="${SERVICE_DEPENDENCIES[$current]:-}"
    if [[ -n "$dependencies" ]]; then
        IFS=',' read -ra DEPS <<< "$dependencies"
        for dep in "${DEPS[@]}"; do
            # If we found our target, we have a cycle
            if [[ "$dep" == "$target" ]]; then
                return 0  # Circular dependency found
            fi
            
            # If we've already visited this dependency, skip to avoid infinite recursion
            local already_visited=false
            for visited_service in "${visited_ref[@]}"; do
                if [[ "$visited_service" == "$dep" ]]; then
                    already_visited=true
                    break
                fi
            done
            
            if [[ "$already_visited" == "false" ]]; then
                if check_circular_dependency "$dep" "$target" visited_ref; then
                    return 0  # Circular dependency found in recursive call
                fi
            fi
        done
    fi
    
    return 1  # No circular dependency found
}

# Generate service startup script
generate_startup_script() {
    local output_file="${1:-startup-order.sh}"
    
    print_step "Generating optimized startup script: $output_file"
    
    cat > "$output_file" << 'EOF'
#!/bin/bash
# Auto-generated Sophia AI service startup script
# Generated by orchestrator.sh

set -euo pipefail

print_info() {
    echo -e "\033[0;34mℹ $1\033[0m"
}

print_success() {
    echo -e "\033[0;32m✓ $1\033[0m"
}

print_error() {
    echo -e "\033[0;31m✗ $1\033[0m"
}

# Service startup order (optimized for dependencies)
EOF
    
    # Add services in priority order
    local services
    services=$(get_services_by_priority true)
    
    echo "" >> "$output_file"
    echo "SERVICES=(" >> "$output_file"
    for service in $services; do
        echo "    \"$service\"" >> "$output_file"
    done
    echo ")" >> "$output_file"
    
    cat >> "$output_file" << 'EOF'

# Start services in order
for service in "${SERVICES[@]}"; do
    print_info "Starting $service..."
    
    if docker-compose up -d "$service"; then
        print_success "Started $service"
    else
        print_error "Failed to start $service"
        exit 1
    fi
    
    # Brief pause between services
    sleep 2
done

print_success "All services started successfully!"
EOF
    
    chmod +x "$output_file"
    print_success "Startup script generated: $output_file"
}

# Show service status dashboard
show_status_dashboard() {
    clear
    print_header
    
    echo "Service Status Dashboard - $(date)"
    echo "=================================================="
    
    # Count services by status
    local healthy=0 unhealthy=0 starting=0 unknown=0
    
    for service in "${!SERVICE_DEPENDENCIES[@]}"; do
        local state
        state=$(get_service_state "$service")
        
        case "$state" in
            "healthy"|"running") ((healthy++)) ;;
            "starting"|"stopping") ((starting++)) ;;
            "unhealthy"|"*_failed") ((unhealthy++)) ;;
            *) ((unknown++)) ;;
        esac
    done
    
    echo "Status Summary:"
    echo "  Healthy: $healthy"
    echo "  Starting/Stopping: $starting"
    echo "  Unhealthy: $unhealthy"
    echo "  Unknown: $unknown"
    echo
    
    show_dependency_graph
}

# Show help
show_help() {
    cat << EOF
Sophia AI Service Orchestration Manager

Usage: $0 <command> [options]

Commands:
  start [parallel] [max-parallel]    Start all services in dependency order
  stop [force] [timeout]             Stop all services in reverse order
  restart [parallel]                 Restart all services
  status                             Show service status dashboard
  deps                              Show dependency graph
  validate                          Validate dependency configuration
  
Service Management:
  start-service <name>              Start specific service
  stop-service <name> [timeout]    Stop specific service
  restart-service <name>            Restart specific service
  check-deps <name>                 Check dependencies for service
  
Utilities:
  generate-script [filename]        Generate optimized startup script
  show-logs <service>               Show service logs
  clear-states                      Clear all service states

Options:
  parallel     Use parallel startup (faster but less reliable)
  force        Force stop services (kill instead of graceful stop)
  max-parallel Maximum concurrent services during parallel start (default: 5)
  timeout      Timeout for graceful stop in seconds (default: 30)

Examples:
  $0 start                          # Sequential startup (recommended)
  $0 start parallel 3               # Parallel startup, max 3 concurrent
  $0 stop                           # Graceful stop all services
  $0 stop force                     # Force stop all services
  $0 restart                        # Full restart
  $0 start-service agno-coordinator # Start single service
  $0 validate                       # Check dependency configuration

Service Priority Levels:
  1. Infrastructure (postgres, redis, qdrant)
  2. Monitoring (prometheus, loki, jaeger)
  3. Core (agno-coordinator, mcp-agents, portkey-llm)
  4. Secondary (agno-teams, mcp-research, grafana)
  5. Orchestration (orchestrator, agno-wrappers, agents-swarm)
  6. Integrations (mcp-github, mcp-hubspot, etc.)
  7. Development Tools (adminer, redis-commander)

EOF
}

# Main execution
main() {
    case "${1:-}" in
        "start")
            start_all_services "${2:-false}" "${3:-5}"
            ;;
        "stop")
            stop_all_services "${2:-false}" "${3:-30}"
            ;;
        "restart")
            restart_all_services "${2:-false}"
            ;;
        "status")
            show_status_dashboard
            ;;
        "deps"|"dependencies")
            show_dependency_graph
            ;;
        "validate")
            validate_dependencies
            ;;
        "start-service")
            if [[ -z "${2:-}" ]]; then
                print_error "Service name required"
                exit 1
            fi
            start_service "$2" "${3:-false}"
            ;;
        "stop-service")
            if [[ -z "${2:-}" ]]; then
                print_error "Service name required"
                exit 1
            fi
            stop_service "$2" "${3:-30}"
            ;;
        "restart-service")
            if [[ -z "${2:-}" ]]; then
                print_error "Service name required"
                exit 1
            fi
            stop_service "$2" 30
            sleep 2
            start_service "$2"
            ;;
        "check-deps")
            if [[ -z "${2:-}" ]]; then
                print_error "Service name required"
                exit 1
            fi
            check_dependencies "$2"
            ;;
        "generate-script")
            generate_startup_script "${2:-startup-order.sh}"
            ;;
        "show-logs")
            if [[ -z "${2:-}" ]]; then
                print_error "Service name required"
                exit 1
            fi
            docker-compose logs -f "${2}"
            ;;
        "clear-states")
            rm -f "$STATE_DIR"/*.state
            print_success "All service states cleared"
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

# Cleanup function
cleanup() {
    # Clean up any temporary files
    rm -f "$ORCHESTRATION_DIR"/*.tmp 2>/dev/null || true
}

trap cleanup EXIT

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi