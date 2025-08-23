# INFRASTRUCTURE ANALYSIS & DEPLOYMENT RECOMMENDATIONS

## LAMBDA LABS CONNECTION ASSESSMENT

**CONFIDENCE LEVEL: 0% - NO ACTIVE CONNECTION**

### Current Status
- Lambda Labs integration is **COMPLETELY PAUSED** across all services
- All Lambda Labs secrets are **MISSING** (❌ status in secrets matrix)
- No active MCP service for Lambda Labs exists
- Configuration exists but is not implemented

### Evidence
```
docs/INFRA_OPERATIONS.md: | **lambda** | ⏸️ paused | LAMBDA_LABS_API_KEY | ❌ |
docs/SECRETS.md: LAMBDA_LABS_API_KEY → null ❌ Missing
docs/SECRETS.md: LAMBDA_API_CLOUD_ENDPOINT → null ❌ Missing  
docs/SECRETS.md: LAMBDA_SSH_PRIVATE_KEY → null ❌ Missing
```

**CONCLUSION: No Fly.io → Lambda Labs connection exists. The deployment failures are unrelated to Lambda Labs.**

---

## ROOT CAUSE ANALYSIS OF DEPLOYMENT FAILURES

### 1. Application-Level Issues (60% of failures)
```
sophiaai-mcp-research-v2: ModuleNotFoundError: No module named 'asyncpg'
sophiaai-jobs-v2: Not listening on expected address 0.0.0.0:8080
sophiaai-dashboard-v2: Missing dist/ directory (npm workspace issue)
```

### 2. Platform Infrastructure Issues (40% of failures)
```
sophiaai-mcp-context-v2: 504 upstream request timeout (23+ retries)
sophiaai-mcp-business-v2: Machine launch timeout (20+ minutes)
```

---

## COMPREHENSIVE IMPROVEMENT RECOMMENDATIONS

### IMMEDIATE FIXES (Priority 1 - Next 2 hours)

#### 1. Fix Python Dependencies
```bash
# Add asyncpg to services/mcp-research/requirements.txt
echo "asyncpg==0.29.0" >> services/mcp-research/requirements.txt

# Verify all Python requirements files are complete
find services/ -name requirements.txt -exec echo "=== {} ===" \; -exec cat {} \;
```

#### 2. Fix Service Port Configurations  
```bash
# Check all Dockerfiles use correct port binding
grep -r "PORT\|8080\|EXPOSE" services/*/
# Ensure all services bind to 0.0.0.0:8080 not localhost:8080
```

#### 3. Fix Dashboard Build Issue
```bash
cd apps/dashboard
# Install workspace dependencies properly
npm install --workspaces
# Create dist directory if needed
npm run build
# Verify dist/ exists before Docker build
ls -la dist/
```

### PLATFORM RELIABILITY IMPROVEMENTS (Priority 2 - Next 24 hours)

#### 1. Implement Regional Redundancy
```yaml
# Update fly.toml files to specify multiple regions
[deploy]
  strategy = "rolling"
  
[[deploy.checks]]
  grace_period = "30s"
  interval = "15s"
  method = "GET"
  timeout = "10s"
  
# Deploy to multiple regions
regions = ["ord", "iad", "dfw"]  # Add redundancy
```

#### 2. Enhanced Health Check Configuration
```yaml
[http_service.checks]
  grace_period = "60s"      # Increased from default
  interval = "30s"          # More frequent checks
  timeout = "20s"           # Longer timeout
  method = "GET"
  path = "/health"
  
[http_service.checks.headers]
  "User-Agent" = "fly-health-check"
```

#### 3. Resource Optimization
```yaml
[vm]
  memory = "1gb"           # Ensure adequate memory
  cpus = 1

[mounts]
  source = "data"
  destination = "/data"
  initial_size = "10gb"    # Prevent disk space issues
```

### DEPLOYMENT STRATEGY IMPROVEMENTS (Priority 2 - Next 24 hours)

#### 1. Staged Deployment Pipeline
```bash
# Deploy in dependency order:
1. mcp-repo-v2        (foundational - already working)
2. jobs-v2           (background tasks - deployed but needs fixing)
3. mcp-context-v2    (data layer)
4. mcp-research-v2   (processing layer) 
5. mcp-business-v2   (business logic)
6. dashboard-v2      (frontend)
```

#### 2. Deployment Retry Logic
```bash
# Create deployment wrapper with retries
#!/bin/bash
deploy_with_retry() {
  local app_name=$1
  local max_retries=3
  
  for i in $(seq 1 $max_retries); do
    echo "Attempt $i for $app_name"
    if flyctl deploy --app $app_name --ha=false --wait-timeout=300; then
      echo "✅ $app_name deployed successfully"
      return 0
    else
      echo "❌ Attempt $i failed, waiting 60s..."
      sleep 60
    fi
  done
  echo "🚨 $app_name deployment failed after $max_retries attempts"
  return 1
}
```

#### 3. Pre-deployment Validation
```bash
# Validate before deployment
validate_service() {
  local service_path=$1
  echo "Validating $service_path..."
  
  # Check requirements files
  if [[ -f "$service_path/requirements.txt" ]]; then
    echo "✅ Requirements file found"
    # Validate no typos in requirements
    pip-compile --dry-run $service_path/requirements.txt
  fi
  
  # Check Dockerfile
  if [[ -f "$service_path/Dockerfile" ]]; then
    echo "✅ Dockerfile found"
    # Validate Dockerfile syntax
    docker build --dry-run $service_path/
  fi
  
  # Check fly.toml
  if [[ -f "$service_path/fly.toml" ]]; then
    echo "✅ fly.toml found"
    flyctl config validate -c $service_path/fly.toml
  fi
}
```

### MONITORING & ALERTING (Priority 3 - Next week)

#### 1. Deployment Health Dashboard
```bash
# Create monitoring script
#!/bin/bash
# deployment_monitor.sh
for app in sophiaai-dashboard-v2 sophiaai-mcp-repo-v2 sophiaai-mcp-research-v2 sophiaai-mcp-context-v2 sophiaai-mcp-business-v2 sophiaai-jobs-v2; do
  status=$(flyctl status --app $app --json | jq -r '.Status')
  echo "$app: $status"
  
  if [[ "$status" != "running" ]]; then
    # Send alert
    curl -X POST "$SLACK_WEBHOOK" -d "{\"text\":\"🚨 $app is $status\"}"
  fi
done
```

#### 2. Automated Recovery
```bash
# Auto-restart failed services
#!/bin/bash
# auto_recovery.sh
for app in $(flyctl apps list --json | jq -r '.[] | select(.Status != "running") | .Name'); do
  echo "🔄 Restarting $app"
  flyctl scale count 0 --app $app
  sleep 10
  flyctl scale count 1 --app $app
done
```

### LAMBDA LABS INTEGRATION (Future - when needed)

#### 1. MCP Server Setup
```bash
# Create services/mcp-lambda/
mkdir -p services/mcp-lambda
cd services/mcp-lambda

# Implement Lambda Labs MCP server
cat > app.py << 'EOF'
import os
import requests
from fastapi import FastAPI

app = FastAPI()

LAMBDA_API_KEY = os.getenv("LAMBDA_LABS_API_KEY")
LAMBDA_ENDPOINT = os.getenv("LAMBDA_API_CLOUD_ENDPOINT", "https://cloud.lambdalabs.com/api/v1")

@app.get("/instances")
async def list_instances():
    headers = {"Authorization": f"Bearer {LAMBDA_API_KEY}"}
    response = requests.get(f"{LAMBDA_ENDPOINT}/instances", headers=headers)
    return response.json()

@app.post("/instances/{instance_type}/launch")
async def launch_instance(instance_type: str):
    # Implementation for launching GPU instances
    pass
EOF
```

#### 2. Secrets Configuration
```bash
# Set Lambda Labs secrets when ready
flyctl secrets set LAMBDA_LABS_API_KEY="your-key" --app sophiaai-mcp-lambda-v2
flyctl secrets set LAMBDA_API_CLOUD_ENDPOINT="https://cloud.lambdalabs.com/api/v1" --app sophiaai-mcp-lambda-v2
flyctl secrets set LAMBDA_SSH_PRIVATE_KEY="your-private-key" --app sophiaai-mcp-lambda-v2
```

---

## PRIORITY ACTION PLAN

### Week 1 (Immediate)
1. ✅ Fix `asyncpg` dependency in mcp-research
2. ✅ Fix port binding in jobs service  
3. ✅ Fix npm workspace issues in dashboard
4. ✅ Implement deployment retry logic
5. ✅ Deploy services in dependency order

### Week 2 (Stability)
1. ✅ Add comprehensive health checks
2. ✅ Implement regional redundancy
3. ✅ Create monitoring dashboard
4. ✅ Setup automated recovery
5. ✅ Performance optimization

### Week 3+ (Enhancement)
1. ⏳ Lambda Labs integration (when required)
2. ⏳ Advanced monitoring and alerting
3. ⏳ Cost optimization
4. ⏳ Security hardening

---

## IMMEDIATE NEXT STEPS

```bash
# 1. Fix the critical dependency issue
echo "asyncpg==0.29.0" >> services/mcp-research/requirements.txt

# 2. Fix the jobs service port binding
sed -i 's/127.0.0.1:8080/0.0.0.0:8080/g' jobs/reindex.py

# 3. Rebuild and redeploy failed services
flyctl deploy --app sophiaai-mcp-research-v2 --ha=false
flyctl deploy --app sophiaai-jobs-v2 --ha=false

# 4. Fix dashboard npm workspace
cd apps/dashboard && npm install --workspaces && npm run build
flyctl deploy --app sophiaai-dashboard-v2 --ha=false
```

**RECOMMENDATION: Focus on fixing the basic application issues first, then Lambda Labs integration can be added later when/if needed.**
