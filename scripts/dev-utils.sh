#!/bin/bash

# 🛠️ Sophia AI Intel - Development Utilities
# Comprehensive management and debugging tools

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_header() { echo -e "${WHITE}=== $1 ===${NC}"; }

# Configuration
COMPOSE_FILE="docker-compose.yml"
OVERRIDE_FILE="docker-compose.override.yml"
ENV_FILE=".env.local"

# Available commands
show_help() {
    echo -e "${WHITE}Sophia AI Intel - Development Utilities${NC}"
    echo "============================================"
    echo
    echo -e "${CYAN}SERVICE MANAGEMENT:${NC}"
    echo "  start [service]     Start all services or specific service"
    echo "  stop [service]      Stop all services or specific service"
    echo "  restart [service]   Restart all services or specific service"
    echo "  logs [service]      Show logs for service (follow mode)"
    echo "  status              Show status of all services"
    echo "  ps                  Show running containers"
    echo
    echo -e "${CYAN}DATABASE OPERATIONS:${NC}"
    echo "  db-reset            Reset all databases to clean state"
    echo "  db-migrate          Run database migrations"
    echo "  db-seed             Seed databases with test data"
    echo "  db-backup           Backup all databases"
    echo "  db-restore [file]   Restore database from backup"
    echo "  db-shell            Open PostgreSQL shell"
    echo "  redis-shell         Open Redis shell"
    echo
    echo -e "${CYAN}DEVELOPMENT TOOLS:${NC}"
    echo "  build [service]     Build Docker images"
    echo "  clean               Clean up containers, images, and volumes"
    echo "  health              Run comprehensive health check"
    echo "  debug [service]     Show debug information for service"
    echo "  test [type]         Run tests (unit, integration, e2e, all)"
    echo "  lint                Run code linting"
    echo "  format              Format code"
    echo
    echo -e "${CYAN}MONITORING & DEBUGGING:${NC}"
    echo "  monitor             Open monitoring dashboard"
    echo "  metrics             Show system metrics"
    echo "  trace [service]     Show distributed tracing"
    echo "  profile [service]   Performance profiling"
    echo
    echo -e "${CYAN}EXAMPLES:${NC}"
    echo "  ./scripts/dev-utils.sh start mcp-agents"
    echo "  ./scripts/dev-utils.sh db-reset"
    echo "  ./scripts/dev-utils.sh test integration"
    echo "  ./scripts/dev-utils.sh logs agno-coordinator"
}

# Service management functions
start_services() {
    local service=${1:-""}
    
    log_header "STARTING SERVICES"
    
    if [ -z "$service" ]; then
        log_info "Starting all services..."
        docker-compose --env-file "$ENV_FILE" up -d
        log_success "All services started"
    else
        log_info "Starting $service..."
        docker-compose --env-file "$ENV_FILE" up -d "$service"
        log_success "$service started"
    fi
    
    sleep 5
    show_status
}

stop_services() {
    local service=${1:-""}
    
    log_header "STOPPING SERVICES"
    
    if [ -z "$service" ]; then
        log_info "Stopping all services..."
        docker-compose down
        log_success "All services stopped"
    else
        log_info "Stopping $service..."
        docker-compose stop "$service"
        log_success "$service stopped"
    fi
}

restart_services() {
    local service=${1:-""}
    
    log_header "RESTARTING SERVICES"
    
    if [ -z "$service" ]; then
        log_info "Restarting all services..."
        docker-compose down
        sleep 2
        docker-compose --env-file "$ENV_FILE" up -d
        log_success "All services restarted"
    else
        log_info "Restarting $service..."
        docker-compose restart "$service"
        log_success "$service restarted"
    fi
}

show_logs() {
    local service=${1:-""}
    
    if [ -z "$service" ]; then
        log_info "Showing logs for all services..."
        docker-compose logs -f
    else
        log_info "Showing logs for $service..."
        docker-compose logs -f "$service"
    fi
}

show_status() {
    log_header "SERVICE STATUS"
    docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    echo
    
    log_header "SYSTEM RESOURCES"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

show_ps() {
    docker-compose ps
}

# Database operations
db_reset() {
    log_header "DATABASE RESET"
    log_warning "This will delete all data! Are you sure? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        log_info "Stopping database services..."
        docker-compose stop postgres redis
        
        log_info "Removing database volumes..."
        docker volume rm $(docker volume ls -q | grep sophia) 2>/dev/null || true
        
        log_info "Restarting database services..."
        docker-compose --env-file "$ENV_FILE" up -d postgres redis
        
        log_info "Waiting for databases to be ready..."
        sleep 10
        
        db_migrate
        log_success "Database reset complete"
    else
        log_info "Database reset cancelled"
    fi
}

db_migrate() {
    log_header "DATABASE MIGRATION"
    
    if [ -f "scripts/init_database.sql" ]; then
        log_info "Running PostgreSQL migrations..."
        docker-compose exec -T postgres psql -U sophia -d sophia -f /docker-entrypoint-initdb.d/init.sql
        log_success "PostgreSQL migrations complete"
    fi
    
    # Run any Python migration scripts
    if [ -d "migrations" ]; then
        log_info "Running Python migrations..."
        # Add migration logic here
        log_success "Python migrations complete"
    fi
}

db_seed() {
    log_header "DATABASE SEEDING"
    
    log_info "Seeding test data..."
    
    # Seed PostgreSQL with test data
    docker-compose exec -T postgres psql -U sophia -d sophia << 'EOF'
INSERT INTO users (email, username, full_name, role) VALUES 
('admin@sophia-intel.ai', 'admin', 'System Administrator', 'admin'),
('dev@sophia-intel.ai', 'developer', 'Developer User', 'user'),
('test@sophia-intel.ai', 'testuser', 'Test User', 'user')
ON CONFLICT (email) DO NOTHING;

INSERT INTO agents (name, description, model, system_prompt, status) VALUES
('Research Assistant', 'AI agent for research tasks', 'gpt-4', 'You are a helpful research assistant', 'active'),
('Code Helper', 'AI agent for coding assistance', 'gpt-4', 'You are a coding expert', 'active'),
('Business Analyst', 'AI agent for business analysis', 'claude-3', 'You are a business analysis expert', 'active')
ON CONFLICT (name) DO NOTHING;
EOF
    
    # Seed Redis with test data
    docker-compose exec redis redis-cli << 'EOF'
SET test:key1 "value1"
SET test:key2 "value2"
SADD test:set "member1" "member2" "member3"
EOF
    
    log_success "Database seeding complete"
}

db_backup() {
    log_header "DATABASE BACKUP"
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="backups"
    mkdir -p "$backup_dir"
    
    log_info "Backing up PostgreSQL..."
    docker-compose exec -T postgres pg_dump -U sophia sophia > "$backup_dir/postgres_backup_$timestamp.sql"
    
    log_info "Backing up Redis..."
    docker-compose exec redis redis-cli --rdb - > "$backup_dir/redis_backup_$timestamp.rdb"
    
    log_success "Backup saved to $backup_dir/"
}

db_restore() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        log_error "Please specify backup file"
        return 1
    fi
    
    log_header "DATABASE RESTORE"
    log_warning "This will overwrite current data! Are you sure? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        if [[ "$backup_file" == *.sql ]]; then
            log_info "Restoring PostgreSQL from $backup_file..."
            docker-compose exec -T postgres psql -U sophia -d sophia < "$backup_file"
        elif [[ "$backup_file" == *.rdb ]]; then
            log_info "Restoring Redis from $backup_file..."
            docker-compose stop redis
            docker cp "$backup_file" $(docker-compose ps -q redis):/data/dump.rdb
            docker-compose start redis
        fi
        log_success "Database restore complete"
    else
        log_info "Restore cancelled"
    fi
}

db_shell() {
    log_info "Opening PostgreSQL shell..."
    docker-compose exec postgres psql -U sophia -d sophia
}

redis_shell() {
    log_info "Opening Redis shell..."
    docker-compose exec redis redis-cli
}

# Development tools
build_services() {
    local service=${1:-""}
    
    log_header "BUILDING SERVICES"
    
    if [ -z "$service" ]; then
        log_info "Building all services..."
        docker-compose build --parallel
        log_success "All services built"
    else
        log_info "Building $service..."
        docker-compose build "$service"
        log_success "$service built"
    fi
}

clean_system() {
    log_header "SYSTEM CLEANUP"
    log_warning "This will remove all containers, images, and volumes! Are you sure? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        log_info "Stopping all services..."
        docker-compose down -v --remove-orphans
        
        log_info "Removing unused containers..."
        docker container prune -f
        
        log_info "Removing unused images..."
        docker image prune -af
        
        log_info "Removing unused volumes..."
        docker volume prune -f
        
        log_info "Removing unused networks..."
        docker network prune -f
        
        log_success "System cleanup complete"
    else
        log_info "Cleanup cancelled"
    fi
}

run_health_check() {
    log_info "Running comprehensive health check..."
    
    if [ -f "scripts/health-check-local.sh" ]; then
        chmod +x scripts/health-check-local.sh
        ./scripts/health-check-local.sh
    else
        log_warning "Health check script not found"
    fi
}

debug_service() {
    local service=$1
    
    if [ -z "$service" ]; then
        log_error "Please specify service name"
        return 1
    fi
    
    log_header "DEBUG INFO FOR $service"
    
    log_info "Container status:"
    docker-compose ps "$service"
    
    echo
    log_info "Container logs (last 50 lines):"
    docker-compose logs --tail=50 "$service"
    
    echo
    log_info "Container inspect:"
    docker inspect $(docker-compose ps -q "$service") 2>/dev/null || log_warning "Container not running"
    
    echo
    log_info "Resource usage:"
    docker stats --no-stream $(docker-compose ps -q "$service") 2>/dev/null || log_warning "Container not running"
}

run_tests() {
    local test_type=${1:-"unit"}
    
    log_header "RUNNING TESTS"
    
    case $test_type in
        "unit")
            log_info "Running unit tests..."
            python -m pytest tests/unit/ -v --tb=short
            ;;
        "integration")
            log_info "Running integration tests..."
            python -m pytest tests/integration/ -v --tb=short
            ;;
        "e2e")
            log_info "Running end-to-end tests..."
            python -m pytest tests/e2e/ -v --tb=short
            ;;
        "all")
            log_info "Running all tests..."
            python -m pytest tests/ -v --tb=short
            ;;
        *)
            log_error "Unknown test type: $test_type"
            log_info "Available types: unit, integration, e2e, all"
            return 1
            ;;
    esac
}

run_lint() {
    log_header "CODE LINTING"
    
    log_info "Running Python linting..."
    find . -name "*.py" -not -path "./.*" -not -path "./venv/*" -not -path "./.venv/*" | xargs pylint || true
    
    log_info "Running JavaScript/TypeScript linting..."
    find apps/ -name "*.js" -o -name "*.ts" -o -name "*.tsx" | xargs eslint || true
}

format_code() {
    log_header "CODE FORMATTING"
    
    log_info "Formatting Python code..."
    find . -name "*.py" -not -path "./.*" -not -path "./venv/*" -not -path "./.venv/*" | xargs black
    
    log_info "Formatting JavaScript/TypeScript code..."
    find apps/ -name "*.js" -o -name "*.ts" -o -name "*.tsx" | xargs prettier --write || true
}

# Monitoring functions
open_monitor() {
    log_info "Opening monitoring dashboards..."
    
    if command -v open >/dev/null 2>&1; then
        # macOS
        open "http://localhost:3000"  # Grafana
        open "http://localhost:9090"  # Prometheus
        open "http://localhost:80"    # Main dashboard
    elif command -v xdg-open >/dev/null 2>&1; then
        # Linux
        xdg-open "http://localhost:3000" &
        xdg-open "http://localhost:9090" &
        xdg-open "http://localhost:80" &
    else
        log_info "Please open these URLs manually:"
        echo "  Grafana:    http://localhost:3000"
        echo "  Prometheus: http://localhost:9090"
        echo "  Dashboard:  http://localhost:80"
    fi
}

show_metrics() {
    log_header "SYSTEM METRICS"
    
    log_info "Docker system info:"
    docker system df
    
    echo
    log_info "Container resource usage:"
    docker stats --no-stream
    
    echo
    log_info "Network usage:"
    docker network ls
}

# Main command dispatcher
main() {
    case ${1:-""} in
        "start")
            start_services "$2"
            ;;
        "stop")
            stop_services "$2"
            ;;
        "restart")
            restart_services "$2"
            ;;
        "logs")
            show_logs "$2"
            ;;
        "status")
            show_status
            ;;
        "ps")
            show_ps
            ;;
        "db-reset")
            db_reset
            ;;
        "db-migrate")
            db_migrate
            ;;
        "db-seed")
            db_seed
            ;;
        "db-backup")
            db_backup
            ;;
        "db-restore")
            db_restore "$2"
            ;;
        "db-shell")
            db_shell
            ;;
        "redis-shell")
            redis_shell
            ;;
        "build")
            build_services "$2"
            ;;
        "clean")
            clean_system
            ;;
        "health")
            run_health_check
            ;;
        "debug")
            debug_service "$2"
            ;;
        "test")
            run_tests "$2"
            ;;
        "lint")
            run_lint
            ;;
        "format")
            format_code
            ;;
        "monitor")
            open_monitor
            ;;
        "metrics")
            show_metrics
            ;;
        "help"|"-h"|"--help"|"")
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"