#!/bin/bash

# ===========================================
# Sophia AI Database Migration Manager
# ===========================================
# Comprehensive database migration and schema management system
# Supports PostgreSQL and Redis with rollback capabilities

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MIGRATIONS_DIR="$SCRIPT_DIR/migrations"
SEEDS_DIR="$SCRIPT_DIR/seeds"
BACKUPS_DIR="$PROJECT_ROOT/backups/database"

# Environment configuration
ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/.env.local}"
if [[ -f "$ENV_FILE" ]]; then
    source "$ENV_FILE"
fi

# Database configuration
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-sophia}"
POSTGRES_USER="${POSTGRES_USER:-sophia}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-sophia_secure_2024}"

REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6380}"

# Migration table
MIGRATION_TABLE="schema_migrations"

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE} Sophia AI - Database Migration Manager${NC}"
    echo -e "${BLUE}============================================${NC}"
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
    
    if ! command -v psql &> /dev/null; then
        missing_deps+=("postgresql-client")
    fi
    
    if ! command -v redis-cli &> /dev/null; then
        missing_deps+=("redis-tools")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        print_info "Install with: brew install ${missing_deps[*]}"
        exit 1
    fi
}

# Test database connections
test_connections() {
    print_step "Testing database connections..."
    
    # Test PostgreSQL
    if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" >/dev/null 2>&1; then
        print_success "PostgreSQL connection successful"
    else
        print_error "Failed to connect to PostgreSQL"
        print_info "Host: $POSTGRES_HOST:$POSTGRES_PORT"
        print_info "Database: $POSTGRES_DB"
        print_info "User: $POSTGRES_USER"
        exit 1
    fi
    
    # Test Redis
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping >/dev/null 2>&1; then
        print_success "Redis connection successful"
    else
        print_error "Failed to connect to Redis"
        print_info "Host: $REDIS_HOST:$REDIS_PORT"
        exit 1
    fi
}

# Initialize migration system
init_migration_system() {
    print_step "Initializing migration system..."
    
    # Create directories
    mkdir -p "$MIGRATIONS_DIR"
    mkdir -p "$SEEDS_DIR"
    mkdir -p "$BACKUPS_DIR"
    
    # Create migration tracking table
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << EOF
CREATE TABLE IF NOT EXISTS $MIGRATION_TABLE (
    id SERIAL PRIMARY KEY,
    version VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64),
    execution_time_ms INTEGER,
    rollback_sql TEXT
);

CREATE INDEX IF NOT EXISTS idx_schema_migrations_version ON $MIGRATION_TABLE(version);
CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied_at ON $MIGRATION_TABLE(applied_at);
EOF
    
    print_success "Migration system initialized"
}

# Create new migration
create_migration() {
    local name="$1"
    if [[ -z "$name" ]]; then
        print_error "Migration name is required"
        echo "Usage: $0 create <migration_name>"
        exit 1
    fi
    
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local version="${timestamp}"
    local filename="${version}_$(echo "$name" | tr ' ' '_' | tr '[:upper:]' '[:lower:]').sql"
    local filepath="$MIGRATIONS_DIR/$filename"
    
    print_step "Creating migration: $filename"
    
    cat > "$filepath" << EOF
-- Migration: $name
-- Version: $version
-- Created: $(date)

-- ===========================================
-- UP Migration
-- ===========================================

BEGIN;

-- Add your migration SQL here
-- Example:
-- CREATE TABLE example_table (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(255) NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- Update migration record
-- This will be handled automatically

COMMIT;

-- ===========================================
-- DOWN Migration (Rollback)
-- ===========================================

-- ROLLBACK_START
-- Add your rollback SQL here
-- Example:
-- DROP TABLE IF EXISTS example_table;
-- ROLLBACK_END
EOF
    
    print_success "Migration created: $filepath"
    print_info "Edit the migration file and run: $0 migrate up"
}

# Get pending migrations
get_pending_migrations() {
    local applied_versions
    applied_versions=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT version FROM $MIGRATION_TABLE ORDER BY version;")
    
    local pending_migrations=()
    for migration_file in "$MIGRATIONS_DIR"/*.sql; do
        if [[ -f "$migration_file" ]]; then
            local version=$(basename "$migration_file" | cut -d'_' -f1-2)
            if ! echo "$applied_versions" | grep -q "$version"; then
                pending_migrations+=("$migration_file")
            fi
        fi
    done
    
    printf '%s\n' "${pending_migrations[@]}" | sort
}

# Calculate file checksum
calculate_checksum() {
    local file="$1"
    if [[ -f "$file" ]]; then
        if command -v sha256sum &> /dev/null; then
            sha256sum "$file" | cut -d' ' -f1
        elif command -v shasum &> /dev/null; then
            shasum -a 256 "$file" | cut -d' ' -f1
        else
            md5 -q "$file" 2>/dev/null || md5sum "$file" | cut -d' ' -f1
        fi
    fi
}

# Run migrations up
migrate_up() {
    print_step "Running pending migrations..."
    
    local pending_migrations
    mapfile -t pending_migrations < <(get_pending_migrations)
    
    if [[ ${#pending_migrations[@]} -eq 0 ]]; then
        print_success "No pending migrations"
        return 0
    fi
    
    for migration_file in "${pending_migrations[@]}"; do
        local version=$(basename "$migration_file" | cut -d'_' -f1-2)
        local name=$(basename "$migration_file" .sql | sed "s/${version}_//")
        local checksum=$(calculate_checksum "$migration_file")
        
        print_info "Applying migration: $version - $name"
        
        local start_time=$(date +%s%3N)
        
        # Extract UP migration (everything before ROLLBACK_START)
        local up_sql=$(sed '/-- ROLLBACK_START/q' "$migration_file" | head -n -1)
        
        # Extract DOWN migration (between ROLLBACK_START and ROLLBACK_END)
        local down_sql=$(sed -n '/-- ROLLBACK_START/,/-- ROLLBACK_END/p' "$migration_file" | 
                        grep -v '-- ROLLBACK_START' | 
                        grep -v '-- ROLLBACK_END')
        
        # Run the migration
        if echo "$up_sql" | PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1; then
            local end_time=$(date +%s%3N)
            local execution_time=$((end_time - start_time))
            
            # Record migration
            PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << EOF
INSERT INTO $MIGRATION_TABLE (version, name, checksum, execution_time_ms, rollback_sql)
VALUES ('$version', '$name', '$checksum', $execution_time, \$rollback\$$down_sql\$rollback\$);
EOF
            
            print_success "Applied migration: $version (${execution_time}ms)"
        else
            print_error "Failed to apply migration: $version"
            exit 1
        fi
    done
    
    print_success "All migrations completed successfully"
}

# Rollback migration
migrate_down() {
    local steps="${1:-1}"
    
    print_step "Rolling back $steps migration(s)..."
    
    local applied_migrations
    mapfile -t applied_migrations < <(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT version, name, rollback_sql FROM $MIGRATION_TABLE ORDER BY version DESC LIMIT $steps;")
    
    if [[ ${#applied_migrations[@]} -eq 0 ]]; then
        print_warning "No migrations to rollback"
        return 0
    fi
    
    for migration_info in "${applied_migrations[@]}"; do
        IFS='|' read -r version name rollback_sql <<< "$migration_info"
        version=$(echo "$version" | xargs)
        name=$(echo "$name" | xargs)
        
        print_info "Rolling back migration: $version - $name"
        
        if [[ -n "$rollback_sql" ]] && [[ "$rollback_sql" != " " ]]; then
            if echo "$rollback_sql" | PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1; then
                # Remove migration record
                PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << EOF
DELETE FROM $MIGRATION_TABLE WHERE version = '$version';
EOF
                print_success "Rolled back migration: $version"
            else
                print_error "Failed to rollback migration: $version"
                exit 1
            fi
        else
            print_warning "No rollback SQL found for migration: $version"
        fi
    done
    
    print_success "Rollback completed successfully"
}

# Show migration status
show_status() {
    print_step "Migration Status:"
    echo
    
    # Applied migrations
    print_info "Applied Migrations:"
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << EOF
\x off
SELECT 
    version,
    name,
    applied_at,
    execution_time_ms || 'ms' as execution_time
FROM $MIGRATION_TABLE 
ORDER BY version;
EOF
    
    echo
    
    # Pending migrations
    print_info "Pending Migrations:"
    local pending_migrations
    mapfile -t pending_migrations < <(get_pending_migrations)
    
    if [[ ${#pending_migrations[@]} -eq 0 ]]; then
        echo "  No pending migrations"
    else
        for migration_file in "${pending_migrations[@]}"; do
            local version=$(basename "$migration_file" | cut -d'_' -f1-2)
            local name=$(basename "$migration_file" .sql | sed "s/${version}_//")
            echo "  $version - $name"
        done
    fi
    echo
}

# Reset database
reset_database() {
    print_warning "This will drop and recreate all database objects!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Operation cancelled"
        return 0
    fi
    
    print_step "Resetting database..."
    
    # Drop all tables except migration table
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << 'EOF'
DO $$ 
DECLARE 
    r RECORD;
BEGIN
    -- Drop all tables except schema_migrations
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'schema_migrations') 
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
    
    -- Drop all sequences
    FOR r IN (SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public') 
    LOOP
        EXECUTE 'DROP SEQUENCE IF EXISTS ' || quote_ident(r.sequence_name) || ' CASCADE';
    END LOOP;
    
    -- Drop all views
    FOR r IN (SELECT viewname FROM pg_views WHERE schemaname = 'public') 
    LOOP
        EXECUTE 'DROP VIEW IF EXISTS ' || quote_ident(r.viewname) || ' CASCADE';
    END LOOP;
END $$;
EOF
    
    # Clear Redis
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" FLUSHDB
    
    # Clear migration history
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "DELETE FROM $MIGRATION_TABLE;"
    
    print_success "Database reset completed"
    print_info "Run migrations with: $0 migrate up"
}

# Seed database
seed_database() {
    print_step "Seeding database..."
    
    if [[ ! -d "$SEEDS_DIR" ]] || [[ -z "$(ls -A "$SEEDS_DIR" 2>/dev/null)" ]]; then
        print_warning "No seed files found in $SEEDS_DIR"
        return 0
    fi
    
    for seed_file in "$SEEDS_DIR"/*.sql; do
        if [[ -f "$seed_file" ]]; then
            local seed_name=$(basename "$seed_file" .sql)
            print_info "Running seed: $seed_name"
            
            if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$seed_file"; then
                print_success "Seed completed: $seed_name"
            else
                print_error "Seed failed: $seed_name"
                exit 1
            fi
        fi
    done
    
    print_success "Database seeding completed"
}

# Backup database
backup_database() {
    print_step "Creating database backup..."
    
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$BACKUPS_DIR/sophia_backup_$timestamp.sql"
    local redis_backup="$BACKUPS_DIR/redis_backup_$timestamp.rdb"
    
    mkdir -p "$BACKUPS_DIR"
    
    # Backup PostgreSQL
    if PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$backup_file"; then
        print_success "PostgreSQL backup created: $backup_file"
    else
        print_error "Failed to create PostgreSQL backup"
        exit 1
    fi
    
    # Backup Redis
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --rdb "$redis_backup" >/dev/null 2>&1; then
        print_success "Redis backup created: $redis_backup"
    else
        print_warning "Failed to create Redis backup (this is normal if Redis is empty)"
    fi
    
    # Compress backups
    if command -v gzip &> /dev/null; then
        gzip "$backup_file"
        print_success "Backup compressed: ${backup_file}.gz"
        if [[ -f "$redis_backup" ]]; then
            gzip "$redis_backup"
            print_success "Redis backup compressed: ${redis_backup}.gz"
        fi
    fi
}

# Restore database
restore_database() {
    local backup_file="$1"
    
    if [[ -z "$backup_file" ]]; then
        print_error "Backup file is required"
        echo "Usage: $0 restore <backup_file>"
        echo
        echo "Available backups:"
        ls -la "$BACKUPS_DIR"/*.sql* 2>/dev/null || echo "  No backups found"
        exit 1
    fi
    
    if [[ ! -f "$backup_file" ]]; then
        print_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    print_warning "This will replace all current data!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Operation cancelled"
        return 0
    fi
    
    print_step "Restoring database from: $backup_file"
    
    # Determine if file is compressed
    local restore_cmd="cat"
    if [[ "$backup_file" == *.gz ]]; then
        restore_cmd="zcat"
    fi
    
    # Restore PostgreSQL
    if $restore_cmd "$backup_file" | PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB"; then
        print_success "Database restored successfully"
    else
        print_error "Failed to restore database"
        exit 1
    fi
}

# Show help
show_help() {
    cat << EOF
Sophia AI Database Migration Manager

Usage: $0 <command> [options]

Commands:
  init                 Initialize migration system
  create <name>        Create new migration file
  migrate up           Apply all pending migrations
  migrate down [N]     Rollback N migrations (default: 1)
  status              Show migration status
  reset               Reset database (drops all data)
  seed                Run database seeds
  backup              Create database backup
  restore <file>      Restore database from backup
  test                Test database connections

Examples:
  $0 init
  $0 create "add_user_table"
  $0 migrate up
  $0 migrate down 2
  $0 status
  $0 backup
  $0 restore backups/sophia_backup_20241128_120000.sql.gz

Environment Variables:
  ENV_FILE            Environment file to load (default: .env.local)
  POSTGRES_HOST       PostgreSQL host (default: localhost)
  POSTGRES_PORT       PostgreSQL port (default: 5432)
  POSTGRES_DB         PostgreSQL database (default: sophia)
  POSTGRES_USER       PostgreSQL user (default: sophia)
  POSTGRES_PASSWORD   PostgreSQL password

EOF
}

# Main execution
main() {
    print_header
    
    case "${1:-}" in
        "init")
            check_dependencies
            test_connections
            init_migration_system
            ;;
        "create")
            check_dependencies
            test_connections
            init_migration_system
            create_migration "$2"
            ;;
        "migrate")
            case "${2:-}" in
                "up")
                    check_dependencies
                    test_connections
                    init_migration_system
                    migrate_up
                    ;;
                "down")
                    check_dependencies
                    test_connections
                    init_migration_system
                    migrate_down "${3:-1}"
                    ;;
                *)
                    print_error "Invalid migrate command: ${2:-}"
                    echo "Usage: $0 migrate [up|down]"
                    exit 1
                    ;;
            esac
            ;;
        "status")
            check_dependencies
            test_connections
            init_migration_system
            show_status
            ;;
        "reset")
            check_dependencies
            test_connections
            init_migration_system
            reset_database
            ;;
        "seed")
            check_dependencies
            test_connections
            seed_database
            ;;
        "backup")
            check_dependencies
            test_connections
            backup_database
            ;;
        "restore")
            check_dependencies
            test_connections
            restore_database "$2"
            ;;
        "test")
            check_dependencies
            test_connections
            print_success "All database connections are working"
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