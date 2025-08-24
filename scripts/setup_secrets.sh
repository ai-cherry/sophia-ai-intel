#!/bin/bash
# Setup Required Secrets for Sophia AI Intel Migration

set -e

echo "🔐 Sophia AI Intel - Setup Required Secrets"
echo "=========================================="
echo "Setting up secrets for Render migration..."
echo ""

REPO="ai-cherry/sophia-ai-intel"

echo "📝 Required Secret Setup Commands:"
echo "=================================="
echo ""

echo "1. RENDER PLATFORM SETUP:"
echo "   • Visit: https://render.com"
echo "   • Create account and generate API token"
echo "   • Run: gh secret set RENDER_API_TOKEN --repo $REPO"
echo ""

echo "2. PULUMI INFRASTRUCTURE:"
echo "   • Visit: https://app.pulumi.com"
echo "   • Create account and generate access token"
echo "   • Run: gh secret set PULUMI_ACCESS_TOKEN --repo $REPO"
echo ""

echo "3. QDRANT VECTOR DATABASE:"
echo "   • Visit: https://cloud.qdrant.io"
echo "   • Create account (free tier available)"
echo "   • Generate API key"
echo "   • Run: gh secret set QDRANT_API_KEY --repo $REPO"
echo ""

echo "4. MEM0 MEMORY MANAGEMENT:"
echo "   • Visit: https://mem0.ai"
echo "   • Create account and generate API key"
echo "   • Run: gh secret set MEM0_API_KEY --repo $REPO"
echo ""

echo "5. EXISTING SECRETS (if not already configured):"
echo "   • gh secret set NEON_DATABASE_URL --repo $REPO"
echo "   • gh secret set REDIS_API_KEY --repo $REPO"
echo "   • gh secret set REDIS_DATABASE_ENDPOINT --repo $REPO"
echo "   • gh secret set OPENAI_API_KEY --repo $REPO"
echo "   • gh secret set GITHUB_APP_ID --repo $REPO"
echo ""

echo "🚀 ALTERNATIVE: Direct Workflow Execution"
echo "========================================"
echo "If you have organization-level secrets already configured,"
echo "you can execute the migration directly:"
echo ""
echo "gh workflow run deploy_render.yml \\"
echo "  --repo $REPO \\"
echo "  --field deploy_phase=complete_migration"
echo ""

echo "📊 Monitor Progress:"
echo "=================="
echo "• View workflow: https://github.com/$REPO/actions"
echo "• Check status: gh run list --repo $REPO --workflow=deploy_render.yml --limit=1"
echo "• View logs: gh run view --repo $REPO --web"
echo ""

echo "✅ Setup guide complete!"
echo "Add the required secrets above, then run the migration."
