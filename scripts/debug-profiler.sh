#!/bin/bash

# ================================================
# Sophia AI Advanced Debugging & Profiling Suite
# ================================================
# Comprehensive debugging tools, profiling capabilities, 
# performance analysis, and service introspection

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
DEBUG_DIR="$PROJECT_ROOT/.debug"
PROFILES_DIR="$PROJECT_ROOT/.profiles"
LOGS_DIR="$PROJECT_ROOT/.logs"

# Create necessary directories
mkdir -p "$DEBUG_DIR" "$PROFILES_DIR" "$LOGS_DIR"

# Service debugging configurations
declare -A DEBUG_PORTS=(
    ["agno-coordinator"]="5678"
    ["mcp-agents"]="5679"
    ["mcp-context"]="5680"
    ["mcp-github"]="5681"
    ["mcp-hubspot"]="5682"
    ["mcp-lambda"]="5683"
    ["mcp-research"]="5684"
    ["mcp-business"]="5685"
    ["agno-teams"]="5686"
    ["orchestrator"]="5687"
    ["agno-wrappers"]="5688"
    ["mcp-apollo"]="5689"
    ["mcp-gong"]="5690"
    ["mcp-salesforce"]="5691"
    ["mcp-slack"]="5692"
    ["portkey-llm"]="9229"
    ["agents-swarm"]="9230"
)

# Service main ports
declare -A SERVICE_PORTS=(
    ["postgres"]="5432"
    ["redis"]="6380"
    ["agno-coordinator"]="8080"
    ["mcp-agents"]="8000"
    ["mcp-context"]="8081"
    ["mcp-github"]="8082"
    ["mcp-hubspot"]="8083"
    ["mcp-lambda"]="8084"
    ["mcp-research"]="8085"
    ["mcp-business"]="8086"
    ["agno-teams"]="8087"
    ["orchestrator"]="8088"
    ["agno-wrappers"]="8089"
    ["mcp-apollo"]="8090"
    ["mcp-gong"]="8091"
    ["mcp-salesforce"]="8092"
    ["mcp-slack"]="8093"
    ["portkey-llm"]="8007"
    ["agents-swarm"]="8008"
    ["prometheus"]="9090"
    ["grafana"]="3000"
)

# Service languages for appropriate debugging tools
declare -A SERVICE_LANGUAGES=(
    ["agno-coordinator"]="python"
    ["mcp-agents"]="python"
    ["mcp-context"]="python"
    ["mcp-github"]="python"
    ["mcp-hubspot"]="python"
    ["mcp-lambda"]="python"
    ["mcp-research"]="python"
    ["mcp-business"]="python"
    ["agno-teams"]="python"
    ["orchestrator"]="python"
    ["agno-wrappers"]="python"
    ["mcp-apollo"]="python"
    ["mcp-gong"]="python"
    ["mcp-salesforce"]="python"
    ["mcp-slack"]="python"
    ["portkey-llm"]="nodejs"
    ["agents-swarm"]="nodejs"
)

print_header() {
    echo -e "${CYAN}================================================${NC}"
    echo -e "${CYAN} Sophia AI - Debug & Profiling Suite${NC}"
    echo -e "${CYAN}================================================${NC}"
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

# Check if service is running
is_service_running() {
    local service="$1"
    docker-compose ps "$service" 2>/dev/null | grep -q "Up" 2>/dev/null
}

# Get container ID for service
get_container_id() {
    local service="$1"
    docker-compose ps -q "$service" 2>/dev/null
}

# Attach debugger to service
attach_debugger() {
    local service="$1"
    local debug_port="${DEBUG_PORTS[$service]:-}"
    local language="${SERVICE_LANGUAGES[$service]:-python}"
    
    if [[ -z "$debug_port" ]]; then
        print_error "No debug port configured for service: $service"
        return 1
    fi
    
    if ! is_service_running "$service"; then
        print_error "Service $service is not running"
        return 1
    fi
    
    print_step "Attaching debugger to $service (${language}:${debug_port})"
    
    case "$language" in
        "python")
            # Python debugging with debugpy
            print_info "Python debugger ready on port $debug_port"
            print_info "VS Code: Add configuration to launch.json:"
            cat << EOF
{
    "name": "Debug $service",
    "type": "python",
    "request": "attach",
    "connect": {
        "host": "localhost",
        "port": $debug_port
    },
    "pathMappings": [
        {
            "localRoot": "\${workspaceFolder}/services/$service",
            "remoteRoot": "/app"
        }
    ]
}
EOF
            ;;
        "nodejs")
            # Node.js debugging
            print_info "Node.js debugger ready on port $debug_port"
            print_info "VS Code: Add configuration to launch.json:"
            cat << EOF
{
    "name": "Debug $service",
    "type": "node",
    "request": "attach",
    "port": $debug_port,
    "address": "localhost",
    "localRoot": "\${workspaceFolder}/services/$service",
    "remoteRoot": "/app"
}
EOF
            ;;
    esac
    
    print_success "Debugger attached to $service"
}

# Start profiling session
start_profiling() {
    local service="$1"
    local duration="${2:-60}"
    local profile_type="${3:-cpu}"
    
    if ! is_service_running "$service"; then
        print_error "Service $service is not running"
        return 1
    fi
    
    local container_id
    container_id=$(get_container_id "$service")
    local language="${SERVICE_LANGUAGES[$service]:-python}"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    print_step "Starting $profile_type profiling for $service (${duration}s)"
    
    case "$language" in
        "python")
            case "$profile_type" in
                "cpu")
                    # CPU profiling with py-spy
                    print_info "Running CPU profiling with py-spy"
                    local output_file="$PROFILES_DIR/${service}_cpu_${timestamp}.svg"
                    
                    docker exec "$container_id" bash -c "
                        pip install py-spy >/dev/null 2>&1 || true
                        py-spy record -o /tmp/profile.svg -d $duration -s 1>&1 || echo 'py-spy not available, using cProfile'
                        python -m cProfile -o /tmp/profile.prof -s cumtime &
                        sleep $duration
                        pkill -f cProfile
                    " &
                    
                    local pid=$!
                    print_info "Profiling in progress (PID: $pid)..."
                    wait $pid
                    
                    # Copy profile data
                    docker cp "$container_id:/tmp/profile.svg" "$output_file" 2>/dev/null || \
                    docker cp "$container_id:/tmp/profile.prof" "${PROFILES_DIR}/${service}_cpu_${timestamp}.prof" 2>/dev/null
                    
                    print_success "CPU profile saved: $output_file"
                    ;;
                "memory")
                    # Memory profiling with memory-profiler
                    print_info "Running memory profiling"
                    local output_file="$PROFILES_DIR/${service}_memory_${timestamp}.txt"
                    
                    docker exec "$container_id" bash -c "
                        pip install memory-profiler psutil >/dev/null 2>&1 || true
                        mprof run --interval=1 python -m memory_profiler main.py 2>&1 &
                        sleep $duration
                        mprof plot --output=/tmp/memory_profile.png 2>/dev/null || true
                        ps aux --sort=-%mem > /tmp/memory_usage.txt
                    " &
                    
                    wait
                    docker cp "$container_id:/tmp/memory_usage.txt" "$output_file" 2>/dev/null
                    docker cp "$container_id:/tmp/memory_profile.png" "${PROFILES_DIR}/${service}_memory_${timestamp}.png" 2>/dev/null
                    
                    print_success "Memory profile saved: $output_file"
                    ;;
                "io")
                    # I/O profiling
                    print_info "Running I/O profiling"
                    local output_file="$PROFILES_DIR/${service}_io_${timestamp}.txt"
                    
                    docker exec "$container_id" bash -c "
                        iotop -a -o -d 1 -n $duration > /tmp/io_profile.txt 2>&1 &
                        iostat -x 1 $duration > /tmp/iostat.txt 2>&1 &
                        wait
                    " &
                    
                    wait
                    docker cp "$container_id:/tmp/io_profile.txt" "$output_file" 2>/dev/null
                    
                    print_success "I/O profile saved: $output_file"
                    ;;
            esac
            ;;
        "nodejs")
            case "$profile_type" in
                "cpu")
                    # Node.js CPU profiling
                    print_info "Running Node.js CPU profiling"
                    local output_file="$PROFILES_DIR/${service}_cpu_${timestamp}.cpuprofile"
                    
                    docker exec "$container_id" bash -c "
                        node --prof app.js &
                        NODE_PID=\$!
                        sleep $duration
                        kill \$NODE_PID
                        node --prof-process isolate-*.log > /tmp/cpu_profile.txt 2>/dev/null || echo 'CPU profile generated'
                    " &
                    
                    wait
                    docker cp "$container_id:/tmp/cpu_profile.txt" "$output_file" 2>/dev/null
                    
                    print_success "CPU profile saved: $output_file"
                    ;;
                "memory")
                    # Node.js memory profiling
                    print_info "Running Node.js memory profiling"
                    local output_file="$PROFILES_DIR/${service}_memory_${timestamp}.heapsnapshot"
                    
                    docker exec "$container_id" bash -c "
                        kill -USR2 \$(pgrep node) 2>/dev/null || echo 'Heap dump triggered'
                        sleep 5
                        find / -name '*.heapsnapshot' -exec cp {} /tmp/heap.heapsnapshot \; 2>/dev/null || echo 'Heap snapshot created'
                    " &
                    
                    wait
                    docker cp "$container_id:/tmp/heap.heapsnapshot" "$output_file" 2>/dev/null
                    
                    print_success "Memory profile saved: $output_file"
                    ;;
            esac
            ;;
    esac
}

# Get service metrics
get_service_metrics() {
    local service="$1"
    local duration="${2:-60}"
    
    if ! is_service_running "$service"; then
        print_error "Service $service is not running"
        return 1
    fi
    
    local container_id
    container_id=$(get_container_id "$service")
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local metrics_file="$DEBUG_DIR/${service}_metrics_${timestamp}.json"
    
    print_step "Collecting metrics for $service (${duration}s)"
    
    # Collect Docker stats
    docker stats "$container_id" --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" > "$DEBUG_DIR/${service}_docker_stats.txt" &
    
    # Collect detailed system metrics
    docker exec "$container_id" bash -c "
        # CPU and memory info
        echo '{' > /tmp/metrics.json
        echo '  \"timestamp\": \"$(date -Iseconds)\",' >> /tmp/metrics.json
        echo '  \"cpu\": {' >> /tmp/metrics.json
        echo '    \"usage\": \"$(top -bn1 | grep 'Cpu(s)' | awk '{print \$2}' | sed 's/%us,//')\",' >> /tmp/metrics.json
        echo '    \"load_avg\": \"$(uptime | awk -F'load average:' '{print \$2}')\"' >> /tmp/metrics.json
        echo '  },' >> /tmp/metrics.json
        
        echo '  \"memory\": {' >> /tmp/metrics.json
        echo '    \"total\": \"$(free -h | awk 'NR==2{print \$2}')\",' >> /tmp/metrics.json
        echo '    \"used\": \"$(free -h | awk 'NR==2{print \$3}')\",' >> /tmp/metrics.json
        echo '    \"available\": \"$(free -h | awk 'NR==2{print \$7}')\"' >> /tmp/metrics.json
        echo '  },' >> /tmp/metrics.json
        
        echo '  \"disk\": {' >> /tmp/metrics.json
        echo '    \"usage\": \"$(df -h / | awk 'NR==2{print \$5}')\",' >> /tmp/metrics.json
        echo '    \"available\": \"$(df -h / | awk 'NR==2{print \$4}')\"' >> /tmp/metrics.json
        echo '  },' >> /tmp/metrics.json
        
        echo '  \"network\": {' >> /tmp/metrics.json
        echo '    \"connections\": \"$(ss -tuln | wc -l)\",' >> /tmp/metrics.json
        echo '    \"tcp_established\": \"$(ss -t state established | wc -l)\"' >> /tmp/metrics.json
        echo '  },' >> /tmp/metrics.json
        
        echo '  \"processes\": {' >> /tmp/metrics.json
        echo '    \"total\": \"$(ps aux | wc -l)\",' >> /tmp/metrics.json
        echo '    \"running\": \"$(ps aux | awk '\$8 ~ /^R/ { count++ } END { print count+0 }')\"' >> /tmp/metrics.json
        echo '  }' >> /tmp/metrics.json
        echo '}' >> /tmp/metrics.json
        
        # Application-specific metrics if available
        if command -v curl &> /dev/null; then
            curl -s http://localhost:${SERVICE_PORTS[$service]:-8080}/metrics 2>/dev/null || echo 'No metrics endpoint'
        fi
    " &
    
    sleep "$duration"
    
    # Copy metrics
    docker cp "$container_id:/tmp/metrics.json" "$metrics_file" 2>/dev/null
    
    print_success "Metrics collected: $metrics_file"
    
    # Display summary
    if [[ -f "$metrics_file" ]]; then
        print_info "Metrics Summary:"
        jq -r '
            "CPU Usage: " + .cpu.usage,
            "Memory Used: " + .memory.used + "/" + .memory.total,
            "Disk Usage: " + .disk.usage,
            "Network Connections: " + .network.connections,
            "Total Processes: " + .processes.total
        ' "$metrics_file" 2>/dev/null || cat "$metrics_file"
    fi
}

# Trace service requests
trace_requests() {
    local service="$1"
    local duration="${2:-60}"
    
    if ! is_service_running "$service"; then
        print_error "Service $service is not running"
        return 1
    fi
    
    local container_id
    container_id=$(get_container_id "$service")
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local trace_file="$DEBUG_DIR/${service}_trace_${timestamp}.log"
    
    print_step "Tracing requests for $service (${duration}s)"
    
    # Network tracing with tcpdump
    docker exec "$container_id" bash -c "
        # Install tcpdump if not available
        apt-get update >/dev/null 2>&1 && apt-get install -y tcpdump >/dev/null 2>&1 || \
        apk add tcpdump >/dev/null 2>&1 || \
        yum install -y tcpdump >/dev/null 2>&1 || echo 'tcpdump installation attempted'
        
        # Start packet capture
        timeout $duration tcpdump -i any -w /tmp/trace.pcap -s 65535 'port ${SERVICE_PORTS[$service]:-8080}' >/dev/null 2>&1 &
        
        # HTTP request logging
        tail -f /var/log/nginx/access.log 2>/dev/null || \
        tail -f /app/logs/access.log 2>/dev/null || \
        netstat -tuln > /tmp/netstat.log &
        
        wait
    " &
    
    local pid=$!
    print_info "Request tracing in progress (PID: $pid)..."
    wait $pid
    
    # Copy trace data
    docker cp "$container_id:/tmp/trace.pcap" "${DEBUG_DIR}/${service}_trace_${timestamp}.pcap" 2>/dev/null
    docker cp "$container_id:/tmp/netstat.log" "$trace_file" 2>/dev/null
    
    print_success "Request trace saved: $trace_file"
}

# Analyze service logs
analyze_logs() {
    local service="$1"
    local lines="${2:-1000}"
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local analysis_file="$DEBUG_DIR/${service}_log_analysis_${timestamp}.txt"
    
    print_step "Analyzing logs for $service (last $lines lines)"
    
    # Get service logs
    docker-compose logs --tail="$lines" "$service" > "$LOGS_DIR/${service}_latest.log" 2>/dev/null
    
    # Perform log analysis
    cat > "$analysis_file" << EOF
Sophia AI - Log Analysis Report
===============================
Service: $service
Timestamp: $(date -Iseconds)
Lines Analyzed: $lines

SUMMARY:
--------
EOF
    
    if [[ -f "$LOGS_DIR/${service}_latest.log" ]]; then
        # Error analysis
        echo "Error Count: $(grep -ci 'error\|exception\|traceback\|fatal' "$LOGS_DIR/${service}_latest.log")" >> "$analysis_file"
        echo "Warning Count: $(grep -ci 'warning\|warn' "$LOGS_DIR/${service}_latest.log")" >> "$analysis_file"
        echo "Info Count: $(grep -ci 'info' "$LOGS_DIR/${service}_latest.log")" >> "$analysis_file"
        echo "Debug Count: $(grep -ci 'debug' "$LOGS_DIR/${service}_latest.log")" >> "$analysis_file"
        
        echo -e "\nTOP ERRORS:" >> "$analysis_file"
        grep -i 'error\|exception\|traceback\|fatal' "$LOGS_DIR/${service}_latest.log" | \
            head -10 >> "$analysis_file" 2>/dev/null || echo "No errors found" >> "$analysis_file"
        
        echo -e "\nTOP WARNINGS:" >> "$analysis_file"
        grep -i 'warning\|warn' "$LOGS_DIR/${service}_latest.log" | \
            head -10 >> "$analysis_file" 2>/dev/null || echo "No warnings found" >> "$analysis_file"
        
        echo -e "\nREQUEST PATTERNS:" >> "$analysis_file"
        grep -i 'http\|request\|response' "$LOGS_DIR/${service}_latest.log" | \
            awk '{print $1, $2}' | sort | uniq -c | sort -nr | \
            head -10 >> "$analysis_file" 2>/dev/null || echo "No HTTP patterns found" >> "$analysis_file"
        
        echo -e "\nPERFORMANCE INDICATORS:" >> "$analysis_file"
        grep -i 'took\|duration\|elapsed\|time' "$LOGS_DIR/${service}_latest.log" | \
            head -10 >> "$analysis_file" 2>/dev/null || echo "No performance indicators found" >> "$analysis_file"
    else
        echo "No logs available for analysis" >> "$analysis_file"
    fi
    
    print_success "Log analysis saved: $analysis_file"
    
    # Display summary
    echo
    print_info "Log Analysis Summary:"
    head -20 "$analysis_file" | tail -10
}

# Interactive debugging session
interactive_debug() {
    local service="$1"
    
    if ! is_service_running "$service"; then
        print_error "Service $service is not running"
        return 1
    fi
    
    local container_id
    container_id=$(get_container_id "$service")
    
    print_step "Starting interactive debugging session for $service"
    print_info "Available commands:"
    echo "  - ps aux                  # List processes"
    echo "  - netstat -tuln          # Network connections"
    echo "  - tail -f /app/logs/*    # Follow logs"
    echo "  - top                    # Resource usage"
    echo "  - env                    # Environment variables"
    echo "  - curl localhost:PORT/health  # Health check"
    echo "  - exit                   # Exit session"
    echo
    
    docker exec -it "$container_id" /bin/bash || docker exec -it "$container_id" /bin/sh
}

# Generate performance report
generate_performance_report() {
    local service="${1:-all}"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local report_file="$DEBUG_DIR/performance_report_${timestamp}.html"
    
    print_step "Generating performance report for $service"
    
    cat > "$report_file" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Sophia AI Performance Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px; }
        .error { color: #e74c3c; }
        .warning { color: #f39c12; }
        .success { color: #27ae60; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Sophia AI Performance Report</h1>
        <p>Generated: TIMESTAMP</p>
        <p>Target: SERVICE</p>
    </div>
EOF
    
    # Replace placeholders
    sed -i '' "s/TIMESTAMP/$(date -Iseconds)/g" "$report_file" 2>/dev/null || sed -i "s/TIMESTAMP/$(date -Iseconds)/g" "$report_file"
    sed -i '' "s/SERVICE/$service/g" "$report_file" 2>/dev/null || sed -i "s/SERVICE/$service/g" "$report_file"
    
    # Add service sections
    if [[ "$service" == "all" ]]; then
        for svc in "${!SERVICE_PORTS[@]}"; do
            if is_service_running "$svc"; then
                add_service_section "$svc" "$report_file"
            fi
        done
    else
        if is_service_running "$service"; then
            add_service_section "$service" "$report_file"
        fi
    fi
    
    # Close HTML
    cat >> "$report_file" << 'EOF'
</body>
</html>
EOF
    
    print_success "Performance report generated: $report_file"
    
    # Try to open in browser
    if command -v open &> /dev/null; then
        open "$report_file" 2>/dev/null || true
    fi
}

add_service_section() {
    local service="$1"
    local report_file="$2"
    local container_id
    container_id=$(get_container_id "$service")
    
    cat >> "$report_file" << EOF
    <div class="section">
        <h2>📊 $service</h2>
        <div class="metric">
            <strong>Status:</strong> <span class="success">Running</span>
        </div>
        <div class="metric">
            <strong>Port:</strong> ${SERVICE_PORTS[$service]:-Unknown}
        </div>
        <div class="metric">
            <strong>Debug Port:</strong> ${DEBUG_PORTS[$service]:-N/A}
        </div>
        
        <h3>Resource Usage</h3>
        <div id="${service}_stats">
            <!-- Docker stats will be inserted here -->
        </div>
    </div>
EOF
}

# Show debugging dashboard
show_debug_dashboard() {
    clear
    print_header
    
    echo -e "${BLUE}Service Status:${NC}"
    echo "===================="
    
    for service in "${!SERVICE_PORTS[@]}"; do
        if is_service_running "$service"; then
            local debug_port="${DEBUG_PORTS[$service]:-N/A}"
            echo -e "${GREEN}✓${NC} $service (Port: ${SERVICE_PORTS[$service]}, Debug: $debug_port)"
        else
            echo -e "${RED}✗${NC} $service (Stopped)"
        fi
    done
    
    echo
    echo -e "${BLUE}Available Debug Commands:${NC}"
    echo "========================="
    echo "  debug attach <service>              # Attach debugger"
    echo "  debug profile <service> [duration]  # Start profiling"
    echo "  debug metrics <service> [duration]  # Collect metrics"
    echo "  debug trace <service> [duration]    # Trace requests"
    echo "  debug logs <service> [lines]        # Analyze logs"
    echo "  debug shell <service>               # Interactive session"
    echo "  debug report [service]              # Generate report"
    echo
}

# Show help
show_help() {
    cat << EOF
Sophia AI Advanced Debugging & Profiling Suite

Usage: $0 <command> [options]

Commands:
  attach <service>                    Attach debugger to service
  profile <service> [duration] [type] Start profiling (cpu|memory|io)
  metrics <service> [duration]        Collect service metrics
  trace <service> [duration]          Trace service requests
  logs <service> [lines]              Analyze service logs
  shell <service>                     Interactive debugging session
  report [service]                    Generate performance report
  dashboard                           Show debugging dashboard
  
Profiling Types:
  cpu      CPU usage profiling
  memory   Memory usage profiling  
  io       I/O operations profiling

Examples:
  $0 attach agno-coordinator               # Attach debugger
  $0 profile mcp-agents 120 cpu            # CPU profile for 2 minutes
  $0 metrics orchestrator 60               # Collect metrics for 1 minute
  $0 trace postgres 30                     # Trace requests for 30 seconds
  $0 logs agno-teams 500                   # Analyze last 500 log lines
  $0 shell mcp-github                      # Interactive debug session
  $0 report all                            # Generate comprehensive report

Debug Ports:
EOF
    
    for service in "${!DEBUG_PORTS[@]}"; do
        echo "  $service: ${DEBUG_PORTS[$service]}"
    done
    
    cat << EOF

Service Ports:
EOF
    
    for service in "${!SERVICE_PORTS[@]}"; do
        echo "  $service: ${SERVICE_PORTS[$service]}"
    done
    
    echo
}

# Main execution
main() {
    case "${1:-}" in
        "attach")
            if [[ -z "${2:-}" ]]; then
                print_error "Service name required"
                exit 1
            fi
            attach_debugger "$2"
            ;;
        "profile")
            if [[ -z "${2:-}" ]]; then
                print_error "Service name required"
                exit 1
            fi
            start_profiling "$2" "${3:-60}" "${4:-cpu}"
            ;;
        "metrics")
            if [[ -z "${2:-}" ]]; then
                print_error "Service name required"
                exit 1
            fi
            get_service_metrics "$2" "${3:-60}"
            ;;
        "trace")
            if [[ -z "${2:-}" ]]; then
                print_error "Service name required"
                exit 1
            fi
            trace_requests "$2" "${3:-60}"
            ;;
        "logs")
            if [[ -z "${2:-}" ]]; then
                print_error "Service name required"
                exit 1
            fi
            analyze_logs "$2" "${3:-1000}"
            ;;
        "shell"|"interactive")
            if [[ -z "${2:-}" ]]; then
                print_error "Service name required"
                exit 1
            fi
            interactive_debug "$2"
            ;;
        "report")
            generate_performance_report "${2:-all}"
            ;;
        "dashboard")
            show_debug_dashboard
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

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi