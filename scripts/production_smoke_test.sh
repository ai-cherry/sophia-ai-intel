#!/bin/bash

# Production Smoke Test Script
# Comprehensive post-deployment verification for Sophia AI Intel services

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
RESULTS_DIR="${SCRIPT_DIR}/../proofs/smoke_tests"
RESULTS_FILE="${RESULTS_DIR}/smoke_test_${TIMESTAMP}.json"
LOG_FILE="${RESULTS_DIR}/smoke_test_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Service configurations
declare -A SERVICES=(
    ["dashboard"]="https://sophiaai-dashboard-v2.fly.dev"
    ["mcp-repo"]="https://sophiaai-mcp-repo-v2.fly.dev"
    ["mcp-research"]="https://sophiaai-mcp-research-v2.fly.dev"
    ["mcp-context"]="https://sophiaai-mcp-context-v2.fly.dev"
    ["mcp-business"]="https://sophiaai-mcp-business-v2.fly.dev"
    ["jobs"]="https://sophiaai-jobs-v2.fly.dev"
)

declare -A SERVICE_TESTS=(
    ["dashboard"]="healthz build"
    ["mcp-repo"]="healthz"
    ["mcp-research"]="healthz search"
    ["mcp-context"]="healthz stats"
    ["mcp-business"]="healthz"
    ["jobs"]="healthz"
)

# Initialize results
RESULTS_JSON="{"
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNINGS=0

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV    Target environment (production, staging) [default: production]"
    echo "  -s, --service SERVICE    Test specific service only"
    echo "  -t, --timeout SECONDS    HTTP timeout in seconds [default: 10]"
    echo "  -r, --retries NUM        Number of retries for failed tests [default: 3]"
    echo "  -v, --verbose            Verbose output"
    echo "  -q, --quiet              Quiet mode (minimal output)"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Services: ${!SERVICES[@]}"
    exit 0
}

# Logging functions
log() {
    echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC') $*" | tee -a "$LOG_FILE"
}

log_info() {
    if [[ "$QUIET" != "true" ]]; then
        echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$LOG_FILE"
    fi
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $*" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "$LOG_FILE"
    ((WARNINGS++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $*" | tee -a "$LOG_FILE"
}

log_test() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${PURPLE}[TEST]${NC} $*" | tee -a "$LOG_FILE"
    fi
}

# Test execution function
execute_test() {
    local service="$1"
    local test_type="$2"
    local url="$3"
    local expected_status="$4"
    local timeout="$5"
    local retries="$6"
    
    log_test "Testing $service/$test_type: $url"
    
    local attempt=1
    while [[ $attempt -le $retries ]]; do
        local start_time=$(date +%s.%N)
        
        # Execute the HTTP request
        local response=$(curl -s -w "%{http_code};%{time_total};%{time_connect}" \
                              -m "$timeout" \
                              -H "User-Agent: SophiaAI-SmokeTest/1.0" \
                              "$url" 2>/dev/null || echo "000;0;0")
        
        local end_time=$(date +%s.%N)
        local total_time=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
        
        # Parse response
        IFS=';' read -r http_code response_time connect_time <<< "$response"
        
        # Check if we got a valid response
        if [[ "$http_code" == "$expected_status" ]]; then
            log_success "$service/$test_type: HTTP $http_code (${response_time}s)"
            echo "\"$service-$test_type\": {\"status\": \"pass\", \"http_code\": $http_code, \"response_time\": $response_time, \"connect_time\": $connect_time, \"attempts\": $attempt},"
            return 0
        else
            if [[ $attempt -eq $retries ]]; then
                log_error "$service/$test_type: HTTP $http_code (expected $expected_status) after $retries attempts"
                echo "\"$service-$test_type\": {\"status\": \"fail\", \"http_code\": $http_code, \"response_time\": $response_time, \"connect_time\": $connect_time, \"attempts\": $attempt, \"expected\": $expected_status},"
                return 1
            else
                log_warning "$service/$test_type: HTTP $http_code (attempt $attempt/$retries), retrying..."
                sleep 2
            fi
        fi
        
        ((attempt++))
    done
}

# Enhanced test functions
test_healthz() {
    local service="$1"
    local base_url="$2"
    
    ((TOTAL_TESTS++))
    if execute_test "$service" "healthz" "${base_url}/healthz" "200" "$TIMEOUT" "$RETRIES"; then
        ((PASSED_TESTS++))
    else
        ((FAILED_TESTS++))
    fi
}

test_build_endpoint() {
    local service="$1"
    local base_url="$2"
    
    ((TOTAL_TESTS++))
    if execute_test "$service" "build" "${base_url}/__build" "200" "$TIMEOUT" "$RETRIES"; then
        ((PASSED_TESTS++))
    else
        ((FAILED_TESTS++))
    fi
}

test_search_endpoint() {
    local service="$1"
    local base_url="$2"
    
    ((TOTAL_TESTS++))
    local search_payload='{"query": "smoke test", "max_results": 1}'
    local start_time=$(date +%s.%N)
    
    local response=$(curl -s -w "%{http_code}" \
                          -m "$TIMEOUT" \
                          -X POST \
                          -H "Content-Type: application/json" \
                          -H "User-Agent: SophiaAI-SmokeTest/1.0" \
                          -d "$search_payload" \
                          "${base_url}/search" 2>/dev/null || echo "000")
    
    local end_time=$(date +%s.%N)
    local total_time=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
    
    if [[ "$response" == *"200" ]]; then
        log_success "$service/search: HTTP 200 (${total_time}s)"
        echo "\"$service-search\": {\"status\": \"pass\", \"http_code\": 200, \"response_time\": $total_time},"
        ((PASSED_TESTS++))
    else
        log_error "$service/search: HTTP ${response##*[^0-9]} (expected 200)"
        echo "\"$service-search\": {\"status\": \"fail\", \"http_code\": ${response##*[^0-9]}, \"response_time\": $total_time, \"expected\": 200},"
        ((FAILED_TESTS++))
    fi
}

test_stats_endpoint() {
    local service="$1"
    local base_url="$2"
    
    ((TOTAL_TESTS++))
    if execute_test "$service" "stats" "${base_url}/context/stats" "200" "$TIMEOUT" "$RETRIES"; then
        ((PASSED_TESTS++))
    else
        ((FAILED_TESTS++))
    fi
}

# Performance benchmark
run_performance_benchmark() {
    log_info "Running performance benchmark..."
    
    local benchmark_results=""
    for service in "${!SERVICES[@]}"; do
        local base_url="${SERVICES[$service]}"
        local total_time=0
        local successful_requests=0
        local benchmark_requests=5
        
        log_test "Benchmarking $service health endpoint ($benchmark_requests requests)"
        
        for ((i=1; i<=benchmark_requests; i++)); do
            local start_time=$(date +%s.%N)
            local response=$(curl -s -w "%{http_code}" -m 5 "${base_url}/healthz" 2>/dev/null || echo "000")
            local end_time=$(date +%s.%N)
            local request_time=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")
            
            if [[ "$response" == *"200" ]]; then
                total_time=$(echo "$total_time + $request_time" | bc -l 2>/dev/null || echo "$total_time")
                ((successful_requests++))
            fi
        done
        
        if [[ $successful_requests -gt 0 ]]; then
            local avg_time=$(echo "scale=3; $total_time / $successful_requests" | bc -l 2>/dev/null || echo "0")
            log_info "$service: Average response time: ${avg_time}s ($successful_requests/$benchmark_requests successful)"
            benchmark_results+='"'$service'": {"avg_response_time": '$avg_time', "success_rate": '$(echo "scale=2; $successful_requests / $benchmark_requests * 100" | bc -l)', "total_requests": '$benchmark_requests'},'
        else
            log_warning "$service: No successful benchmark requests"
            benchmark_results+='"'$service'": {"avg_response_time": null, "success_rate": 0, "total_requests": '$benchmark_requests'},'
        fi
    done
    
    echo "$benchmark_results"
}

# Main execution
main() {
    # Default values
    ENVIRONMENT="production"
    SPECIFIC_SERVICE=""
    TIMEOUT=10
    RETRIES=3
    VERBOSE=false
    QUIET=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -s|--service)
                SPECIFIC_SERVICE="$2"
                shift 2
                ;;
            -t|--timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            -r|--retries)
                RETRIES="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -q|--quiet)
                QUIET=true
                shift
                ;;
            -h|--help)
                usage
                ;;
            *)
                echo "Unknown option: $1"
                usage
                ;;
        esac
    done
    
    # Create results directory
    mkdir -p "$RESULTS_DIR"
    
    # Initialize log
    echo "=== Sophia AI Intel Production Smoke Test ===" > "$LOG_FILE"
    echo "Timestamp: $(date -u)" >> "$LOG_FILE"
    echo "Environment: $ENVIRONMENT" >> "$LOG_FILE"
    echo "Timeout: ${TIMEOUT}s" >> "$LOG_FILE"
    echo "Retries: $RETRIES" >> "$LOG_FILE"
    echo "================================================" >> "$LOG_FILE"
    
    # Print header
    if [[ "$QUIET" != "true" ]]; then
        echo -e "${CYAN}"
        echo "╔══════════════════════════════════════════════════════════════════════════════╗"
        echo "║                    Sophia AI Intel Production Smoke Test                    ║"
        echo "╚══════════════════════════════════════════════════════════════════════════════╝"
        echo -e "${NC}"
        echo "Environment: $ENVIRONMENT"
        echo "Timestamp: $(date -u)"
        echo "Results: $RESULTS_FILE"
        echo "Log: $LOG_FILE"
        echo ""
    fi
    
    # Start results JSON
    RESULTS_JSON+="\"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"environment\": \"$ENVIRONMENT\", \"config\": {\"timeout\": $TIMEOUT, \"retries\": $RETRIES}, \"tests\": {"
    
    # Determine which services to test
    local services_to_test
    if [[ -n "$SPECIFIC_SERVICE" ]]; then
        if [[ -v SERVICES["$SPECIFIC_SERVICE"] ]]; then
            services_to_test=("$SPECIFIC_SERVICE")
        else
            log_error "Unknown service: $SPECIFIC_SERVICE"
            log_info "Available services: ${!SERVICES[@]}"
            exit 1
        fi
    else
        services_to_test=("${!SERVICES[@]}")
    fi
    
    # Execute tests for each service
    for service in "${services_to_test[@]}"; do
        local base_url="${SERVICES[$service]}"
        local tests="${SERVICE_TESTS[$service]}"
        
        log_info "Testing $service ($base_url)"
        
        # Execute each test type for the service
        for test_type in $tests; do
            case $test_type in
                "healthz")
                    test_healthz "$service" "$base_url"
                    ;;
                "build")
                    test_build_endpoint "$service" "$base_url"
                    ;;
                "search")
                    test_search_endpoint "$service" "$base_url"
                    ;;
                "stats")
                    test_stats_endpoint "$service" "$base_url"
                    ;;
                *)
                    log_warning "Unknown test type: $test_type for service: $service"
                    ;;
            esac
        done
        
        echo "" # Add spacing between services
    done
    
    # Run performance benchmark
    local benchmark_data
    benchmark_data=$(run_performance_benchmark)
    
    # Remove trailing comma from results
    RESULTS_JSON="${RESULTS_JSON%,}"
    
    # Complete results JSON
    RESULTS_JSON+="}, \"benchmark\": {${benchmark_data%,}}, \"summary\": {\"total_tests\": $TOTAL_TESTS, \"passed\": $PASSED_TESTS, \"failed\": $FAILED_TESTS, \"warnings\": $WARNINGS, \"success_rate\": $(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || echo "0")}"
    RESULTS_JSON+=", \"slo_compliance\": {\"health_slo\": $([ $FAILED_TESTS -eq 0 ] && echo "true" || echo "false"), \"target_success_rate\": 100, \"actual_success_rate\": $(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || echo "0")}}"
    
    # Save results
    echo "$RESULTS_JSON" | jq '.' > "$RESULTS_FILE" 2>/dev/null || echo "$RESULTS_JSON" > "$RESULTS_FILE"
    
    # Print summary
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                   SUMMARY                                   ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    
    local success_rate
    success_rate=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || echo "0")
    
    echo "Total Tests: $TOTAL_TESTS"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
    echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
    echo "Success Rate: ${success_rate}%"
    
    # SLO Compliance check
    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo -e "SLO Compliance: ${GREEN}✅ PASS${NC} (All services healthy)"
    else
        echo -e "SLO Compliance: ${RED}❌ FAIL${NC} ($FAILED_TESTS services unhealthy)"
    fi
    
    echo ""
    echo "Results saved to: $RESULTS_FILE"
    echo "Detailed log: $LOG_FILE"
    
    # Exit with appropriate code
    if [[ $FAILED_TESTS -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# Execute main function with all arguments
main "$@"