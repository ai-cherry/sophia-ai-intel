# Codespaces Secret Synchronization Guide

## Issue Identified
Critical deployment secrets missing from Codespaces environment:
- ❌ `RENDER_API_TOKEN` - Required for Render deployment
- ❌ `NEON_DATABASE_URL` - Required for database connectivity
- ✅ `REDIS_ACCOUNT_KEY` - Available
- ✅ `QDRANT_API_KEY` - Available  
- ✅ `MEM0_API_KEY` - Available
- ✅ `ANTHROPIC_API_KEY` - Available

## Quick Fix Options

### Option 1: Restart Codespace (Recommended)
1. **Stop current Codespace:**
   - Click the Codespace name in bottom left
   - Select "Stop Current Codespace" 
   - Wait for full shutdown

2. **Restart Codespace:**
   - Go to https://github.com/codespaces
   - Find your `sophia-ai-intel` Codespace
   - Click "Start" to restart
   - This will pull latest organization secrets

### Option 2: Rebuild Codespace (If restart doesn't work)
1. **Rebuild Container:**
   - Open Command Palette (Ctrl+Shift+P)
   - Run "Codespaces: Rebuild Container"
   - Select "Rebuild"
   - Wait for complete rebuild

### Option 3: Manual Secret Export (Temporary)
If you need immediate access, you can manually set the secrets:

```bash
# Set the missing secrets temporarily
export RENDER_API_TOKEN="your-render-api-token-here"
export NEON_DATABASE_URL="your-neon-database-url-here"

# Verify they're set
echo "RENDER_API_TOKEN: $([ -n "$RENDER_API_TOKEN" ] && echo "✅ Set" || echo "❌ Missing")"
echo "NEON_DATABASE_URL: $([ -n "$NEON_DATABASE_URL" ] && echo "✅ Set" || echo "❌ Missing")"
```

## Verification Commands

After restart/rebuild, run these to verify all secrets are available:

```bash
# Check all migration secrets
echo "=== Migration Secret Status ==="
echo "RENDER_API_TOKEN: $([ -n "$RENDER_API_TOKEN" ] && echo "✅ Set" || echo "❌ Missing")"
echo "NEON_DATABASE_URL: $([ -n "$NEON_DATABASE_URL" ] && echo "✅ Set" || echo "❌ Missing")"
echo "REDIS_ACCOUNT_KEY: $([ -n "$REDIS_ACCOUNT_KEY" ] && echo "✅ Set" || echo "❌ Missing")"
echo "REDIS_DATABASE_ENDPOINT: $([ -n "$REDIS_DATABASE_ENDPOINT" ] && echo "✅ Set" || echo "❌ Missing")"
echo "QDRANT_API_KEY: $([ -n "$QDRANT_API_KEY" ] && echo "✅ Set" || echo "❌ Missing")"
echo "MEM0_API_KEY: $([ -n "$MEM0_API_KEY" ] && echo "✅ Set" || echo "❌ Missing")"
echo "LAMBDA_API_KEY: $([ -n "$LAMBDA_API_KEY" ] && echo "✅ Set" || echo "❌ Missing")"
echo "ANTHROPIC_API_KEY: $([ -n "$ANTHROPIC_API_KEY" ] && echo "✅ Set" || echo "❌ Missing")"
echo "OPENAI_API_KEY: $([ -n "$OPENAI_API_KEY" ] && echo "✅ Set" || echo "❌ Missing")"
echo "HUBSPOT_API_TOKEN: $([ -n "$HUBSPOT_API_TOKEN" ] && echo "✅ Set" || echo "❌ Missing")"
```

## Ready to Deploy

Once all secrets show ✅ Set, you can immediately execute the migration:

```bash
# Trigger the deployment workflow
gh workflow run "Deploy Sophia to Render"

# Or use the file trigger
echo "Deployment triggered: $(date)" >> DEPLOY_NOW
git add DEPLOY_NOW
git commit -m "🚀 Trigger Render deployment"
git push
```

## Migration System Status

✅ **Complete migration system ready:**
- Full automated pipeline built
- All deployment scripts created  
- External services integration configured
- Validation and monitoring systems ready
- Clean git history (no embedded secrets)

The only blocker is secret synchronization - once resolved, deployment can execute immediately.
