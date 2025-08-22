#!/bin/bash

set -e

echo "🔍 Fly.io Token Authentication Test"
echo "===================================="
echo ""

# Check if FLY_API_TOKEN is set
if [ -z "$FLY_API_TOKEN" ]; then
    echo "❌ FLY_API_TOKEN environment variable is not set!"
    echo ""
    echo "To test your token, run:"
    echo "  export FLY_API_TOKEN='your-token-here'"
    echo "  ./scripts/test_fly_token.sh"
    echo ""
    echo "Get your token from: https://fly.io/user/personal_access_tokens"
    exit 1
fi

# Check token format
if [[ ! "$FLY_API_TOKEN" =~ ^fo1_ ]]; then
    echo "⚠️  WARNING: Token does not start with 'fo1_'"
    echo "   Current prefix: ${FLY_API_TOKEN:0:4}..."
    echo "   Expected format: fo1_xxxxxxxxxxxxx"
    echo ""
fi

# Test with flyctl
echo "📋 Testing token with flyctl..."
echo ""

if ! command -v flyctl &> /dev/null; then
    echo "Installing flyctl..."
    curl -L https://fly.io/install.sh | sh
    export PATH="$HOME/.fly/bin:$PATH"
fi

echo "Flyctl version:"
flyctl version

echo ""
echo "Testing authentication..."
if flyctl auth whoami; then
    echo ""
    echo "✅ Token is VALID! Authentication successful."
    echo ""
    echo "📋 Next steps:"
    echo "1. Copy this EXACT token to GitHub Secrets"
    echo "2. Go to: https://github.com/ai-cherry/sophia-ai-intel/settings/secrets/actions"
    echo "3. Click on FLY_API_TOKEN → Update secret"
    echo "4. Paste the token with NO extra spaces or newlines"
    echo "5. Save and trigger deployment again"
else
    echo ""
    echo "❌ Token is INVALID! Authentication failed."
    echo ""
    echo "📋 Fix steps:"
    echo "1. Generate a new token: https://fly.io/user/personal_access_tokens"
    echo "2. Click 'Create token' → Name it 'github-actions'"
    echo "3. Copy the ENTIRE token (starts with 'fo1_')"
    echo "4. Test it again with this script"
    echo "5. Once valid, update GitHub Secrets"
fi

echo ""
echo "📊 Token diagnostics:"
echo "  Length: ${#FLY_API_TOKEN} characters"
echo "  Prefix: ${FLY_API_TOKEN:0:4}..."
echo "  Suffix: ...${FLY_API_TOKEN: -4}"