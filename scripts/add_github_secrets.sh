#!/bin/bash
# Script to add secrets to GitHub Actions
# Run this locally with GitHub CLI installed

echo "🔐 Adding secrets to GitHub Actions repository"
echo "================================================"
echo ""
echo "This script will add the following secrets:"
echo "  - PORTKEY_API_KEY"
echo "  - NEON_API_TOKEN" 
echo "  - FLY_API_TOKEN"
echo ""
echo "Make sure you have GitHub CLI installed and authenticated."
echo ""

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed!"
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo "❌ GitHub CLI is not authenticated!"
    echo "Run: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI is authenticated"
echo ""

# Set repository
REPO="ai-cherry/sophia-ai-intel"
echo "📦 Repository: $REPO"
echo ""

# Add secrets
echo "Adding PORTKEY_API_KEY..."
echo "hPxFZGd8AN269n4bznDf2/Onbi8I" | gh secret set PORTKEY_API_KEY --repo $REPO

echo "Adding NEON_API_TOKEN..."
echo "napi_mr8himnznklsfgjpwb78w89q9eqfi0pb9ceg8y8y08a05v68vwrefcxg4gu82sg7" | gh secret set NEON_API_TOKEN --repo $REPO

echo "Adding FLY_API_TOKEN..."
echo "FlyV1 fm2_lJPECAAAAAAACcioxBAurYNBuSUwC7nABZDf+hGrwrVodHRwczovL2FwaS5mbHkuaW8vdjGUAJLOABLk6x8Lk7hodHRwczovL2FwaS5mbHkuaW8vYWFhL3YxxDzUx3UohX4CHVYz+VWxtztOAZAWrtPorVAhnlzR6xWG1Uc/33MvMqeA+l6G8PQeeVsqEOu7GWFz/uEtmxTEToWKixtZ2NIRqqILHZlfmpVIJPPH8gtUmf5Tz6H2K1F79q58HZJApSzj5pI/YuKbTSMnpck69ApaYvXZoSmGeSEnOatenjALEZS92rNoxMQgd4TfoZwwt/ARfkx7tJeYehEnCQyo0hnhd5xp84sxIu8=,fm2_lJPEToWKixtZ2NIRqqILHZlfmpVIJPPH8gtUmf5Tz6H2K1F79q58HZJApSzj5pI/YuKbTSMnpck69ApaYvXZoSmGeSEnOatenjALEZS92rNoxMQQDIjAtmGkDN0ZBBFJ54xFgsO5aHR0cHM6Ly9hcGkuZmx5LmlvL2FhYS92MZgEks5oqJEnzwAAAAEkoK9FF84AEh9YCpHOABIfWAzEEMQsx+atlEj8+R2/6O/P1wzEIHpQN/5K+vGRt9Yzd59VT7LaoWqfVHnkTTGBhlyBNNZ7" | gh secret set FLY_API_TOKEN --repo $REPO

echo ""
echo "✅ All secrets have been added!"
echo ""

# List secrets to confirm
echo "📋 Current secrets in repository:"
gh secret list --repo $REPO

echo ""
echo "🎉 SUCCESS! You can now run the Deploy All workflow."
echo ""
echo "Next steps:"
echo "1. Go to: https://github.com/$REPO/actions"
echo "2. Click on 'Deploy All (Dashboard + MCPs)' workflow"
echo "3. Click 'Run workflow' button"
echo "4. Monitor the deployment progress"