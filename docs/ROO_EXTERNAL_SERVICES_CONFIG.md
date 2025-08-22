# Roo External Services Configuration

This document configures Roo to interact with all your external services via APIs and MCP servers.

## 🔐 Service Credentials Setup

### 1. Infrastructure & Deployment

#### Lambda Labs
```bash
# Environment variables needed:
LAMBDA_LABS_API_KEY=<your-key>
LAMBDA_LABS_INSTANCE_ID=<instance-id>

# MCP Server: services/mcp-lambda/
```

#### Pulumi
```bash
# Environment variables:
PULUMI_ACCESS_TOKEN=<your-token>
PULUMI_ORG=<your-org>

# Config file: ~/.pulumi/credentials.json
```

#### GitHub
```bash
# Already configured:
GITHUB_PAT=<your-token>
GITHUB_APP_ID=<app-id>
GITHUB_PRIVATE_KEY=<private-key>

# MCP Server: services/mcp-github/ ✅
```

### 2. Databases & Vector Stores

#### Qdrant
```bash
# Environment variables:
QDRANT_URL=<cluster-url>
QDRANT_API_KEY=<api-key>
QDRANT_COLLECTION=<collection-name>

# MCP Server: services/mcp-qdrant/
```

#### Redis
```bash
# Environment variables:
REDIS_URL=redis://:<password>@<host>:<port>
REDIS_PASSWORD=<password>
REDIS_HOST=<host>
REDIS_PORT=<port>

# MCP Server: services/mcp-redis/
```

#### Neon
```bash
# Already configured:
NEON_DATABASE_URL=<postgresql-url>
NEON_API_KEY=<api-key>

# MCP Server: services/mcp-context/ ✅
```

### 3. AI & Memory Services

#### Mem0
```bash
# Environment variables:
MEM0_API_KEY=<api-key>
MEM0_ORG_ID=<org-id>
MEM0_USER_ID=<user-id>

# MCP Server: services/mcp-memory/
```

#### Portkey
```bash
# Environment variables:
PORTKEY_API_KEY=<api-key>
PORTKEY_WORKSPACE_ID=<workspace-id>

# MCP Server: Integrated in libs/llm-router/ ✅
```

#### OpenRouter
```bash
# Environment variables:
OPENROUTER_API_KEY=<api-key>
OPENROUTER_SITE_URL=<your-site>
OPENROUTER_SITE_NAME=<site-name>

# MCP Server: services/mcp-openrouter/
```

### 4. Business Tools

#### Slack
```bash
# Environment variables:
SLACK_BOT_TOKEN=xoxb-<token>
SLACK_APP_TOKEN=xapp-<token>
SLACK_SIGNING_SECRET=<secret>
SLACK_WORKSPACE_ID=<workspace>

# MCP Server: services/mcp-slack/
```

#### Gong.io
```bash
# Environment variables:
GONG_API_KEY=<api-key>
GONG_API_SECRET=<api-secret>
GONG_WORKSPACE_ID=<workspace>

# MCP Server: services/mcp-gong/
```

#### Salesforce
```bash
# Environment variables:
SALESFORCE_USERNAME=<username>
SALESFORCE_PASSWORD=<password>
SALESFORCE_SECURITY_TOKEN=<token>
SALESFORCE_CLIENT_ID=<client-id>
SALESFORCE_CLIENT_SECRET=<client-secret>
SALESFORCE_INSTANCE_URL=<instance-url>

# MCP Server: services/mcp-salesforce/
```

#### HubSpot
```bash
# Environment variables:
HUBSPOT_API_KEY=<api-key>
HUBSPOT_ACCESS_TOKEN=<access-token>
HUBSPOT_APP_ID=<app-id>
HUBSPOT_PORTAL_ID=<portal-id>

# MCP Server: services/mcp-hubspot/
```

#### Looker
```bash
# Environment variables:
LOOKER_CLIENT_ID=<client-id>
LOOKER_CLIENT_SECRET=<client-secret>
LOOKER_BASE_URL=<instance-url>
LOOKER_VERIFY_SSL=true

# MCP Server: services/mcp-looker/
```

#### UserGems
```bash
# Environment variables:
USERGEMS_API_KEY=<api-key>
USERGEMS_WORKSPACE_ID=<workspace>

# MCP Server: services/mcp-usergems/
```

---

## 🎯 MCP Server Templates

### Basic MCP Server Template
Create `services/mcp-<service>/app.py`:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import httpx

app = FastAPI(title="MCP <Service> Server")

# Configuration
API_KEY = os.getenv("<SERVICE>_API_KEY")
BASE_URL = os.getenv("<SERVICE>_BASE_URL", "https://api.<service>.com")

class Query(BaseModel):
    action: str
    params: dict

@app.get("/healthz")
async def health():
    return {"status": "healthy", "service": "mcp-<service>"}

@app.post("/execute")
async def execute(query: Query):
    """Execute actions on <Service>"""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/{query.action}",
            headers=headers,
            json=query.params
        )
    
    return response.json()
```

### Dockerfile Template
Create `services/mcp-<service>/Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PORT=8080
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Requirements Template
Create `services/mcp-<service>/requirements.txt`:

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
httpx==0.27.2
pydantic==2.8.2
python-dotenv==1.0.1
<service-specific-sdk>
```

---

## 🔧 Roo Configuration for External Services

### Update `.vscode/settings.json`:

```json
{
  "cider.externalServices": {
    "enabled": true,
    "services": [
      "lambda-labs",
      "pulumi",
      "github",
      "qdrant",
      "redis",
      "neon",
      "mem0",
      "portkey",
      "openrouter",
      "slack",
      "gong",
      "salesforce",
      "hubspot",
      "looker",
      "usergems"
    ],
    "autoApproveServiceActions": true,
    "requireApprovalForDestructive": true
  },
  "cider.mcpServers": {
    "autoDiscovery": true,
    "serverDirectory": "./services/mcp-*",
    "autoStart": false,
    "healthCheckInterval": 60000
  }
}
```

---

## 🚀 Quick Setup Script

Create `scripts/setup_external_services.sh`:

```bash
#!/bin/bash
# Setup all external service connections

# Check for required environment variables
REQUIRED_VARS=(
    "LAMBDA_LABS_API_KEY"
    "PULUMI_ACCESS_TOKEN"
    "GITHUB_PAT"
    "QDRANT_API_KEY"
    "REDIS_PASSWORD"
    "NEON_DATABASE_URL"
    "MEM0_API_KEY"
    "PORTKEY_API_KEY"
    "OPENROUTER_API_KEY"
    "SLACK_BOT_TOKEN"
    "GONG_API_KEY"
    "SALESFORCE_USERNAME"
    "HUBSPOT_API_KEY"
    "LOOKER_CLIENT_ID"
    "USERGEMS_API_KEY"
)

echo "Checking external service credentials..."
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "⚠️  Missing: $var"
    else
        echo "✅ Found: $var"
    fi
done

# Create MCP server directories
SERVICES=(
    "lambda" "pulumi" "qdrant" "redis" 
    "memory" "openrouter" "slack" "gong" 
    "salesforce" "hubspot" "looker" "usergems"
)

for service in "${SERVICES[@]}"; do
    mkdir -p "services/mcp-$service"
    echo "📁 Created services/mcp-$service"
done

echo "✅ External services setup complete"
```

---

## 🔒 Security Configuration

### Secret Storage
Use GitHub Secrets or a secure vault:

```bash
# Store in GitHub Secrets (for CI/CD)
gh secret set LAMBDA_LABS_API_KEY
gh secret set PULUMI_ACCESS_TOKEN
# ... etc

# Or use 1Password/Vault
op item create --category=apikey --title="Lambda Labs" --vault="Sophia AI"
```

### Access Control
Create `.env.services` (DO NOT COMMIT):

```bash
# Infrastructure
LAMBDA_LABS_API_KEY=your-key-here
PULUMI_ACCESS_TOKEN=your-token-here

# Databases
QDRANT_API_KEY=your-key-here
REDIS_PASSWORD=your-password-here
NEON_DATABASE_URL=your-url-here

# AI Services
MEM0_API_KEY=your-key-here
PORTKEY_API_KEY=your-key-here
OPENROUTER_API_KEY=your-key-here

# Business Tools
SLACK_BOT_TOKEN=your-token-here
GONG_API_KEY=your-key-here
SALESFORCE_USERNAME=your-username-here
HUBSPOT_API_KEY=your-key-here
LOOKER_CLIENT_ID=your-client-id-here
USERGEMS_API_KEY=your-key-here
```

---

## 📋 Service Capabilities Matrix

| Service | Read | Write | Delete | Deploy | Analytics |
|---------|------|-------|--------|--------|-----------|
| Lambda Labs | ✅ | ✅ | ✅ | ✅ | ✅ |
| Pulumi | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| GitHub | ✅ | ✅ | ⚠️ | ✅ | ✅ |
| Qdrant | ✅ | ✅ | ⚠️ | - | ✅ |
| Redis | ✅ | ✅ | ✅ | - | ✅ |
| Neon | ✅ | ✅ | ⚠️ | - | ✅ |
| Mem0 | ✅ | ✅ | ✅ | - | ✅ |
| Portkey | ✅ | ✅ | - | - | ✅ |
| OpenRouter | ✅ | - | - | - | ✅ |
| Slack | ✅ | ✅ | ⚠️ | - | ✅ |
| Gong | ✅ | ⚠️ | - | - | ✅ |
| Salesforce | ✅ | ✅ | ⚠️ | - | ✅ |
| HubSpot | ✅ | ✅ | ⚠️ | - | ✅ |
| Looker | ✅ | ⚠️ | - | - | ✅ |
| UserGems | ✅ | - | - | - | ✅ |

⚠️ = Requires additional confirmation

---

## 🎯 Next Steps

1. **Add credentials** to `.env.services` (local) or GitHub Secrets (CI/CD)
2. **Run setup script**: `./scripts/setup_external_services.sh`
3. **Create MCP servers** for each service you need
4. **Test connections**: Each MCP server has a `/healthz` endpoint
5. **Deploy MCP servers** to Fly.io for production use

With this configuration, Roo can now interact with all your external services programmatically!