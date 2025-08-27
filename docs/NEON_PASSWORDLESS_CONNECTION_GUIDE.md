# Neon Passwordless Connection Guide

## Overview

This guide provides comprehensive instructions for connecting to Neon PostgreSQL using passwordless authentication, both for local development and cloud deployments.

## Quick Start Commands

### A) Modern libpq (SNI) - Most Likely to Work

```bash
PGSSLMODE=require psql -h pg.neon.tech -U neondb_owner -d neondb
```

### B) If Endpoint ID is Required

1. **Get your endpoint ID** (starts with `ep-…`):

```bash
# Requires NEON_API_KEY + NEON_PROJECT_ID in environment
curl -sS -H "Authorization: Bearer $NEON_API_KEY" \
  "https://console.neon.tech/api/v2/projects/$NEON_PROJECT_ID/endpoints" \
  | jq -r '.endpoints[] | select(.type=="read_write") | .id,.host,.branch_id'
```

2. **Connect with endpoint option**:

```bash
PGSSLMODE=require psql -h pg.neon.tech -U neondb_owner -d neondb \
  --options=endpoint=ep-rough-dew-af6w48m3
```

## Installation Requirements

### For Local Development

**macOS:**
```bash
brew install postgresql
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get install postgresql-client
```

### For Cloud Deployments

- **App Services**: Only need `asyncpg` Python library and DSN
- **Migration Containers**: Include `postgresql-client` in Docker image
- **CI/CD**: Add `psql` to GitHub Actions runner or build container

## Passwordless Connection Helper Script

Save as `scripts/psql_passwordless.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   NEON_PROJECT_ID=rough-... \
#   NEON_API_KEY=... \
#   ./scripts/psql_passwordless.sh [-u neondb_owner] [-d neondb]

USER="neondb_owner"
DB="neondb"
while getopts "u:d:" opt; do
  case $opt in
    u) USER="$OPTARG" ;;
    d) DB="$OPTARG" ;;
  esac
done

if ! command -v psql >/dev/null 2>&1; then
  echo "psql not found."
  echo "macOS: brew install postgresql"
  echo "Linux: sudo apt-get install postgresql-client"
  exit 2
fi

echo "== Trying passwordless (SNI) at pg.neon.tech =="
if PGSSLMODE=require psql -h pg.neon.tech -U "$USER" -d "$DB" \
   -c "select current_user, current_database();" 2>/dev/null; then
  echo "OK: SNI passwordless worked"
  exit 0
fi

echo "SNI attempt failed; trying explicit endpoint param..."
if [[ -z "${NEON_API_KEY:-}" || -z "${NEON_PROJECT_ID:-}" ]]; then
  echo "Need NEON_API_KEY and NEON_PROJECT_ID to auto-discover endpoint."
  exit 3
fi

EP_JSON=$(curl -sS -H "Authorization: Bearer $NEON_API_KEY" \
  "https://console.neon.tech/api/v2/projects/$NEON_PROJECT_ID/endpoints") || {
  echo "Failed to query endpoints via REST"; exit 4; }

EP_ID=$(echo "$EP_JSON" | awk '/"type":"read_write"/{f=1} f && /"id":/ {gsub(/[", ]/,""); split($0,a,":"); print a[2]; exit}')
if [[ -z "$EP_ID" ]]; then
  echo "Could not find a read_write endpoint in project."
  exit 5
fi

PGSSLMODE=require psql -h pg.neon.tech -U "$USER" -d "$DB" \
  --options=endpoint="$EP_ID" \
  -c "select current_user, current_database(), version();" && {
  echo "OK: passwordless with explicit endpoint worked"
  exit 0
}

echo "Both flows failed. Check psql version and endpoint configuration."
exit 6
```

## Makefile Targets for Database Operations

Add to your `Makefile`:

```makefile
# Neon Database Operations
# Requires: brew install postgresql (macOS) or apt-get install postgresql-client (Linux)

NEON_PROJECT_ID ?= rough-union-72390895
NEON_USER ?= neondb_owner
NEON_DB ?= neondb
NEON_ENDPOINT ?= ep-rough-dew-af6w48m3

# Connect to Neon interactively
.PHONY: psql-neon
psql-neon:
	@echo "Connecting to Neon (passwordless)..."
	@PGSSLMODE=require psql -h pg.neon.tech -U $(NEON_USER) -d $(NEON_DB) \
		--options=endpoint=$(NEON_ENDPOINT) || \
	PGSSLMODE=require psql -h pg.neon.tech -U $(NEON_USER) -d $(NEON_DB)

# Apply database migrations
.PHONY: migrate-neon
migrate-neon:
	@echo "Applying migrations to Neon..."
	@for sql in ops/sql/*.sql; do \
		echo "Applying $$sql..."; \
		PGSSLMODE=require psql -h pg.neon.tech -U $(NEON_USER) -d $(NEON_DB) \
			--options=endpoint=$(NEON_ENDPOINT) -f $$sql || exit 1; \
	done
	@echo "✅ All migrations applied"

# Check Neon connection
.PHONY: test-neon
test-neon:
	@echo "Testing Neon connection..."
	@PGSSLMODE=require psql -h pg.neon.tech -U $(NEON_USER) -d $(NEON_DB) \
		--options=endpoint=$(NEON_ENDPOINT) \
		-c "SELECT current_user, current_database(), version();" || \
	PGSSLMODE=require psql -h pg.neon.tech -U $(NEON_USER) -d $(NEON_DB) \
		-c "SELECT current_user, current_database(), version();"

# Create backup of Neon database
.PHONY: backup-neon
backup-neon:
	@echo "Creating backup of Neon database..."
	@mkdir -p backups
	@PGSSLMODE=require pg_dump -h pg.neon.tech -U $(NEON_USER) -d $(NEON_DB) \
		--options=endpoint=$(NEON_ENDPOINT) \
		> backups/neon_backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup created in backups/"
```

## Environment Variables

Add to `.env`:

```bash
# Neon Configuration
NEON_PROJECT_ID=rough-union-72390895
NEON_API_KEY=napi_r3gsuacduzw44nqdqav1u0hr2uv4bb2if48r8627jkxo7e4b2sxn92wsgf6zlxby
NEON_BRANCH_ID=br-green-firefly-afykrx78
NEON_ENDPOINT_ID=ep-rough-dew-af6w48m3
NEON_ROLE=neondb_owner
NEON_DB=neondb

# For passwordless connection (no password needed)
NEON_PASSWORDLESS_HOST=pg.neon.tech
```

## GitHub Actions CI/CD

Example workflow for database migrations:

```yaml
name: Database Migrations

on:
  push:
    paths:
      - 'ops/sql/*.sql'
  workflow_dispatch:

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install PostgreSQL client
        run: |
          sudo apt-get update
          sudo apt-get install -y postgresql-client
      
      - name: Run migrations
        env:
          NEON_PROJECT_ID: ${{ secrets.NEON_PROJECT_ID }}
          NEON_API_KEY: ${{ secrets.NEON_API_KEY }}
          NEON_ENDPOINT: ${{ secrets.NEON_ENDPOINT_ID }}
        run: |
          make migrate-neon
```

## Docker Support

For containerized migrations:

```dockerfile
FROM postgres:16-alpine
COPY ops/sql/*.sql /migrations/
COPY scripts/psql_passwordless.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/psql_passwordless.sh
ENTRYPOINT ["/usr/local/bin/psql_passwordless.sh"]
```

## Troubleshooting

### Connection Failures

1. **Check psql version**: 
   ```bash
   psql --version  # Should be 14+ for best SNI support
   ```

2. **Upgrade if needed**:
   ```bash
   brew upgrade postgresql  # macOS
   sudo apt-get upgrade postgresql-client  # Linux
   ```

3. **Verify endpoint**:
   ```bash
   python3 scripts/neon_rest.py endpoints
   ```

4. **Test with explicit endpoint**:
   ```bash
   PGSSLMODE=require psql -h pg.neon.tech -U neondb_owner -d neondb \
     --options=endpoint=ep-rough-dew-af6w48m3
   ```

### Sanity Checklist

- ✅ `psql` installed (`psql --version`)
- ✅ `PGSSLMODE=require` is set
- ✅ Try SNI (`-h pg.neon.tech`) first
- ✅ If fails, pass `--options=endpoint=ep_…`
- ✅ Still stuck? Upgrade libpq/psql and retry

## Best Practices

1. **Development**: Use passwordless connection for simplicity
2. **Production**: Implement JWT/JWKS for enhanced security
3. **CI/CD**: Use passwordless with endpoint option for reliability
4. **Migrations**: Always test in staging branch first
5. **Backups**: Regular automated backups before migrations

## Next Steps

1. **Install psql locally**:
   ```bash
   brew install postgresql  # or apt-get install postgresql-client
   ```

2. **Test connection**:
   ```bash
   make test-neon
   ```

3. **Apply audit schema**:
   ```bash
   make migrate-neon
   ```

4. **Set up JWKS for production**:
   ```bash
   python3 scripts/neon_rest.py jwks-add
   ```

## Summary

- **Local Development**: Install psql, use passwordless connection
- **Cloud Runtime**: Services use asyncpg with DSN, no psql needed
- **Migrations**: Use psql in CI/CD or containers
- **Production**: Implement JWT/JWKS for secure, scalable access