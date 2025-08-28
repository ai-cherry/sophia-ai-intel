#!/bin/bash

# ===========================================
# Sophia AI Backup and Disaster Recovery
# ===========================================
# Comprehensive backup and disaster recovery system
# Supports PostgreSQL, Redis, and application data

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
BACKUP_DIR="${BACKUP_BASE_DIR:-$PROJECT_ROOT/backups}"
CONFIG_DIR="$PROJECT_ROOT/config"

# Timestamp for backups
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
DATE_PREFIX=$(date '+%Y%m%d')

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

# Backup retention settings
DAILY_RETENTION_DAYS="${BACKUP_DAILY_RETENTION:-7}"
WEEKLY_RETENTION_WEEKS="${BACKUP_WEEKLY_RETENTION:-4}"
MONTHLY_RETENTION_MONTHS="${BACKUP_MONTHLY_RETENTION:-6}"

# S3 configuration (optional)
AWS_S3_BUCKET="${BACKUP_S3_BUCKET:-}"
AWS_REGION="${BACKUP_S3_REGION:-us-west-2}"

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE} Sophia AI - Backup & Disaster Recovery${NC}"
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
    
    if ! command -v pg_dump &> /dev/null; then
        missing_deps+=("postgresql-client")
    fi
    
    if ! command -v redis-cli &> /dev/null; then
        missing_deps+=("redis-tools")
    fi
    
    if [[ -n "$AWS_S3_BUCKET" ]] && ! command -v aws &> /dev/null; then
        missing_deps+=("awscli")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        print_info "Install with: brew install ${missing_deps[*]}"
        exit 1
    fi
}

# Create backup directories
create_backup_dirs() {
    print_step "Creating backup directories..."
    
    local dirs=(
        "$BACKUP_DIR/postgres"
        "$BACKUP_DIR/redis" 
        "$BACKUP_DIR/application"
        "$BACKUP_DIR/logs"
        "$BACKUP_DIR/archive"
        "$BACKUP_DIR/daily"
        "$BACKUP_DIR/weekly"
        "$BACKUP_DIR/monthly"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done
    
    print_success "Backup directories created"
}

# Test database connections
test_connections() {
    print_step "Testing database connections..."
    
    # Test PostgreSQL
    if PGPASSWORD="$POSTGRES_PASSWORD" pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
        print_success "PostgreSQL connection successful"
    else
        print_error "Failed to connect to PostgreSQL"
        return 1
    fi
    
    # Test Redis
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping >/dev/null 2>&1; then
        print_success "Redis connection successful"
    else
        print_error "Failed to connect to Redis"
        return 1
    fi
}

# Backup PostgreSQL database
backup_postgres() {
    local backup_type="$1"
    local backup_file="$BACKUP_DIR/postgres/sophia_${backup_type}_${TIMESTAMP}.sql"
    
    print_step "Creating PostgreSQL backup ($backup_type)..."
    
    # Create compressed backup with custom format for better performance
    if PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --format=custom \
        --no-owner \
        --no-privileges \
        --verbose \
        --file="${backup_file}.dump" 2>/dev/null; then
        
        # Also create SQL format for easier inspection
        PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
            -h "$POSTGRES_HOST" \
            -p "$POSTGRES_PORT" \
            -U "$POSTGRES_USER" \
            -d "$POSTGRES_DB" \
            --no-owner \
            --no-privileges > "$backup_file"
        
        # Compress SQL backup
        gzip "$backup_file"
        
        local file_size=$(du -h "${backup_file}.gz" | cut -f1)
        print_success "PostgreSQL backup created: ${backup_file}.gz ($file_size)"
        
        # Create metadata file
        cat > "${backup_file%.sql}.meta" << EOF
backup_type: $backup_type
database: $POSTGRES_DB
timestamp: $TIMESTAMP
host: $POSTGRES_HOST:$POSTGRES_PORT
format: custom+sql
size: $file_size
created_at: $(date -Iseconds)
retention_policy: ${backup_type}
EOF
        
        echo "${backup_file}.gz"
    else
        print_error "Failed to create PostgreSQL backup"
        return 1
    fi
}

# Backup Redis database
backup_redis() {
    local backup_type="$1"
    local backup_file="$BACKUP_DIR/redis/redis_${backup_type}_${TIMESTAMP}.rdb"
    
    print_step "Creating Redis backup ($backup_type)..."
    
    # Create Redis backup using SAVE command
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --rdb "$backup_file" >/dev/null 2>&1; then
        
        # Compress the backup
        gzip "$backup_file"
        
        local file_size=$(du -h "${backup_file}.gz" | cut -f1)
        print_success "Redis backup created: ${backup_file}.gz ($file_size)"
        
        # Create metadata file
        cat > "${backup_file%.rdb}.meta" << EOF
backup_type: $backup_type
database: redis
timestamp: $TIMESTAMP
host: $REDIS_HOST:$REDIS_PORT
format: rdb
size: $file_size
created_at: $(date -Iseconds)
retention_policy: ${backup_type}
EOF
        
        echo "${backup_file}.gz"
    else
        print_warning "Redis backup failed (this is normal if Redis is empty)"
        return 0
    fi
}

# Backup application data
backup_application_data() {
    local backup_type="$1"
    local backup_file="$BACKUP_DIR/application/app_data_${backup_type}_${TIMESTAMP}.tar.gz"
    
    print_step "Creating application data backup ($backup_type)..."
    
    local app_data_dirs=(
        "$PROJECT_ROOT/uploads"
        "$PROJECT_ROOT/logs"
        "$PROJECT_ROOT/config"
        "$PROJECT_ROOT/ssl"
        "$PROJECT_ROOT/.env*"
    )
    
    local existing_dirs=()
    for dir in "${app_data_dirs[@]}"; do
        if [[ -e "$dir" ]]; then
            existing_dirs+=("$dir")
        fi
    done
    
    if [[ ${#existing_dirs[@]} -gt 0 ]]; then
        tar -czf "$backup_file" -C "$PROJECT_ROOT" "${existing_dirs[@]#$PROJECT_ROOT/}" 2>/dev/null
        
        local file_size=$(du -h "$backup_file" | cut -f1)
        print_success "Application data backup created: $backup_file ($file_size)"
        
        # Create metadata file
        cat > "${backup_file%.tar.gz}.meta" << EOF
backup_type: $backup_type
content: application_data
timestamp: $TIMESTAMP
includes: $(printf '%s,' "${existing_dirs[@]}")
format: tar.gz
size: $file_size
created_at: $(date -Iseconds)
retention_policy: ${backup_type}
EOF
        
        echo "$backup_file"
    else
        print_info "No application data to backup"
        return 0
    fi
}

# Upload to S3 (if configured)
upload_to_s3() {
    local backup_file="$1"
    local backup_type="$2"
    
    if [[ -n "$AWS_S3_BUCKET" ]] && [[ -f "$backup_file" ]]; then
        print_step "Uploading to S3: $(basename "$backup_file")"
        
        local s3_key="sophia-ai-backups/$backup_type/$(date +%Y)/%m/$(basename "$backup_file")"
        
        if aws s3 cp "$backup_file" "s3://$AWS_S3_BUCKET/$s3_key" \
            --region "$AWS_REGION" \
            --storage-class STANDARD_IA >/dev/null 2>&1; then
            
            print_success "Uploaded to S3: s3://$AWS_S3_BUCKET/$s3_key"
            
            # Upload metadata too
            if [[ -f "${backup_file%.gz}.meta" ]]; then
                aws s3 cp "${backup_file%.gz}.meta" "s3://$AWS_S3_BUCKET/${s3_key%.gz}.meta" \
                    --region "$AWS_REGION" >/dev/null 2>&1
            fi
        else
            print_warning "Failed to upload to S3"
        fi
    fi
}

# Create full backup
create_full_backup() {
    local backup_type="${1:-manual}"
    
    print_step "Creating full backup ($backup_type)..."
    
    local backup_files=()
    
    # Backup PostgreSQL
    if postgres_backup=$(backup_postgres "$backup_type"); then
        backup_files+=("$postgres_backup")
        upload_to_s3 "$postgres_backup" "$backup_type"
    fi
    
    # Backup Redis
    if redis_backup=$(backup_redis "$backup_type"); then
        backup_files+=("$redis_backup")
        upload_to_s3 "$redis_backup" "$backup_type"
    fi
    
    # Backup application data
    if app_backup=$(backup_application_data "$backup_type"); then
        backup_files+=("$app_backup")
        upload_to_s3 "$app_backup" "$backup_type"
    fi
    
    # Create backup manifest
    local manifest_file="$BACKUP_DIR/backup_manifest_${backup_type}_${TIMESTAMP}.json"
    cat > "$manifest_file" << EOF
{
    "backup_id": "${backup_type}_${TIMESTAMP}",
    "backup_type": "$backup_type",
    "created_at": "$(date -Iseconds)",
    "files": [
        $(printf '"%s",' "${backup_files[@]}" | sed 's/,$//')
    ],
    "total_files": ${#backup_files[@]},
    "database": {
        "postgres_host": "$POSTGRES_HOST:$POSTGRES_PORT",
        "postgres_db": "$POSTGRES_DB",
        "redis_host": "$REDIS_HOST:$REDIS_PORT"
    },
    "environment": "$(basename "$ENV_FILE")"
}
EOF
    
    print_success "Full backup completed: $manifest_file"
    print_info "Backup files: ${#backup_files[@]}"
    
    # Link to daily/weekly/monthly directories
    case "$backup_type" in
        "daily")
            ln -sf "$manifest_file" "$BACKUP_DIR/daily/latest_backup.json"
            ;;
        "weekly")
            ln -sf "$manifest_file" "$BACKUP_DIR/weekly/latest_backup.json"
            ;;
        "monthly")
            ln -sf "$manifest_file" "$BACKUP_DIR/monthly/latest_backup.json"
            ;;
    esac
}

# Restore from backup
restore_from_backup() {
    local backup_manifest="$1"
    
    if [[ ! -f "$backup_manifest" ]]; then
        print_error "Backup manifest not found: $backup_manifest"
        exit 1
    fi
    
    print_warning "This will replace all current data!"
    read -p "Are you sure you want to restore? (type 'yes' to confirm): " -r
    if [[ "$REPLY" != "yes" ]]; then
        print_info "Restore cancelled"
        return 0
    fi
    
    print_step "Restoring from backup: $backup_manifest"
    
    # Parse manifest
    local backup_files
    mapfile -t backup_files < <(jq -r '.files[]' "$backup_manifest" 2>/dev/null || echo "")
    
    for backup_file in "${backup_files[@]}"; do
        if [[ -z "$backup_file" ]]; then
            continue
        fi
        
        case "$backup_file" in
            *postgres*.sql.gz)
                restore_postgres "$backup_file"
                ;;
            *redis*.rdb.gz)
                restore_redis "$backup_file"
                ;;
            *app_data*.tar.gz)
                restore_application_data "$backup_file"
                ;;
        esac
    done
    
    print_success "Restore completed from: $backup_manifest"
}

# Restore PostgreSQL
restore_postgres() {
    local backup_file="$1"
    
    print_step "Restoring PostgreSQL from: $(basename "$backup_file")"
    
    # Decompress if needed
    local sql_file="${backup_file%.gz}"
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" > "$sql_file"
    fi
    
    # Drop and recreate database
    PGPASSWORD="$POSTGRES_PASSWORD" dropdb \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        --if-exists "$POSTGRES_DB"
    
    PGPASSWORD="$POSTGRES_PASSWORD" createdb \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        "$POSTGRES_DB"
    
    # Restore database
    if PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        -f "$sql_file" >/dev/null; then
        
        print_success "PostgreSQL restored successfully"
        
        # Cleanup temporary file
        if [[ "$backup_file" == *.gz ]]; then
            rm -f "$sql_file"
        fi
    else
        print_error "Failed to restore PostgreSQL"
        exit 1
    fi
}

# Restore Redis
restore_redis() {
    local backup_file="$1"
    
    print_step "Restoring Redis from: $(basename "$backup_file")"
    
    # Flush current Redis data
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" FLUSHALL
    
    # Decompress and restore
    local rdb_file="${backup_file%.gz}"
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" > "$rdb_file"
    fi
    
    # Note: Redis RDB restore requires Redis server restart with the RDB file
    print_warning "Redis RDB restore requires manual intervention:"
    print_info "1. Stop Redis server"
    print_info "2. Copy $rdb_file to Redis data directory as dump.rdb"
    print_info "3. Start Redis server"
}

# Restore application data
restore_application_data() {
    local backup_file="$1"
    
    print_step "Restoring application data from: $(basename "$backup_file")"
    
    if tar -xzf "$backup_file" -C "$PROJECT_ROOT"; then
        print_success "Application data restored successfully"
    else
        print_error "Failed to restore application data"
        exit 1
    fi
}

# Clean old backups
cleanup_old_backups() {
    print_step "Cleaning up old backups..."
    
    # Daily backups
    find "$BACKUP_DIR/postgres" -name "*daily*.sql.gz" -mtime +$DAILY_RETENTION_DAYS -delete 2>/dev/null || true
    find "$BACKUP_DIR/redis" -name "*daily*.rdb.gz" -mtime +$DAILY_RETENTION_DAYS -delete 2>/dev/null || true
    find "$BACKUP_DIR/application" -name "*daily*.tar.gz" -mtime +$DAILY_RETENTION_DAYS -delete 2>/dev/null || true
    
    # Weekly backups (convert weeks to days)
    local weekly_days=$((WEEKLY_RETENTION_WEEKS * 7))
    find "$BACKUP_DIR/postgres" -name "*weekly*.sql.gz" -mtime +$weekly_days -delete 2>/dev/null || true
    find "$BACKUP_DIR/redis" -name "*weekly*.rdb.gz" -mtime +$weekly_days -delete 2>/dev/null || true
    find "$BACKUP_DIR/application" -name "*weekly*.tar.gz" -mtime +$weekly_days -delete 2>/dev/null || true
    
    # Monthly backups (convert months to days, approximately)
    local monthly_days=$((MONTHLY_RETENTION_MONTHS * 30))
    find "$BACKUP_DIR/postgres" -name "*monthly*.sql.gz" -mtime +$monthly_days -delete 2>/dev/null || true
    find "$BACKUP_DIR/redis" -name "*monthly*.rdb.gz" -mtime +$monthly_days -delete 2>/dev/null || true
    find "$BACKUP_DIR/application" -name "*monthly*.tar.gz" -mtime +$monthly_days -delete 2>/dev/null || true
    
    # Clean metadata files
    find "$BACKUP_DIR" -name "*.meta" -mtime +$DAILY_RETENTION_DAYS -delete 2>/dev/null || true
    
    print_success "Old backups cleaned up"
}

# List available backups
list_backups() {
    print_step "Available backups:"
    echo
    
    local backup_types=("daily" "weekly" "monthly")
    
    for backup_type in "${backup_types[@]}"; do
        print_info "$backup_type backups:"
        
        local manifests
        mapfile -t manifests < <(find "$BACKUP_DIR" -name "*${backup_type}*manifest*.json" | sort -r | head -5)
        
        if [[ ${#manifests[@]} -eq 0 ]]; then
            echo "  No $backup_type backups found"
        else
            for manifest in "${manifests[@]}"; do
                if [[ -f "$manifest" ]]; then
                    local backup_id
                    local created_at
                    backup_id=$(jq -r '.backup_id' "$manifest" 2>/dev/null || echo "unknown")
                    created_at=$(jq -r '.created_at' "$manifest" 2>/dev/null || echo "unknown")
                    echo "  $backup_id ($created_at)"
                fi
            done
        fi
        echo
    done
    
    # Manual backups
    print_info "Manual backups:"
    local manual_manifests
    mapfile -t manual_manifests < <(find "$BACKUP_DIR" -name "*manual*manifest*.json" | sort -r | head -10)
    
    if [[ ${#manual_manifests[@]} -eq 0 ]]; then
        echo "  No manual backups found"
    else
        for manifest in "${manual_manifests[@]}"; do
            if [[ -f "$manifest" ]]; then
                local backup_id
                local created_at
                backup_id=$(jq -r '.backup_id' "$manifest" 2>/dev/null || echo "unknown")
                created_at=$(jq -r '.created_at' "$manifest" 2>/dev/null || echo "unknown")
                echo "  $backup_id ($created_at)"
            fi
        done
    fi
}

# Verify backup integrity
verify_backup() {
    local backup_manifest="$1"
    
    if [[ ! -f "$backup_manifest" ]]; then
        print_error "Backup manifest not found: $backup_manifest"
        exit 1
    fi
    
    print_step "Verifying backup integrity: $(basename "$backup_manifest")"
    
    local backup_files
    mapfile -t backup_files < <(jq -r '.files[]' "$backup_manifest" 2>/dev/null || echo "")
    
    local verified=0
    local total=${#backup_files[@]}
    
    for backup_file in "${backup_files[@]}"; do
        if [[ -z "$backup_file" ]]; then
            continue
        fi
        
        if [[ -f "$backup_file" ]]; then
            case "$backup_file" in
                *.gz)
                    if gzip -t "$backup_file" 2>/dev/null; then
                        ((verified++))
                        print_success "✓ $(basename "$backup_file")"
                    else
                        print_error "✗ $(basename "$backup_file") - corrupted"
                    fi
                    ;;
                *)
                    if [[ -r "$backup_file" ]]; then
                        ((verified++))
                        print_success "✓ $(basename "$backup_file")"
                    else
                        print_error "✗ $(basename "$backup_file") - unreadable"
                    fi
                    ;;
            esac
        else
            print_error "✗ $(basename "$backup_file") - missing"
        fi
    done
    
    if [[ $verified -eq $total ]]; then
        print_success "Backup verification passed: $verified/$total files"
    else
        print_error "Backup verification failed: $verified/$total files"
        exit 1
    fi
}

# Show help
show_help() {
    cat << EOF
Sophia AI Backup & Disaster Recovery

Usage: $0 <command> [options]

Commands:
  backup [type]        Create backup (type: manual, daily, weekly, monthly)
  restore <manifest>   Restore from backup manifest file
  list                 List available backups
  verify <manifest>    Verify backup integrity
  cleanup              Clean up old backups
  test                 Test database connections

Examples:
  $0 backup manual
  $0 backup daily
  $0 restore backups/backup_manifest_daily_20241128_120000.json
  $0 list
  $0 verify backups/backup_manifest_daily_20241128_120000.json
  $0 cleanup

Environment Variables:
  BACKUP_BASE_DIR           Base backup directory (default: ./backups)
  BACKUP_DAILY_RETENTION    Daily backup retention days (default: 7)
  BACKUP_WEEKLY_RETENTION   Weekly backup retention weeks (default: 4)
  BACKUP_MONTHLY_RETENTION  Monthly backup retention months (default: 6)
  BACKUP_S3_BUCKET         S3 bucket for backup storage (optional)
  BACKUP_S3_REGION         S3 region (default: us-west-2)

EOF
}

# Main execution
main() {
    print_header
    
    case "${1:-}" in
        "backup")
            check_dependencies
            create_backup_dirs
            test_connections
            create_full_backup "${2:-manual}"
            ;;
        "restore")
            check_dependencies
            test_connections
            restore_from_backup "$2"
            ;;
        "list")
            list_backups
            ;;
        "verify")
            verify_backup "$2"
            ;;
        "cleanup")
            cleanup_old_backups
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