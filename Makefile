# Makefile for Sophia AI Infrastructure
# Fly.io deployment targets

# Variables
ENV_FILE ?= /Users/lynnmusil/sophia-ai-intel-1/.env

# Fly.io targets
fly-sync-dry:
	python scripts/fly_sync.py --env $(ENV) --dry-run

fly-sync:
	python scripts/fly_sync.py --env $(ENV)

fly-apps-create:
	./scripts/fly-create-apps.sh

fly-deploy-all:
	$(MAKE) fly-sync ENV=$(ENV_FILE)

# Help target
help:
	@echo "Available targets:"
	@echo "  fly-sync-dry     - Run fly sync in dry-run mode (requires ENV=path/to/.env)"
	@echo "  fly-sync         - Sync secrets to Fly.io apps (requires ENV=path/to/.env)"
	@echo "  fly-apps-create  - Create all Fly.io applications"
	@echo "  fly-deploy-all   - Deploy all services to Fly.io"
	@echo ""
	@echo "Example usage:"
	@echo "  make fly-sync-dry ENV=/path/to/.env"
	@echo "  make fly-sync ENV=/path/to/.env"
	@echo "  make fly-apps-create"
	@echo "  make fly-deploy-all"

.PHONY: fly-sync-dry fly-sync fly-apps-create fly-deploy-all help