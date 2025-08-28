#!/bin/bash

# ===========================================
# Sophia AI Development Workflow Automation
# ===========================================
# Comprehensive development workflow with file watchers, hot reloading,
# automated testing, and development tools integration

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
WORKSPACE_DIR="$PROJECT_ROOT"

# PID files for background processes
PIDS_DIR="$PROJECT_ROOT/.pids"
mkdir -p "$PIDS_DIR"

# Development tools configuration
DEV_PORT="${DEV_PORT:-3001}"
API_PORT="${API_PORT:-8080}"
WATCH_EXTENSIONS="${WATCH_EXTENSIONS:-js,ts,tsx,jsx,py,sql,json,yaml,yml,md}"
DEBOUNCE_TIME="${DEBOUNCE_TIME:-2}"

# Service directories to watch
SERVICE_DIRS=(
    "services/agno-coordinator"
    "services/mcp-agents"
    "services/mcp-context"
    "services/mcp-github"
    "services/mcp-hubspot"
    "services/mcp-lambda"
    "services/mcp-research"
    "services/mcp-business"
    "services/agno-teams"
    "services/agno-wrappers"
    "services/orchestrator"
    "llm/portkey-llm"
    "agents/swarm"
    "frontend"
    "scripts"
    "tests"
)

print_header() {
    echo -e "${CYAN}============================================${NC}"
    echo -e "${CYAN} Sophia AI - Development Workflow Manager${NC}"
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

# Check dependencies
check_dependencies() {
    local missing_deps=()
    
    if ! command -v fswatch &> /dev/null && ! command -v inotifywait &> /dev/null; then
        missing_deps+=("fswatch")
    fi
    
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        missing_deps+=("docker-compose")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        print_info "Install with: brew install ${missing_deps[*]}"
        exit 1
    fi
}

# Get file watcher command
get_file_watcher() {
    if command -v fswatch &> /dev/null; then
        echo "fswatch"
    elif command -v inotifywait &> /dev/null; then
        echo "inotifywait"
    else
        print_error "No file watcher available (fswatch or inotifywait required)"
        exit 1
    fi
}

# Kill process by PID file
kill_process() {
    local pid_file="$1"
    local process_name="${2:-process}"
    
    if [[ -f "$pid_file" ]]; then
        local pid
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            print_info "Stopping $process_name (PID: $pid)"
            kill "$pid" 2>/dev/null || true
            sleep 1
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
        rm -f "$pid_file"
    fi
}

# Stop all development processes
stop_all_processes() {
    print_step "Stopping all development processes..."
    
    # Stop file watchers
    kill_process "$PIDS_DIR/file_watcher.pid" "file watcher"
    kill_process "$PIDS_DIR/test_watcher.pid" "test watcher"
    kill_process "$PIDS_DIR/lint_watcher.pid" "lint watcher"
    kill_process "$PIDS_DIR/dev_server.pid" "dev server"
    kill_process "$PIDS_DIR/log_aggregator.pid" "log aggregator"
    
    # Stop any remaining background jobs
    jobs -p | xargs -r kill 2>/dev/null || true
    
    print_success "All development processes stopped"
}

# Cleanup on exit
cleanup_on_exit() {
    print_info "Cleaning up development environment..."
    stop_all_processes
    exit 0
}

trap cleanup_on_exit SIGTERM SIGINT

# Hot reload service
hot_reload_service() {
    local service_path="$1"
    local service_name
    service_name=$(basename "$service_path")
    
    print_info "Hot reloading service: $service_name"
    
    # Check if service is running in Docker
    if docker-compose ps "$service_name" 2>/dev/null | grep -q "Up"; then
        print_info "Restarting Docker service: $service_name"
        docker-compose restart "$service_name" || print_warning "Failed to restart $service_name"
    else
        print_warning "Service $service_name not running in Docker"
    fi
}

# Run tests for changed files
run_tests_for_changes() {
    local changed_files=("$@")
    local test_files=()
    
    for file in "${changed_files[@]}"; do
        # Find corresponding test files
        local test_file=""
        case "$file" in
            *.py)
                # Python test files
                test_file="${file%%.py}_test.py"
                if [[ ! -f "$test_file" ]]; then
                    test_file="tests/test_$(basename "${file%%.py}").py"
                fi
                if [[ ! -f "$test_file" ]]; then
                    test_file="tests/$(dirname "$file")/test_$(basename "${file%%.py}").py"
                fi
                ;;
            *.js|*.ts)
                # JavaScript/TypeScript test files
                test_file="${file%%.js}.test.js"
                test_file="${file%%.ts}.test.ts"
                if [[ ! -f "$test_file" ]]; then
                    test_file="tests/$(basename "${file%%.js}").test.js"
                    test_file="tests/$(basename "${file%%.ts}").test.ts"
                fi
                ;;
        esac
        
        if [[ -f "$test_file" ]]; then
            test_files+=("$test_file")
        fi
    done
    
    if [[ ${#test_files[@]} -gt 0 ]]; then
        print_info "Running tests for changed files..."
        for test_file in "${test_files[@]}"; do
            case "$test_file" in
                *.py)
                    pytest "$test_file" -v || print_warning "Tests failed for $test_file"
                    ;;
                *.js|*.ts)
                    npm test "$test_file" 2>/dev/null || print_warning "Tests failed for $test_file"
                    ;;
            esac
        done
    fi
}

# Run linting for changed files
run_linting() {
    local changed_files=("$@")
    
    for file in "${changed_files[@]}"; do
        case "$file" in
            *.py)
                # Python linting
                if command -v black &> /dev/null; then
                    black "$file" --quiet 2>/dev/null || true
                fi
                if command -v flake8 &> /dev/null; then
                    flake8 "$file" 2>/dev/null || print_warning "Linting issues in $file"
                fi
                ;;
            *.js|*.ts)
                # JavaScript/TypeScript linting
                if command -v eslint &> /dev/null; then
                    eslint "$file" --fix --quiet 2>/dev/null || print_warning "Linting issues in $file"
                fi
                if command -v prettier &> /dev/null; then
                    prettier --write "$file" 2>/dev/null || true
                fi
                ;;
            *.json)
                # JSON formatting
                if command -v jq &> /dev/null; then
                    jq . "$file" > "${file}.tmp" && mv "${file}.tmp" "$file" 2>/dev/null || true
                fi
                ;;
        esac
    done
}

# File watcher handler
handle_file_change() {
    local changed_file="$1"
    local timestamp=$(date '+%H:%M:%S')
    
    print_info "[$timestamp] File changed: $changed_file"
    
    # Determine service from path
    local service=""
    for dir in "${SERVICE_DIRS[@]}"; do
        if [[ "$changed_file" == "$dir"* ]]; then
            service="$dir"
            break
        fi
    done
    
    # Skip certain files
    case "$changed_file" in
        *.log|*.pid|*.tmp|*/.git/*|*/node_modules/*|*/__pycache__/*|*.pyc)
            return 0
            ;;
    esac
    
    # Run appropriate actions based on file type
    case "$changed_file" in
        *.py|*.js|*.ts|*.tsx|*.jsx)
            # Code files - run linting and tests
            run_linting "$changed_file"
            run_tests_for_changes "$changed_file"
            
            # Hot reload service if applicable
            if [[ -n "$service" ]]; then
                hot_reload_service "$service"
            fi
            ;;
        *.sql)
            # Database migrations
            print_info "Database migration detected: $changed_file"
            if [[ "$changed_file" == *"migrations"* ]]; then
                print_info "Consider running: ./scripts/database/migrate.sh migrate up"
            fi
            ;;
        *.json|*.yaml|*.yml)
            # Configuration files
            if [[ "$changed_file" == *"docker-compose"* || "$changed_file" == *".env"* ]]; then
                print_warning "Docker configuration changed - consider restarting services"
            fi
            
            # Format JSON files
            run_linting "$changed_file"
            ;;
        *.md)
            # Documentation files
            print_info "Documentation updated: $changed_file"
            ;;
    esac
}

# Start file watcher
start_file_watcher() {
    print_step "Starting file watcher..."
    
    local watcher_cmd
    watcher_cmd=$(get_file_watcher)
    
    local watch_dirs=()
    for dir in "${SERVICE_DIRS[@]}"; do
        if [[ -d "$WORKSPACE_DIR/$dir" ]]; then
            watch_dirs+=("$WORKSPACE_DIR/$dir")
        fi
    done
    
    if [[ ${#watch_dirs[@]} -eq 0 ]]; then
        print_error "No service directories found to watch"
        return 1
    fi
    
    case "$watcher_cmd" in
        "fswatch")
            fswatch -r -l "$DEBOUNCE_TIME" "${watch_dirs[@]}" | while read -r file; do
                handle_file_change "$file"
            done &
            ;;
        "inotifywait")
            inotifywait -m -r -e modify,create,delete "${watch_dirs[@]}" --format '%w%f' | while read -r file; do
                handle_file_change "$file"
            done &
            ;;
    esac
    
    echo $! > "$PIDS_DIR/file_watcher.pid"
    print_success "File watcher started (PID: $(cat "$PIDS_DIR/file_watcher.pid"))"
}

# Start log aggregator
start_log_aggregator() {
    print_step "Starting log aggregator..."
    
    {
        # Tail all service logs
        docker-compose logs -f --tail=50 2>/dev/null | while IFS= read -r line; do
            echo "[$(date '+%H:%M:%S')] $line"
        done
    } &
    
    echo $! > "$PIDS_DIR/log_aggregator.pid"
    print_success "Log aggregator started (PID: $(cat "$PIDS_DIR/log_aggregator.pid"))"
}

# Start development server dashboard
start_dev_dashboard() {
    print_step "Starting development dashboard..."
    
    local dashboard_port="${DEV_DASHBOARD_PORT:-9999}"
    
    # Create simple HTML dashboard
    local dashboard_file="$PROJECT_ROOT/.dev-dashboard.html"
    cat > "$dashboard_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Sophia AI - Development Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
        .header { background: #2d3748; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .services { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .service { background: #2d3748; padding: 15px; border-radius: 8px; border-left: 4px solid #48bb78; }
        .service.down { border-left-color: #f56565; }
        .status { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .status.up { background: #48bb78; }
        .status.down { background: #f56565; }
        .links { margin-top: 20px; }
        .links a { color: #4299e1; margin-right: 15px; text-decoration: none; }
        .links a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Sophia AI Development Dashboard</h1>
        <p>Last updated: <span id="timestamp">$(date)</span></p>
        <div class="links">
            <a href="http://localhost:8080" target="_blank">🎯 API Gateway</a>
            <a href="http://localhost:3000" target="_blank">📊 Grafana</a>
            <a href="http://localhost:9090" target="_blank">📈 Prometheus</a>
            <a href="http://localhost:8080" target="_blank">🗄️ Adminer</a>
            <a href="http://localhost:8081" target="_blank">📡 Redis Commander</a>
            <a href="http://localhost:16686" target="_blank">🔍 Jaeger</a>
        </div>
    </div>
    
    <div class="services">
        <!-- Services will be populated by JavaScript -->
    </div>
    
    <script>
        // Auto-refresh page
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
EOF
    
    # Start simple HTTP server for dashboard
    if command -v python3 &> /dev/null; then
        (cd "$PROJECT_ROOT" && python3 -m http.server "$dashboard_port" > /dev/null 2>&1) &
        echo $! > "$PIDS_DIR/dev_server.pid"
        print_success "Development dashboard started at http://localhost:$dashboard_port"
        print_info "Dashboard file: $dashboard_file"
    else
        print_warning "Python3 not available - dashboard not started"
    fi
}

# Health check all services
health_check_services() {
    print_step "Checking service health..."
    
    local services=(
        "postgres:5432"
        "redis:6380"
        "agno-coordinator:8080"
        "mcp-agents:8000"
        "orchestrator:8088"
        "grafana:3000"
        "prometheus:9090"
    )
    
    for service_port in "${services[@]}"; do
        local service=$(echo "$service_port" | cut -d: -f1)
        local port=$(echo "$service_port" | cut -d: -f2)
        
        if nc -z localhost "$port" 2>/dev/null; then
            print_success "$service is healthy (port $port)"
        else
            print_warning "$service is not responding (port $port)"
        fi
    done
}

# Start development mode
start_dev_mode() {
    print_step "Starting development mode..."
    
    # Ensure services are running
    if ! docker-compose ps | grep -q "Up"; then
        print_info "Starting Docker services..."
        docker-compose up -d
        sleep 5
    fi
    
    # Start file watcher
    start_file_watcher
    
    # Start log aggregator
    start_log_aggregator
    
    # Start development dashboard
    start_dev_dashboard
    
    # Health check
    health_check_services
    
    print_success "Development mode started!"
    print_info "File watching active on:"
    for dir in "${SERVICE_DIRS[@]}"; do
        if [[ -d "$WORKSPACE_DIR/$dir" ]]; then
            print_info "  - $dir"
        fi
    done
    
    print_info ""
    print_info "Development tools:"
    print_info "  - File watcher with hot reload"
    print_info "  - Automated testing on file changes"
    print_info "  - Code linting and formatting"
    print_info "  - Log aggregation"
    print_info "  - Development dashboard"
    print_info ""
    print_info "Press Ctrl+C to stop development mode"
    
    # Keep the script running
    while true; do
        sleep 10
        
        # Check if processes are still running
        if [[ ! -f "$PIDS_DIR/file_watcher.pid" ]] || ! kill -0 "$(cat "$PIDS_DIR/file_watcher.pid")" 2>/dev/null; then
            print_warning "File watcher stopped, restarting..."
            start_file_watcher
        fi
        
        if [[ ! -f "$PIDS_DIR/log_aggregator.pid" ]] || ! kill -0 "$(cat "$PIDS_DIR/log_aggregator.pid")" 2>/dev/null; then
            print_warning "Log aggregator stopped, restarting..."
            start_log_aggregator
        fi
    done
}

# Quick service restart
quick_restart() {
    local service="${1:-all}"
    
    if [[ "$service" == "all" ]]; then
        print_step "Restarting all services..."
        docker-compose restart
    else
        print_step "Restarting service: $service"
        docker-compose restart "$service"
    fi
    
    sleep 2
    health_check_services
}

# Format all code
format_code() {
    print_step "Formatting all code..."
    
    # Python files
    if command -v black &> /dev/null; then
        find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" -exec black {} + 2>/dev/null || true
    fi
    
    # JavaScript/TypeScript files
    if command -v prettier &> /dev/null; then
        find . -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.jsx" | head -100 | xargs prettier --write 2>/dev/null || true
    fi
    
    # JSON files
    if command -v jq &> /dev/null; then
        find . -name "*.json" -not -path "./node_modules/*" | while read -r file; do
            jq . "$file" > "${file}.tmp" && mv "${file}.tmp" "$file" 2>/dev/null || true
        done
    fi
    
    print_success "Code formatting completed"
}

# Run full test suite
run_full_tests() {
    print_step "Running full test suite..."
    
    # Python tests
    if [[ -f "pytest.ini" ]] || [[ -d "tests" ]]; then
        print_info "Running Python tests..."
        pytest tests/ -v --tb=short || print_warning "Some Python tests failed"
    fi
    
    # JavaScript tests
    if [[ -f "package.json" ]]; then
        print_info "Running JavaScript tests..."
        npm test 2>/dev/null || print_warning "Some JavaScript tests failed"
    fi
    
    print_success "Test suite completed"
}

# Show help
show_help() {
    cat << EOF
Sophia AI Development Workflow Manager

Usage: $0 <command> [options]

Commands:
  start               Start development mode with file watching
  stop                Stop all development processes
  restart [service]   Restart service(s) (default: all)
  health              Check health of all services
  format              Format all code files
  test                Run full test suite
  dashboard           Open development dashboard
  logs [service]      Show logs for service (default: all)

Development Features:
  - Automatic file watching with hot reload
  - Code linting and formatting on save
  - Automated test execution on file changes
  - Real-time log aggregation
  - Development dashboard with service status
  - Health monitoring and alerts

Examples:
  $0 start                    # Start development mode
  $0 restart agno-coordinator # Restart specific service  
  $0 health                   # Check service health
  $0 format                   # Format all code
  $0 test                     # Run tests

Environment Variables:
  DEV_PORT                   Development server port (default: 3001)
  WATCH_EXTENSIONS          File extensions to watch (default: js,ts,tsx,jsx,py,sql,json,yaml,yml,md)
  DEBOUNCE_TIME             File watch debounce time in seconds (default: 2)

EOF
}

# Main execution
main() {
    print_header
    
    case "${1:-}" in
        "start")
            check_dependencies
            start_dev_mode
            ;;
        "stop")
            stop_all_processes
            ;;
        "restart")
            check_dependencies
            quick_restart "${2:-all}"
            ;;
        "health")
            health_check_services
            ;;
        "format")
            format_code
            ;;
        "test")
            run_full_tests
            ;;
        "dashboard")
            if [[ -f "$PIDS_DIR/dev_server.pid" ]]; then
                local dashboard_port="${DEV_DASHBOARD_PORT:-9999}"
                print_info "Opening dashboard: http://localhost:$dashboard_port"
                open "http://localhost:$dashboard_port" 2>/dev/null || true
            else
                print_error "Development dashboard not running. Start with: $0 start"
            fi
            ;;
        "logs")
            local service="${2:-}"
            if [[ -n "$service" ]]; then
                docker-compose logs -f "$service"
            else
                docker-compose logs -f
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

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi