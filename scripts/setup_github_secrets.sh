#!/bin/bash
# Setup GitHub Secrets for Sophia AI Intel
# This script helps configure secrets in GitHub without exposing values

set -euo pipefail

echo "================================================"
echo "   GitHub Secrets Configuration Helper"
echo "================================================"
echo ""
echo "This script will help you set up GitHub secrets"
echo "Required: GitHub CLI (gh) must be installed"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) not found"
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub"
    echo "Run: gh auth login"
    exit 1
fi

# Load credentials from vault
if [ -f ".env.vault" ]; then
    source scripts/load_credentials.sh
    echo ""
else
    echo "❌ .env.vault not found"
    exit 1
fi

echo "Setting GitHub Secrets for ai-cherry/sophia-ai-intel"
echo "======================================================"
echo ""

# Critical secrets for deployment
CRITICAL_SECRETS=(
    "FLY_API_TOKEN"
    "NEON_DATABASE_URL"
    "NEON_API_TOKEN"
    "GITHUB_PAT"
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
    "PORTKEY_API_KEY"
    "TAVILY_API_KEY"
    "SERPER_API_KEY"
    "LAMBDA_CLOUD_API_KEY"
    "PULUMI_ACCESS_TOKEN"
    "QDRANT_API_KEY"
    "QDRANT_URL"
    "REDIS_PASSWORD"
    "REDIS_ENDPOINT"
    "MEM0_API_KEY"
    "SLACK_APP_TOKEN"
    "SLACK_CLIENT_SECRET"
    "SALESFORCE_ACCESS_TOKEN"
    "HUBSPOT_API_TOKEN"
)

echo "Setting critical deployment secrets..."
echo "--------------------------------------"

for secret in "${CRITICAL_SECRETS[@]}"; do
    if [ -n "${!secret:-}" ]; then
        echo -n "Setting $secret... "
        if echo "${!secret}" | gh secret set "$secret" --repo ai-cherry/sophia-ai-intel 2>/dev/null; then
            echo "✅"
        else
            echo "⚠️ (may already exist or no permission)"
        fi
    else
        echo "⚠️ Skipping $secret (not found in vault)"
    fi
done

echo ""
echo "Setting additional service secrets..."
echo "-------------------------------------"

# Additional secrets
ADDITIONAL_SECRETS=(
    "DEEPSEEK_API_KEY"
    "GEMINI_API_KEY"
    "GROK_API_KEY"
    "GROQ_API_KEY"
    "MISTRAL_API_KEY"
    "PERPLEXITY_API_KEY"
    "OPENROUTER_API_KEY"
    "LANGCHAIN_API_KEY"
    "PHIDATA_API_KEY"
    "EXA_API_KEY"
    "BRAVE_API_KEY"
    "GONG_ACCESS_KEY"
    "LINEAR_API_KEY"
    "NOTION_API_KEY"
    "ASANA_PAT_TOKEN"
    "SENTRY_API_TOKEN"
    "ARIZE_API_KEY"
    "N8N_API_KEY"
    "AIRBYTE_CLIENT_ID"
    "DOCKER_PAT"
    "FIGMA_PAT"
    "CONTINUE_API_KEY"
    "HUGGINGFACE_API_TOKEN"
)

for secret in "${ADDITIONAL_SECRETS[@]}"; do
    if [ -n "${!secret:-}" ]; then
        echo -n "Setting $secret... "
        if echo "${!secret}" | gh secret set "$secret" --repo ai-cherry/sophia-ai-intel 2>/dev/null; then
            echo "✅"
        else
            echo "⚠️"
        fi
    fi
done

echo ""
echo "================================================"
echo "✅ GitHub Secrets configuration complete!"
echo ""
echo "Verify secrets at:"
echo "https://github.com/ai-cherry/sophia-ai-intel/settings/secrets/actions"
echo ""
echo "You can now run the deploy workflow!"
echo "================================================"