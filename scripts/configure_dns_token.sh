#!/bin/bash
# Sophia AI DNS Token Configuration Script
# Configures DNSIMPLE_TOKEN in GitHub Actions secrets for DNS management

set -e

echo "🔐 Configuring DNS Token for Sophia AI Infrastructure"
echo "=================================================="

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI not found. Please install it first:"
    echo "   https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated with GitHub CLI
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI. Please run:"
    echo "   gh auth login"
    exit 1
fi

echo "✅ GitHub CLI is installed and authenticated"

# Repository information
REPO="ai-cherry/sophia-ai-intel"
echo "📁 Repository: $REPO"

# Check current secrets
echo "🔍 Checking current GitHub secrets..."
CURRENT_SECRETS=$(gh secret list --repo $REPO --json name)
DNS_TOKEN_EXISTS=$(echo $CURRENT_SECRETS | jq -r '.[] | select(.name=="DNSIMPLE_TOKEN") | .name' 2>/dev/null || echo "")

if [[ "$DNS_TOKEN_EXISTS" == "DNSIMPLE_TOKEN" ]]; then
    echo "⚠️  DNSIMPLE_TOKEN already exists in GitHub secrets"
    echo "   Use 'gh secret set DNSIMPLE_TOKEN --repo $REPO' to update"
else
    echo "❌ DNSIMPLE_TOKEN not found in GitHub secrets"
fi

echo ""
echo "🎯 DNS Token Configuration Steps:"
echo "================================="
echo ""
echo "1️⃣ Get your DNSimple API token:"
echo "   - Go to https://dnsimple.com/user/api_access"
echo "   - Generate a new API token if you don't have one"
echo "   - Copy the token (format: dnsimple_u_...)"
echo ""
echo "2️⃣ Set the token in GitHub secrets:"
echo "   - Run: gh secret set DNSIMPLE_TOKEN --repo $REPO"
echo "   - Or use the web UI: https://github.com/$REPO/settings/secrets/actions"
echo ""
echo "3️⃣ Verify the configuration:"
echo "   - Run: python scripts/dns_management.py cleanup"
echo "   - This will test the token and clean up DNS conflicts"
echo ""
echo "4️⃣ Set up agent swarm DNS:"
echo "   - Run: python scripts/dns_management.py setup"
echo "   - This will create DNS records for agent services"
echo ""

# Interactive configuration option
echo "🤖 Would you like to configure the token now? (y/N)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "📝 Enter your DNSimple token (it will be hidden):"
    read -rs DNSIMPLE_TOKEN
    
    if [[ -z "$DNSIMPLE_TOKEN" ]]; then
        echo "❌ No token provided. Exiting..."
        exit 1
    fi
    
    echo ""
    echo "🔐 Setting DNSIMPLE_TOKEN in GitHub secrets..."
    
    if echo "$DNSIMPLE_TOKEN" | gh secret set DNSIMPLE_TOKEN --repo $REPO; then
        echo "✅ DNSIMPLE_TOKEN successfully configured in GitHub secrets"
        
        echo ""
        echo "🧪 Testing DNS management..."
        
        # Set token for local testing
        export DNSIMPLE_TOKEN="$DNSIMPLE_TOKEN"
        
        # Test the DNS management
        if python scripts/dns_management.py health; then
            echo "✅ DNS management working correctly"
            
            echo ""
            echo "🚀 Ready to run DNS operations:"
            echo "   - DNS cleanup: python scripts/dns_management.py cleanup"
            echo "   - Agent setup: python scripts/dns_management.py setup"
            echo "   - Full setup: python scripts/dns_management.py full"
            
        else
            echo "⚠️  DNS management test had issues. Check the token and try again."
        fi
        
    else
        echo "❌ Failed to set DNSIMPLE_TOKEN in GitHub secrets"
        exit 1
    fi
else
    echo ""
    echo "⏭️  Configuration skipped. You can run this script again later."
    echo ""
    echo "💡 Manual configuration:"
    echo "   gh secret set DNSIMPLE_TOKEN --repo $REPO"
    echo ""
fi

echo ""
echo "📋 Next Steps After DNS Token Configuration:"
echo "==========================================="
echo "1. Run DNS cleanup: python scripts/dns_management.py cleanup"
echo "2. Set up agent DNS: python scripts/dns_management.py setup"  
echo "3. Deploy agent swarm: flyctl deploy -a sophiaai-mcp-agents"
echo "4. Validate infrastructure: python scripts/dns_management.py health"
echo ""
echo "🎯 Complete infrastructure setup: python scripts/dns_management.py full"
echo ""
