#!/bin/bash

# Sophia AI Intel - Environment Variable Validation Script
# This script validates that all required environment variables are set
# before starting the application services.

set -e

echo "🔐 Validating environment variables for Sophia AI Intel..."

# Required environment variables for core functionality
REQUIRED_VARS=(
    "NEON_DATABASE_URL"
    "REDIS_URL"
    "QDRANT_URL"
    "QDRANT_API_KEY"
    "PORTKEY_API_KEY"
    "OPENAI_API_KEY"
)

# Optional but recommended environment variables
OPTIONAL_VARS=(
    "ANTHROPIC_API_KEY"
    "TAVILY_API_KEY"
    "PERPLEXITY_API_KEY"
    "GITHUB_APP_ID"
    "GITHUB_INSTALLATION_ID"
    "GITHUB_PRIVATE_KEY"
)

# Track missing variables
MISSING_REQUIRED=()
MISSING_OPTIONAL=()

# Check required variables
for var in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        MISSING_REQUIRED+=("$var")
    fi
done

# Check optional variables
for var in "${OPTIONAL_VARS[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        MISSING_OPTIONAL+=("$var")
    fi
done

# Report results
if [[ ${#MISSING_REQUIRED[@]} -gt 0 ]]; then
    echo "❌ ERROR: Missing required environment variables:"
    for var in "${MISSING_REQUIRED[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please set these variables in your environment or .env file."
    echo "You can copy .env.example to .env and populate the values."
    exit 1
fi

if [[ ${#MISSING_OPTIONAL[@]} -gt 0 ]]; then
    echo "⚠️  WARNING: Missing optional environment variables:"
    for var in "${MISSING_OPTIONAL[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Some features may not work without these variables."
    echo "You can add them to your environment or .env file if needed."
    echo ""
fi

# Validate specific formats
echo "🔍 Validating environment variable formats..."

# Validate database URL format
if [[ ! "$NEON_DATABASE_URL" =~ ^postgresql:// ]]; then
    echo "❌ ERROR: NEON_DATABASE_URL must start with 'postgresql://'"
    exit 1
fi

# Validate Redis URL format
if [[ ! "$REDIS_URL" =~ ^redis:// ]]; then
    echo "❌ ERROR: REDIS_URL must start with 'redis://'"
    exit 1
fi

# Validate Qdrant URL format
if [[ ! "$QDRANT_URL" =~ ^https?:// ]]; then
    echo "❌ ERROR: QDRANT_URL must start with 'http://' or 'https://'"
    exit 1
fi

# Validate API keys are not placeholder values
if [[ "$PORTKEY_API_KEY" == "your_portkey_api_key_here" ]]; then
    echo "❌ ERROR: PORTKEY_API_KEY contains placeholder value"
    exit 1
fi

if [[ "$OPENAI_API_KEY" == "your_openai_api_key_here" ]]; then
    echo "❌ ERROR: OPENAI_API_KEY contains placeholder value"
    exit 1
fi

echo "✅ Environment variable validation completed successfully!"
echo ""
echo "📋 Summary:"
echo "   - Required variables: ${#REQUIRED_VARS[@]} present"
echo "   - Optional variables: $(( ${#OPTIONAL_VARS[@]} - ${#MISSING_OPTIONAL[@]} )) of ${#OPTIONAL_VARS[@]} present"
echo ""
echo "🚀 Services can now be started safely."