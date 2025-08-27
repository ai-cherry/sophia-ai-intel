#!/bin/bash
set -e

echo "🔄 Running DBT transformations..."

# Load environment variables
source /app/.env

# Test connection
dbt debug

# Run models
echo "📊 Running staging models..."
dbt run --models staging

echo "📈 Running mart models..."
dbt run --models marts

# Run tests
echo "✅ Running tests..."
dbt test

# Generate documentation
echo "📚 Generating documentation..."
dbt docs generate

echo "✨ DBT run completed successfully!"