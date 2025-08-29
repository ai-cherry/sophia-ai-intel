# Cline MCP Connection Setup Instructions

## Quick Setup (Non-Intrusive)

This setup allows Cline to connect to your existing MCP services **without modifying any of your existing Sophia AI services**. Your current services remain completely unchanged.

## Prerequisites

1. **Your existing services are running** (confirmed ✅):
   - All 9 MCP services are up and running on ports 8081-8092
   - They've been running for 11+ hours
   - Health checks show they're operational

2. **Install MCP Python library** (one-time setup):
```bash
pip install mcp httpx
```

## Setup Steps

### Step 1: Make the adapter executable
```bash
chmod +x mcp-universal-adapter.py
```

### Step 2: Test the adapter standalone (optional)
```bash
# Test that the adapter can start
python3 mcp-universal-adapter.py
# Press Ctrl+C to stop after seeing "MCP server ready for connections"
```

### Step 3: Configure Cline

#### Option A: Using the provided config file
1. Open Cline settings in VSCode
2. Go to MCP Servers section
3. Click "Edit Config File"
4. Copy the content from `cline-mcp-config.json` into your Cline MCP configuration

#### Option B: Manual configuration
1. Open Cline settings
2. Add a new MCP server with these details:
   - **Name**: sophia-universal
   - **Command**: python3
   - **Arguments**: /Users/lynnmusil/sophia-ai-intel-1/mcp-universal-adapter.py

### Step 4: Restart Cline
After adding the configuration, restart Cline (or reload VSCode) to establish the connection.

## Verifying the Connection

Once connected, you'll be able to use these tools in Cline:

### Available Tools
- `search_context` - Semantic search in your document store
- `store_document` - Store documents with embeddings
- `web_search` - Perform web searches
- `search_code` - Search GitHub repositories
- `get_crm_contacts` - Access HubSpot/Salesforce contacts
- `execute_workflow` - Run orchestrator workflows
- `create_agent_task` - Create coordinator tasks
- `check_service_health` - Monitor service status

### Available Resources
Access service information via:
- `sophia://context`
- `sophia://research`
- `sophia://github`
- `sophia://hubspot`
- `sophia://salesforce`
- `sophia://gong`
- `sophia://agents`
- `sophia://coordinator`
- `sophia://orchestrator`

## How It Works (Non-Intrusive Architecture)

```
Your Current Setup (UNCHANGED):
[Sophia App] <--HTTP--> [Services:8081-8092] <---> [Databases]

Added for Cline (NEW):
[Cline] <--MCP Protocol--> [Adapter] <--HTTP--> [Services:8081-8092]
```

The adapter acts as a translator:
1. Cline sends MCP protocol requests to the adapter
2. Adapter translates them to HTTP requests for your services
3. Your services respond normally (they don't know about MCP)
4. Adapter translates responses back to MCP format for Cline

## Benefits of This Approach

✅ **Zero Changes to Existing Services**
- Your services continue running exactly as they are
- No code modifications required
- No risk to Sophia integration

✅ **Complete Isolation**
- Adapter runs as a separate process
- Can be stopped/started without affecting services
- Easy to remove if not needed

✅ **Full Functionality**
- Cline gets access to all your services
- All tools and resources available
- Seamless integration experience

## Troubleshooting

### If Cline doesn't see the server:
1. Check that all services are running: `docker ps | grep mcp`
2. Verify the adapter path is correct in the config
3. Check Python and MCP library are installed: `python3 -c "import mcp"`

### If tools aren't working:
1. Check service health: `curl http://localhost:8081/health`
2. Review adapter logs in Cline's output panel
3. Ensure Docker network is functioning

### To test without Cline:
```bash
# Check if services are accessible
for port in 8081 8085 8082 8083 8092 8091 8000 8080 8088; do
  echo "Port $port: $(curl -s http://localhost:$port/health | head -c 50)"
done
```

## Advanced Options

### Running adapter in Docker (optional):
```bash
docker run -d --name mcp-adapter \
  --network sophia-network \
  -v $(pwd):/app \
  python:3.11-slim sh -c "pip install mcp httpx && python /app/mcp-universal-adapter.py"
```

### Customizing service endpoints:
Edit the `SERVICES` dictionary in `mcp-universal-adapter.py` if your services run on different ports or hosts.

## Summary

This setup provides a **completely non-intrusive** way to connect Cline to your MCP services:
- Your Sophia integration remains untouched
- No modifications to existing services
- Easy to set up and remove
- Full access to all service capabilities

The adapter pattern ensures complete compatibility without any compromise to your existing architecture.
