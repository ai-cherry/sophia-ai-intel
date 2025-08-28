#!/bin/bash

# ===============================================
# Sophia AI Scalability Stress Testing Suite
# ===============================================
# Comprehensive performance benchmarking and stress testing
# for all 17 microservices with load generation and analysis

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
STRESS_DIR="$PROJECT_ROOT/.stress-test"
REPORTS_DIR="$PROJECT_ROOT/.stress-reports"
BENCHMARKS_DIR="$PROJECT_ROOT/.benchmarks"

# Create necessary directories
mkdir -p "$STRESS_DIR" "$REPORTS_DIR" "$BENCHMARKS_DIR"

# Test configuration
DEFAULT_DURATION="${STRESS_DURATION:-300}"  # 5 minutes
DEFAULT_CONCURRENT_USERS="${CONCURRENT_USERS:-10}"
DEFAULT_RPS="${REQUESTS_PER_SECOND:-50}"

# Service endpoints for testing
declare -A SERVICE_ENDPOINTS=(
    ["agno-coordinator"]="http://localhost:8080/health"
    ["mcp-agents"]="http://localhost:8000/healthz"
    ["mcp-context"]="http://localhost:8081/healthz"
    ["mcp-github"]="http://localhost:8082/healthz"
    ["mcp-hubspot"]="http://localhost:8083/healthz"
    ["mcp-lambda"]="http://localhost:8084/healthz"
    ["mcp-research"]="http://localhost:8085/healthz"
    ["mcp-business"]="http://localhost:8086/healthz"
    ["agno-teams"]="http://localhost:8087/healthz"
    ["orchestrator"]="http://localhost:8088/healthz"
    ["agno-wrappers"]="http://localhost:8089/healthz"
    ["mcp-apollo"]="http://localhost:8090/healthz"
    ["mcp-gong"]="http://localhost:8091/healthz"
    ["mcp-salesforce"]="http://localhost:8092/healthz"
    ["mcp-slack"]="http://localhost:8093/healthz"
    ["portkey-llm"]="http://localhost:8007/health"
    ["agents-swarm"]="http://localhost:8008/health"
    ["prometheus"]="http://localhost:9090/-/healthy"
    ["grafana"]="http://localhost:3000/api/health"
)

# AI inference endpoints for specialized testing
declare -A AI_ENDPOINTS=(
    ["agno-coordinator"]="http://localhost:8080/api/v1/coordinate"
    ["mcp-agents"]="http://localhost:8000/api/v1/agent/execute"
    ["mcp-research"]="http://localhost:8085/api/v1/research/query"
    ["portkey-llm"]="http://localhost:8007/api/v1/chat/completions"
    ["agents-swarm"]="http://localhost:8008/api/v1/swarm/execute"
)

print_header() {
    echo -e "${CYAN}===============================================${NC}"
    echo -e "${CYAN} Sophia AI - Scalability Stress Testing Suite${NC}"
    echo -e "${CYAN}===============================================${NC}"
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

# Check if required tools are available
check_dependencies() {
    local missing_tools=()
    
    # Check for load testing tools
    if ! command -v curl &> /dev/null; then
        missing_tools+=("curl")
    fi
    
    if ! command -v ab &> /dev/null; then
        print_warning "Apache Bench (ab) not found. Installing via package manager..."
        if command -v brew &> /dev/null; then
            brew install apache-bench || true
        elif command -v apt-get &> /dev/null; then
            sudo apt-get install -y apache2-utils || true
        fi
    fi
    
    if ! command -v wrk &> /dev/null; then
        print_warning "wrk load testing tool not found. Installing..."
        if command -v brew &> /dev/null; then
            brew install wrk || true
        elif command -v apt-get &> /dev/null; then
            sudo apt-get install -y wrk || true
        fi
    fi
    
    if ! command -v vegeta &> /dev/null; then
        print_warning "vegeta load testing tool not found. Installing..."
        if command -v brew &> /dev/null; then
            brew install vegeta || true
        elif command -v go &> /dev/null; then
            go install github.com/tsenart/vegeta@latest || true
        fi
    fi
    
    # Check for monitoring tools
    if ! command -v htop &> /dev/null && ! command -v top &> /dev/null; then
        missing_tools+=("htop or top")
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        print_warning "Some tools are missing: ${missing_tools[*]}"
        print_info "Installing available alternatives..."
    fi
}

# Wait for service to be ready
wait_for_service() {
    local service="$1"
    local endpoint="${SERVICE_ENDPOINTS[$service]}"
    local max_attempts=30
    local attempt=1
    
    print_step "Waiting for $service to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$endpoint" >/dev/null 2>&1; then
            print_success "$service is ready"
            return 0
        fi
        
        print_info "Attempt $attempt/$max_attempts - $service not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    print_error "$service failed to become ready after $max_attempts attempts"
    return 1
}

# Basic load test with Apache Bench
run_ab_test() {
    local service="$1"
    local endpoint="${SERVICE_ENDPOINTS[$service]}"
    local requests="${2:-1000}"
    local concurrency="${3:-10}"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local report_file="$REPORTS_DIR/${service}_ab_${timestamp}.txt"
    
    print_step "Running Apache Bench test for $service"
    print_info "Requests: $requests, Concurrency: $concurrency"
    
    if command -v ab &> /dev/null; then
        ab -n "$requests" -c "$concurrency" -g "$REPORTS_DIR/${service}_ab_${timestamp}.tsv" "$endpoint" > "$report_file" 2>&1
        
        # Extract key metrics
        local req_per_sec=$(grep "Requests per second:" "$report_file" | awk '{print $4}')
        local avg_time=$(grep "Time per request:" "$report_file" | head -1 | awk '{print $4}')
        local failed_requests=$(grep "Failed requests:" "$report_file" | awk '{print $3}')
        
        print_success "AB test completed for $service"
        print_info "Requests per second: $req_per_sec"
        print_info "Average response time: ${avg_time}ms"
        print_info "Failed requests: $failed_requests"
        
        # Store metrics in benchmark file
        cat >> "$BENCHMARKS_DIR/${service}_metrics.json" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "test_type": "apache_bench",
  "requests": $requests,
  "concurrency": $concurrency,
  "requests_per_second": $req_per_sec,
  "avg_response_time_ms": $avg_time,
  "failed_requests": $failed_requests,
  "report_file": "$report_file"
}
EOF
    else
        print_warning "Apache Bench not available, skipping AB test"
    fi
}

# Advanced load test with wrk
run_wrk_test() {
    local service="$1"
    local endpoint="${SERVICE_ENDPOINTS[$service]}"
    local duration="${2:-30s}"
    local threads="${3:-4}"
    local connections="${4:-10}"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local report_file="$REPORTS_DIR/${service}_wrk_${timestamp}.txt"
    
    print_step "Running wrk test for $service"
    print_info "Duration: $duration, Threads: $threads, Connections: $connections"
    
    if command -v wrk &> /dev/null; then
        wrk -t"$threads" -c"$connections" -d"$duration" --latency "$endpoint" > "$report_file" 2>&1
        
        # Extract metrics
        local req_per_sec=$(grep "Requests/sec:" "$report_file" | awk '{print $2}')
        local avg_latency=$(grep "Latency" "$report_file" | head -1 | awk '{print $2}')
        local total_requests=$(grep "requests in" "$report_file" | awk '{print $1}')
        
        print_success "wrk test completed for $service"
        print_info "Requests per second: $req_per_sec"
        print_info "Average latency: $avg_latency"
        print_info "Total requests: $total_requests"
        
        # Store metrics
        cat >> "$BENCHMARKS_DIR/${service}_metrics.json" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "test_type": "wrk",
  "duration": "$duration",
  "threads": $threads,
  "connections": $connections,
  "requests_per_second": "$req_per_sec",
  "avg_latency": "$avg_latency",
  "total_requests": "$total_requests",
  "report_file": "$report_file"
}
EOF
    else
        print_warning "wrk not available, skipping wrk test"
    fi
}

# Vegeta load test
run_vegeta_test() {
    local service="$1"
    local endpoint="${SERVICE_ENDPOINTS[$service]}"
    local rate="${2:-50/s}"
    local duration="${3:-30s}"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local results_file="$REPORTS_DIR/${service}_vegeta_${timestamp}.bin"
    local report_file="$REPORTS_DIR/${service}_vegeta_${timestamp}.txt"
    
    print_step "Running Vegeta test for $service"
    print_info "Rate: $rate, Duration: $duration"
    
    if command -v vegeta &> /dev/null; then
        # Generate targets file
        local targets_file="$STRESS_DIR/${service}_targets.txt"
        echo "GET $endpoint" > "$targets_file"
        
        # Run attack
        vegeta attack -targets="$targets_file" -rate="$rate" -duration="$duration" > "$results_file"
        
        # Generate report
        vegeta report < "$results_file" > "$report_file"
        
        # Extract metrics
        local success_rate=$(grep "Success" "$report_file" | awk '{print $3}')
        local avg_latency=$(grep "Mean" "$report_file" | awk '{print $3}')
        local p95_latency=$(grep "95th percentile" "$report_file" | awk '{print $4}')
        
        print_success "Vegeta test completed for $service"
        print_info "Success rate: $success_rate"
        print_info "Mean latency: $avg_latency"
        print_info "95th percentile: $p95_latency"
        
        # Store metrics
        cat >> "$BENCHMARKS_DIR/${service}_metrics.json" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "test_type": "vegeta",
  "rate": "$rate",
  "duration": "$duration",
  "success_rate": "$success_rate",
  "mean_latency": "$avg_latency",
  "p95_latency": "$p95_latency",
  "report_file": "$report_file"
}
EOF
    else
        print_warning "Vegeta not available, skipping Vegeta test"
    fi
}

# AI-specific stress test
run_ai_stress_test() {
    local service="$1"
    local endpoint="${AI_ENDPOINTS[$service]:-}"
    local duration="${2:-60}"
    local concurrent_users="${3:-5}"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    if [[ -z "$endpoint" ]]; then
        print_warning "No AI endpoint configured for $service, skipping AI stress test"
        return 0
    fi
    
    print_step "Running AI-specific stress test for $service"
    print_info "Duration: ${duration}s, Concurrent Users: $concurrent_users"
    
    local report_file="$REPORTS_DIR/${service}_ai_stress_${timestamp}.txt"
    local pids=()
    
    # Start concurrent workers
    for ((i=1; i<=concurrent_users; i++)); do
        {
            local worker_requests=0
            local worker_errors=0
            local start_time=$(date +%s)
            local end_time=$((start_time + duration))
            
            while [ $(date +%s) -lt $end_time ]; do
                # Create test payload based on service
                local payload=""
                case "$service" in
                    "portkey-llm")
                        payload='{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"Hello, this is a test"}],"max_tokens":10}'
                        ;;
                    "mcp-agents")
                        payload='{"action":"test","parameters":{"message":"stress test"}}'
                        ;;
                    "mcp-research")
                        payload='{"query":"test query","max_results":1}'
                        ;;
                    *)
                        payload='{"test":true}'
                        ;;
                esac
                
                if curl -sf -X POST -H "Content-Type: application/json" -d "$payload" "$endpoint" >/dev/null 2>&1; then
                    ((worker_requests++))
                else
                    ((worker_errors++))
                fi
                
                sleep 0.1  # Small delay between requests
            done
            
            echo "Worker $i: $worker_requests requests, $worker_errors errors" >> "$report_file"
        } &
        pids+=($!)
    done
    
    # Wait for all workers to complete
    for pid in "${pids[@]}"; do
        wait $pid
    done
    
    # Calculate totals
    local total_requests=$(awk '{sum += $3} END {print sum}' "$report_file")
    local total_errors=$(awk '{sum += $5} END {print sum}' "$report_file")
    local rps=$((total_requests / duration))
    
    print_success "AI stress test completed for $service"
    print_info "Total requests: $total_requests"
    print_info "Total errors: $total_errors"
    print_info "Requests per second: $rps"
    
    # Store metrics
    cat >> "$BENCHMARKS_DIR/${service}_ai_metrics.json" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "test_type": "ai_stress",
  "duration": $duration,
  "concurrent_users": $concurrent_users,
  "total_requests": $total_requests,
  "total_errors": $total_errors,
  "requests_per_second": $rps,
  "error_rate": $(echo "scale=4; $total_errors / $total_requests" | bc 2>/dev/null || echo "0"),
  "report_file": "$report_file"
}
EOF
}

# Database stress test
run_database_stress_test() {
    local duration="${1:-60}"
    local concurrent_connections="${2:-10}"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    print_step "Running database stress test"
    print_info "Duration: ${duration}s, Concurrent connections: $concurrent_connections"
    
    local report_file="$REPORTS_DIR/database_stress_${timestamp}.txt"
    
    # PostgreSQL stress test
    if command -v pgbench &> /dev/null; then
        print_info "Running pgbench stress test..."
        
        # Initialize test database
        PGPASSWORD="$POSTGRES_PASSWORD" pgbench -h localhost -p 5432 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -i >/dev/null 2>&1 || true
        
        # Run benchmark
        PGPASSWORD="$POSTGRES_PASSWORD" pgbench -h localhost -p 5432 -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
            -c "$concurrent_connections" -T "$duration" -P 5 > "$report_file" 2>&1
        
        # Extract metrics
        local tps=$(grep "tps" "$report_file" | tail -1 | awk '{print $3}')
        
        print_success "Database stress test completed"
        print_info "Transactions per second: $tps"
        
        # Store metrics
        cat >> "$BENCHMARKS_DIR/database_metrics.json" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "test_type": "postgresql_pgbench",
  "duration": $duration,
  "concurrent_connections": $concurrent_connections,
  "transactions_per_second": "$tps",
  "report_file": "$report_file"
}
EOF
    else
        print_warning "pgbench not available for PostgreSQL stress testing"
        
        # Simple connection test
        for ((i=1; i<=concurrent_connections; i++)); do
            {
                local start_time=$(date +%s)
                local end_time=$((start_time + duration))
                local queries=0
                
                while [ $(date +%s) -lt $end_time ]; do
                    if PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -p 5432 -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
                        -c "SELECT 1;" >/dev/null 2>&1; then
                        ((queries++))
                    fi
                    sleep 1
                done
                
                echo "Connection $i: $queries queries completed" >> "$report_file"
            } &
        done
        
        wait
        
        local total_queries=$(awk '{sum += $3} END {print sum}' "$report_file")
        print_info "Total queries completed: $total_queries"
    fi
    
    # Redis stress test
    if command -v redis-benchmark &> /dev/null; then
        print_info "Running Redis benchmark..."
        
        local redis_report="$REPORTS_DIR/redis_stress_${timestamp}.txt"
        redis-benchmark -h localhost -p 6380 -c "$concurrent_connections" -n 10000 > "$redis_report" 2>&1
        
        local redis_rps=$(grep "requests per second" "$redis_report" | head -1 | awk '{print $1}')
        print_info "Redis requests per second: $redis_rps"
        
        # Store Redis metrics
        cat >> "$BENCHMARKS_DIR/redis_metrics.json" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "test_type": "redis_benchmark",
  "concurrent_connections": $concurrent_connections,
  "requests_per_second": "$redis_rps",
  "report_file": "$redis_report"
}
EOF
    fi
}

# System resource monitoring during tests
start_monitoring() {
    local duration="${1:-300}"
    local monitor_file="$REPORTS_DIR/system_monitoring_$(date +%Y%m%d_%H%M%S).log"
    
    print_step "Starting system monitoring for ${duration}s"
    
    # CPU and memory monitoring
    {
        echo "Timestamp,CPU%,Memory%,LoadAvg1,LoadAvg5,LoadAvg15,DiskIO,NetworkRX,NetworkTX"
        
        local end_time=$(($(date +%s) + duration))
        while [ $(date +%s) -lt $end_time ]; do
            local timestamp=$(date -Iseconds)
            local cpu_usage=$(top -l1 -n0 | grep "CPU usage" | awk '{print $3}' | sed 's/%//' || echo "0")
            local memory_usage=$(top -l1 -n0 | grep "PhysMem" | awk '{print $2}' | sed 's/M//' || echo "0")
            local load_avg=$(uptime | awk -F'load averages: ' '{print $2}' | tr ' ' ',' || echo "0,0,0")
            
            echo "$timestamp,$cpu_usage,$memory_usage,$load_avg,0,0,0"
            sleep 5
        done
    } > "$monitor_file" &
    
    local monitor_pid=$!
    echo $monitor_pid > "$STRESS_DIR/monitor.pid"
    
    print_info "System monitoring started (PID: $monitor_pid)"
}

# Stop monitoring
stop_monitoring() {
    if [[ -f "$STRESS_DIR/monitor.pid" ]]; then
        local monitor_pid=$(cat "$STRESS_DIR/monitor.pid")
        if kill -0 $monitor_pid 2>/dev/null; then
            kill $monitor_pid
            print_success "System monitoring stopped"
        fi
        rm -f "$STRESS_DIR/monitor.pid"
    fi
}

# Generate comprehensive report
generate_report() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local final_report="$REPORTS_DIR/stress_test_summary_${timestamp}.html"
    
    print_step "Generating comprehensive stress test report"
    
    cat > "$final_report" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Sophia AI Stress Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px; }
        .good { color: #27ae60; }
        .warning { color: #f39c12; }
        .critical { color: #e74c3c; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Sophia AI Stress Test Report</h1>
        <p>Generated: TIMESTAMP</p>
        <p>Test Duration: DURATION minutes</p>
    </div>
    
    <div class="section">
        <h2>📊 Service Performance Summary</h2>
        <table id="service-table">
            <thead>
                <tr>
                    <th>Service</th>
                    <th>Requests/sec</th>
                    <th>Avg Response Time</th>
                    <th>Error Rate</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <!-- Service metrics will be inserted here -->
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <h2>🧠 AI Services Performance</h2>
        <p>Specialized AI inference and processing metrics</p>
        <!-- AI metrics will be inserted here -->
    </div>
    
    <div class="section">
        <h2>🗄️ Database Performance</h2>
        <p>PostgreSQL and Redis performance metrics</p>
        <!-- Database metrics will be inserted here -->
    </div>
    
    <div class="section">
        <h2>💻 System Resource Usage</h2>
        <p>CPU, memory, and I/O utilization during tests</p>
        <!-- System metrics will be inserted here -->
    </div>
</body>
</html>
EOF
    
    # Replace placeholders
    sed -i '' "s/TIMESTAMP/$(date -Iseconds)/g" "$final_report" 2>/dev/null || sed -i "s/TIMESTAMP/$(date -Iseconds)/g" "$final_report"
    sed -i '' "s/DURATION/$((DEFAULT_DURATION / 60))/g" "$final_report" 2>/dev/null || sed -i "s/DURATION/$((DEFAULT_DURATION / 60))/g" "$final_report"
    
    print_success "Comprehensive report generated: $final_report"
    
    # Try to open in browser
    if command -v open &> /dev/null; then
        open "$final_report" 2>/dev/null || true
    fi
}

# Run full stress test suite
run_full_suite() {
    local duration="${1:-$DEFAULT_DURATION}"
    local concurrent_users="${2:-$DEFAULT_CONCURRENT_USERS}"
    local rps="${3:-$DEFAULT_RPS}"
    
    print_header
    print_step "Starting comprehensive stress test suite"
    print_info "Duration: ${duration}s, Concurrent Users: $concurrent_users, RPS: $rps"
    
    # Check dependencies
    check_dependencies
    
    # Start system monitoring
    start_monitoring "$duration"
    
    # Test each service
    for service in "${!SERVICE_ENDPOINTS[@]}"; do
        if wait_for_service "$service"; then
            print_step "Testing $service with multiple tools..."
            
            # Run different types of tests
            run_ab_test "$service" $((rps * duration / 10)) $concurrent_users &
            run_wrk_test "$service" "${duration}s" 4 $concurrent_users &
            run_vegeta_test "$service" "${rps}/s" "${duration}s" &
            
            # Wait for tests to complete
            wait
            
            # Run AI-specific tests if applicable
            if [[ -n "${AI_ENDPOINTS[$service]:-}" ]]; then
                run_ai_stress_test "$service" $((duration / 5)) $((concurrent_users / 2))
            fi
            
            print_success "Completed stress testing for $service"
        else
            print_warning "Skipping $service - not available"
        fi
    done
    
    # Database stress testing
    run_database_stress_test $((duration / 3)) $concurrent_users
    
    # Stop monitoring
    stop_monitoring
    
    # Generate final report
    generate_report
    
    print_success "Full stress test suite completed!"
    print_info "Reports available in: $REPORTS_DIR"
    print_info "Benchmarks available in: $BENCHMARKS_DIR"
}

# Show help
show_help() {
    cat << EOF
Sophia AI Scalability Stress Testing Suite

Usage: $0 <command> [options]

Commands:
  full [duration] [users] [rps]    Run full stress test suite
  service <name> [duration]        Test specific service
  database [duration] [conns]      Test database performance
  ai <service> [duration] [users]  Test AI-specific endpoints
  monitor [duration]               Monitor system resources
  report                           Generate performance report

Options:
  duration    Test duration in seconds (default: $DEFAULT_DURATION)
  users       Concurrent users (default: $DEFAULT_CONCURRENT_USERS)  
  rps         Requests per second (default: $DEFAULT_RPS)
  conns       Database connections (default: same as users)

Examples:
  $0 full 300 20 100                      # 5min test, 20 users, 100 RPS
  $0 service agno-coordinator 120         # Test specific service for 2 minutes
  $0 database 180 15                      # Database test, 3min, 15 connections
  $0 ai portkey-llm 60 5                  # AI service test, 1min, 5 users

Available Services:
EOF
    
    for service in "${!SERVICE_ENDPOINTS[@]}"; do
        echo "  - $service"
    done
    
    echo
    echo "AI Services:"
    for service in "${!AI_ENDPOINTS[@]}"; do
        echo "  - $service (AI endpoint available)"
    done
    
    echo
}

# Main execution
main() {
    case "${1:-}" in
        "full")
            run_full_suite "${2:-$DEFAULT_DURATION}" "${3:-$DEFAULT_CONCURRENT_USERS}" "${4:-$DEFAULT_RPS}"
            ;;
        "service")
            if [[ -z "${2:-}" ]]; then
                print_error "Service name required"
                exit 1
            fi
            
            local service="$2"
            local duration="${3:-60}"
            
            if [[ -z "${SERVICE_ENDPOINTS[$service]:-}" ]]; then
                print_error "Unknown service: $service"
                exit 1
            fi
            
            start_monitoring "$duration"
            wait_for_service "$service"
            run_ab_test "$service" $((duration * 10)) 10
            run_wrk_test "$service" "${duration}s" 4 10
            stop_monitoring
            ;;
        "database")
            local duration="${2:-60}"
            local connections="${3:-10}"
            start_monitoring "$duration"
            run_database_stress_test "$duration" "$connections"
            stop_monitoring
            ;;
        "ai")
            if [[ -z "${2:-}" ]]; then
                print_error "AI service name required"
                exit 1
            fi
            
            local service="$2"
            local duration="${3:-60}"
            local users="${4:-5}"
            
            if [[ -z "${AI_ENDPOINTS[$service]:-}" ]]; then
                print_error "No AI endpoint for service: $service"
                exit 1
            fi
            
            start_monitoring "$duration"
            run_ai_stress_test "$service" "$duration" "$users"
            stop_monitoring
            ;;
        "monitor")
            local duration="${2:-300}"
            start_monitoring "$duration"
            print_info "Monitoring for ${duration}s... Press Ctrl+C to stop early"
            sleep "$duration"
            stop_monitoring
            ;;
        "report")
            generate_report
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
    stop_monitoring
}

trap cleanup EXIT

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi