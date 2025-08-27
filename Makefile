# Sophia AI Intel - Database Operations Makefile
# ===============================================

# Neon Database Configuration
NEON_PROJECT_ID ?= rough-union-72390895
NEON_API_KEY ?= napi_r3gsuacduzw44nqdqav1u0hr2uv4bb2if48r8627jkxo7e4b2sxn92wsgf6zlxby
NEON_USER ?= neondb_owner
NEON_DB ?= neondb
NEON_ENDPOINT ?= ep-rough-dew-af6w48m3
NEON_BRANCH_ID ?= br-green-firefly-afykrx78

# Detect psql and pg_dump locations
PSQL := $(shell if [ -f "/opt/homebrew/opt/postgresql@15/bin/psql" ]; then echo "/opt/homebrew/opt/postgresql@15/bin/psql"; elif [ -f "/opt/homebrew/opt/postgresql@17/bin/psql" ]; then echo "/opt/homebrew/opt/postgresql@17/bin/psql"; elif command -v psql >/dev/null 2>&1; then echo "psql"; else echo "echo 'psql not found' >&2 && false"; fi)
PG_DUMP := $(shell if [ -f "/opt/homebrew/opt/postgresql@15/bin/pg_dump" ]; then echo "/opt/homebrew/opt/postgresql@15/bin/pg_dump"; elif [ -f "/opt/homebrew/opt/postgresql@17/bin/pg_dump" ]; then echo "/opt/homebrew/opt/postgresql@17/bin/pg_dump"; elif command -v pg_dump >/dev/null 2>&1; then echo "pg_dump"; else echo "echo 'pg_dump not found' >&2 && false"; fi)

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# Default target
.PHONY: help
help:
	@echo "$(GREEN)Sophia AI Intel - Database Operations$(NC)"
	@echo "======================================="
	@echo ""
	@echo "$(YELLOW)Neon Database Commands:$(NC)"
	@echo "  make psql-neon        - Connect to Neon interactively (passwordless)"
	@echo "  make test-neon        - Test Neon connection"
	@echo "  make migrate-neon     - Apply database migrations"
	@echo "  make backup-neon      - Create database backup"
	@echo ""
	@echo "$(YELLOW)Infrastructure Commands:$(NC)"
	@echo "  make test-infra       - Test all infrastructure components"
	@echo "  make status           - Show infrastructure status"
	@echo ""
	@echo "$(YELLOW)Development Commands:$(NC)"
	@echo "  make install-psql     - Install PostgreSQL client"
	@echo "  make setup-env        - Update .env with Neon configuration"
	@echo ""

# ====== Neon Database Operations ======

# Connect to Neon interactively
.PHONY: psql-neon
psql-neon:
	@echo "$(GREEN)Connecting to Neon (passwordless)...$(NC)"
	@echo "Using psql: $(PSQL)"
	@export NEON_PROJECT_ID=$(NEON_PROJECT_ID) && \
	export NEON_API_KEY=$(NEON_API_KEY) && \
	./scripts/psql_passwordless.sh -u $(NEON_USER) -d $(NEON_DB) || \
	(echo "$(YELLOW)Fallback: trying direct connection with endpoint...$(NC)" && \
	PGSSLMODE=require $(PSQL) -h pg.neon.tech -U $(NEON_USER) -d $(NEON_DB) \
		--options=endpoint=$(NEON_ENDPOINT))

# Test Neon connection
.PHONY: test-neon
test-neon:
	@echo "$(GREEN)Testing Neon connection...$(NC)"
	@echo "Using psql: $(PSQL)"
	@PGSSLMODE=require $(PSQL) -h pg.neon.tech -U $(NEON_USER) -d $(NEON_DB) \
		--options=endpoint=$(NEON_ENDPOINT) \
		-c "SELECT current_user, current_database(), version();" 2>/dev/null && \
		echo "$(GREEN)✅ Connection successful!$(NC)" || \
	(PGSSLMODE=require $(PSQL) -h pg.neon.tech -U $(NEON_USER) -d $(NEON_DB) \
		-c "SELECT current_user, current_database(), version();" 2>/dev/null && \
		echo "$(GREEN)✅ SNI connection successful!$(NC)" || \
		echo "$(RED)❌ Connection failed. Check your psql installation and credentials.$(NC)")

# Apply database migrations
.PHONY: migrate-neon
migrate-neon:
	@echo "$(GREEN)Applying migrations to Neon...$(NC)"
	@if [ ! -d "ops/sql" ] || [ -z "$$(ls -A ops/sql/*.sql 2>/dev/null)" ]; then \
		echo "$(YELLOW)No migrations found in ops/sql/$(NC)"; \
		if [ -f "libs/memory/schema.sql" ]; then \
			echo "$(GREEN)Found libs/memory/schema.sql - applying...$(NC)"; \
			PGSSLMODE=require $(PSQL) -h pg.neon.tech -U $(NEON_USER) -d $(NEON_DB) \
				--options=endpoint=$(NEON_ENDPOINT) -f libs/memory/schema.sql && \
			echo "$(GREEN)✅ Schema applied successfully$(NC)" || \
			echo "$(RED)❌ Failed to apply schema$(NC)"; \
		fi; \
	else \
		for sql in ops/sql/*.sql; do \
			echo "$(GREEN)Applying $$sql...$(NC)"; \
			PGSSLMODE=require $(PSQL) -h pg.neon.tech -U $(NEON_USER) -d $(NEON_DB) \
				--options=endpoint=$(NEON_ENDPOINT) -f $$sql || exit 1; \
		done; \
		echo "$(GREEN)✅ All migrations applied$(NC)"; \
	fi

# Create database backup
.PHONY: backup-neon
backup-neon:
	@echo "$(GREEN)Creating backup of Neon database...$(NC)"
	@mkdir -p backups
	@PGSSLMODE=require $(PG_DUMP) -h pg.neon.tech -U $(NEON_USER) -d $(NEON_DB) \
		--options=endpoint=$(NEON_ENDPOINT) \
		> backups/neon_backup_$$(date +%Y%m%d_%H%M%S).sql 2>/dev/null && \
		echo "$(GREEN)✅ Backup created in backups/$(NC)" || \
		echo "$(RED)❌ Backup failed. Check pg_dump: $(PG_DUMP)$(NC)"

# ====== Infrastructure Testing ======

# Test all infrastructure components
.PHONY: test-infra
test-infra:
	@echo "$(GREEN)Testing Infrastructure Components$(NC)"
	@echo "=================================="
	@echo ""
	@echo "$(YELLOW)1. Testing Qdrant...$(NC)"
	@python3 scripts/test_qdrant.py 2>/dev/null && echo "$(GREEN)✅ Qdrant OK$(NC)" || echo "$(RED)❌ Qdrant failed$(NC)"
	@echo ""
	@echo "$(YELLOW)2. Testing Redis...$(NC)"
	@python3 scripts/test_redis.py 2>/dev/null && echo "$(GREEN)✅ Redis OK$(NC)" || echo "$(RED)❌ Redis failed$(NC)"
	@echo ""
	@echo "$(YELLOW)3. Testing Lambda Labs...$(NC)"
	@python3 scripts/test_lambda_labs.py 2>/dev/null && echo "$(GREEN)✅ Lambda Labs OK$(NC)" || echo "$(RED)❌ Lambda Labs failed$(NC)"
	@echo ""
	@echo "$(YELLOW)4. Testing Neon...$(NC)"
	@$(MAKE) --no-print-directory test-neon

# Show infrastructure status
.PHONY: status
status:
	@echo "$(GREEN)Infrastructure Status$(NC)"
	@echo "===================="
	@echo ""
	@cat INFRASTRUCTURE_INITIALIZATION_STATUS.md | grep -E "^##|^###|✅|⚠️|❌" | sed 's/^/  /'

# ====== Development Setup ======

# Install PostgreSQL client
.PHONY: install-psql
install-psql:
	@echo "$(GREEN)Installing PostgreSQL client...$(NC)"
	@if [[ "$$(uname)" == "Darwin" ]]; then \
		echo "$(YELLOW)Installing for macOS...$(NC)"; \
		brew install postgresql || echo "$(RED)Failed to install. Is Homebrew installed?$(NC)"; \
	elif [[ "$$(uname)" == "Linux" ]]; then \
		echo "$(YELLOW)Installing for Linux...$(NC)"; \
		sudo apt-get update && sudo apt-get install -y postgresql-client || \
		echo "$(RED)Failed to install. Try: sudo apt-get install postgresql-client$(NC)"; \
	else \
		echo "$(RED)Unsupported OS. Please install PostgreSQL client manually.$(NC)"; \
	fi
	@$(PSQL) --version

# Update .env with Neon configuration
.PHONY: setup-env
setup-env:
	@echo "$(GREEN)Updating .env with Neon configuration...$(NC)"
	@if [ ! -f .env ]; then touch .env; fi
	@grep -q "NEON_PROJECT_ID" .env || echo "NEON_PROJECT_ID=$(NEON_PROJECT_ID)" >> .env
	@grep -q "NEON_API_KEY" .env || echo "NEON_API_KEY=$(NEON_API_KEY)" >> .env
	@grep -q "NEON_BRANCH_ID" .env || echo "NEON_BRANCH_ID=$(NEON_BRANCH_ID)" >> .env
	@grep -q "NEON_ENDPOINT_ID" .env || echo "NEON_ENDPOINT_ID=$(NEON_ENDPOINT)" >> .env
	@grep -q "NEON_ROLE" .env || echo "NEON_ROLE=$(NEON_USER)" >> .env
	@grep -q "NEON_DB" .env || echo "NEON_DB=$(NEON_DB)" >> .env
	@grep -q "NEON_PASSWORDLESS_HOST" .env || echo "NEON_PASSWORDLESS_HOST=pg.neon.tech" >> .env
	@echo "$(GREEN)✅ .env updated with Neon configuration$(NC)"

# ====== Quick Setup ======

# One-command setup for new developers
.PHONY: quick-setup
quick-setup: install-psql setup-env
	@echo ""
	@echo "$(GREEN)Quick setup complete!$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Test connection: make test-neon"
	@echo "  2. Apply migrations: make migrate-neon"
	@echo "  3. Test all infrastructure: make test-infra"

# Clean backup files older than 7 days
.PHONY: clean-backups
clean-backups:
	@echo "$(YELLOW)Cleaning old backup files...$(NC)"
	@find backups -name "*.sql" -type f -mtime +7 -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Old backups cleaned$(NC)"

.PHONY: all
all: test-infra