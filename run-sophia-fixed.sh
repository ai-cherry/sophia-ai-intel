#!/bin/bash
# Sophia AI - Fixed Local Deployment Script
export PATH=/Applications/Docker.app/Contents/Resources/bin:$PATH

echo "Starting Sophia AI Local Deployment..."

# Clean up
/Applications/Docker.app/Contents/Resources/bin/docker compose down --remove-orphans 2>/dev/null || true

# Start infrastructure
echo "Starting infrastructure..."
/Applications/Docker.app/Contents/Resources/bin/docker compose up -d redis postgres

# Wait
sleep 15

# Start monitoring  
echo "Starting monitoring..."
/Applications/Docker.app/Contents/Resources/bin/docker compose up -d prometheus grafana

# Show status
echo "Current status:"
/Applications/Docker.app/Contents/Resources/bin/docker ps

echo "Deployment script completed. Check container status above."

