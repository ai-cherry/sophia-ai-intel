#!/bin/bash
set -e

echo "🚀 Fly.io Deployment Script"
echo "=========================="

# Configuration
APP_NAME=${FLY_APP_NAME:-sophia-mcp-platform}
REGION=${FLY_REGION:-iad}
CONFIG_PATH=${FLY_CONFIG:-ops/fly/fly.toml}
DEPLOY_STRATEGY=${1:-rolling}

# Check prerequisites
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl not found. Please install: https://fly.io/docs/getting-started/installing-flyctl/"
    exit 1
fi

# Function to check service health
check_health() {
    local service=$1
    echo "  Checking health of $service..."
    
    if flyctl status --app "$APP_NAME" | grep -q "running"; then
        echo "  ✅ $service is healthy"
        return 0
    else
        echo "  ❌ $service health check failed"
        return 1
    fi
}

# Pre-deployment checks
echo "🔍 Pre-deployment checks..."

# Check Fly.io auth
if ! flyctl auth whoami &> /dev/null; then
    echo "📝 Please log in to Fly.io..."
    flyctl auth login
fi

# Check if app exists
if ! flyctl apps list | grep -q "$APP_NAME"; then
    echo "❌ App $APP_NAME not found. Please run fly-sync-secrets.sh first."
    exit 1
fi

# Validate configuration
if [ ! -f "$CONFIG_PATH" ]; then
    echo "❌ Fly configuration not found at $CONFIG_PATH"
    exit 1
fi

echo "✅ Pre-deployment checks passed"
echo ""

# Build and push Docker images
echo "🐳 Building Docker images..."
docker-compose -f ops/docker-compose.yaml build

# Deploy based on strategy
case "$DEPLOY_STRATEGY" in
    "blue-green")
        echo "🔄 Blue-Green Deployment Strategy"
        
        # Scale up new version
        flyctl scale count 2 --app "$APP_NAME"
        
        # Deploy new version
        flyctl deploy --config "$CONFIG_PATH" --strategy bluegreen
        
        # Wait for health checks
        sleep 30
        
        # If healthy, complete deployment
        if check_health "new-version"; then
            echo "✅ Blue-green deployment successful"
        else
            echo "⚠️  Rolling back..."
            flyctl rollback --app "$APP_NAME"
            exit 1
        fi
        ;;
        
    "canary")
        echo "🐦 Canary Deployment Strategy"
        
        # Deploy with canary
        flyctl deploy --config "$CONFIG_PATH" --strategy canary
        
        # Monitor metrics for 5 minutes
        echo "📊 Monitoring canary for 5 minutes..."
        sleep 300
        
        # Promote if successful
        echo "📈 Promoting canary to production..."
        flyctl deploy --config "$CONFIG_PATH"
        ;;
        
    "rolling"|*)
        echo "🔄 Rolling Deployment Strategy (default)"
        
        # Standard rolling deployment
        flyctl deploy --config "$CONFIG_PATH" \
            --app "$APP_NAME" \
            --region "$REGION" \
            --verbose
        ;;
esac

# Post-deployment verification
echo ""
echo "🔍 Post-deployment verification..."

# Check app status
flyctl status --app "$APP_NAME"

# Check recent logs
echo ""
echo "📋 Recent logs:"
flyctl logs --app "$APP_NAME" -n 20

# Run smoke tests
echo ""
echo "🧪 Running smoke tests..."
./scripts/fly-smoke-tests.sh "$APP_NAME"

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📊 Access your services:"
echo "  Dashboard: https://$APP_NAME.fly.dev"
echo "  Metrics: https://$APP_NAME.fly.dev/metrics"
echo "  Health: https://$APP_NAME.fly.dev/health"