# Sophia AI Intel - Comprehensive Codebase Audit Plan

## Overview
This document outlines the complete audit plan for the sophia-ai-intel repository, ensuring real end-to-end testing with proof artifacts and no mocks.

## Script Architecture

### Main Script: `scripts/real_assess.sh`
A comprehensive bash script that performs all audit tasks with the following characteristics:
- **Idempotent**: Can be run multiple times without issues
- **Proof-first**: Every operation creates artifacts in `proofs/assessment/`
- **Error-resilient**: Captures failures as normalized JSON and continues
- **No mocks**: Real commands, real builds, real tests

### Script Components

#### 1. Setup & Environment (Lines 1-50)
```bash
#!/bin/bash
set -euo pipefail  # Strict error handling

# Create directories
mkdir -p proofs/assessment/mcp_health

# Environment detection
node --version > proofs/assessment/env.txt
python3 --version >> proofs/assessment/env.txt
docker --version >> proofs/assessment/env.txt 2>&1 || echo "Docker not available" >> proofs/assessment/env.txt

# Normalized error helper function
write_error_json() {
    local query="$1"
    local provider="$2"
    local code="$3"
    local message="$4"
    local output_file="$5"
    
    cat > "$output_file" <<EOF
{
  "status": "failure",
  "query": "$query",
  "results": [],
  "summary": {"text": "$message", "confidence": 1.0, "model": "n/a", "sources": []},
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "execution_time_ms": 0,
  "errors": [{"provider": "$provider", "code": "$code", "message": "$message"}]
}
EOF
}
```

#### 2. Repository Inventory (Lines 51-150)
- Tree structure (3 levels): `tree -L 3 -a` or fallback to `find`
- Package.json discovery and parsing
- Python requirements.txt and pyproject.toml scanning
- Workflow files listing
- Dockerfile discovery
- fly.toml analysis with app name extraction

#### 3. Foot-gun Scans (Lines 151-200)
- Railway references scan (railway.app, RW_, RAILWAY_)
- Vite base configuration check
- Nginx /__build and /healthz endpoint verification

#### 4. Dashboard Build Process (Lines 201-300)
- Navigate to apps/dashboard
- Run `npm ci` with fallback to `--legacy-peer-deps`
- Execute `npm run build`
- Capture all stdout/stderr to proofs/assessment/npm_dashboard_build.txt

#### 5. Lint & Type Checking (Lines 301-350)
- Check for lint script in package.json
- Run eslint if available
- Run TypeScript compiler for type checking
- Capture all output regardless of exit codes

#### 6. Python Services Setup (Lines 351-450)
For each service in services/*:
- Check for requirements.txt
- Create virtual environment
- Install dependencies
- Log output or write normalized error JSON

#### 7. Local MCP Health Checks (Lines 451-550)
- Start MCP services with uvicorn on different ports
- Wait for startup
- Execute curl health checks
- Kill processes cleanly
- Capture all responses

#### 8. Docker Build Tests (Lines 551-650)
- Iterate through discovered Dockerfiles
- Build each image with audit-<name> tag
- Capture build output
- Write normalized errors for failures

#### 9. Environment Variables Scan (Lines 651-700)
- Grep for process.env.* patterns
- Grep for os.getenv() patterns
- Aggregate unique environment variable names
- Output as JSON

#### 10. Report Generation (Lines 701-800)
Generate comprehensive docs/CODEBASE_AUDIT.md with:
- Repository overview
- Build results summary
- Test results
- Docker build status
- MCP health check results
- Deployment readiness assessment
- Foot-gun findings
- Environment requirements matrix
- High-impact fixes recommendations
- Next actions

## Proof Artifacts Structure

```
proofs/assessment/
├── tree.txt                    # Repository structure
├── packages.json               # Node/Python packages inventory
├── workflows.json              # GitHub workflows list
├── dockerfiles.json            # Dockerfile locations
├── fly_tomls.json             # Fly.io configurations
├── railway_scan.txt           # Railway references scan
├── vite_base.txt              # Vite base configuration
├── env_required.json          # Environment variables list
├── npm_dashboard_build.txt    # Dashboard build output
├── eslint.txt                 # Linting results
├── tsc.txt                    # TypeScript check results
├── docker_builds.txt          # Docker build logs
├── pip_*.txt                  # Python dependency installation logs
└── mcp_health/
    ├── mcp_github_local.txt   # MCP GitHub health check
    ├── mcp_context_local.txt  # MCP Context health check
    └── mcp_research_local.txt # MCP Research health check
```

## Execution Flow

1. **Initial Setup**
   - Verify Node 20 and Python 3.11
   - Create assessment directories
   - Initialize logging

2. **Inventory Phase**
   - Map repository structure
   - Identify all build targets
   - Locate configuration files

3. **Static Analysis**
   - Scan for known issues
   - Check configurations
   - Identify missing components

4. **Build Phase**
   - Install dependencies
   - Build dashboard
   - Compile TypeScript

5. **Test Phase**
   - Run linters
   - Execute type checks
   - Start local services

6. **Docker Phase**
   - Build all images
   - Verify Dockerfile syntax
   - Check build contexts

7. **Health Check Phase**
   - Start MCP services locally
   - Execute health endpoints
   - Verify responses

8. **Report Generation**
   - Aggregate all findings
   - Generate markdown report
   - Create actionable recommendations

## Error Handling Strategy

All errors follow this normalized JSON structure:
```json
{
  "status": "failure",
  "query": "<operation_name>",
  "results": [],
  "summary": {
    "text": "<error_description>",
    "confidence": 1.0,
    "model": "n/a",
    "sources": []
  },
  "timestamp": "<ISO_8601_UTC>",
  "execution_time_ms": 0,
  "errors": [{
    "provider": "<system_component>",
    "code": "<error_code>",
    "message": "<detailed_message>"
  }]
}
```

## Dependencies

- **Node.js 20**: Required for dashboard and workspace builds
- **Python 3.11**: Required for MCP services
- **Docker**: Required for container builds (optional but recommended)
- **Basic Unix tools**: tree, grep, curl, jq

## Helper Scripts

### MCP Runner Helper
A small Python script to assist with starting MCP services for health checks:
```python
#!/usr/bin/env python3
# scripts/mcp_runner.py
import subprocess
import time
import sys
import signal

def run_mcp(service_path, port):
    proc = subprocess.Popen(
        ["uvicorn", "app:app", "--port", str(port)],
        cwd=service_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)  # Wait for startup
    return proc

if __name__ == "__main__":
    service = sys.argv[1]
    port = int(sys.argv[2])
    proc = run_mcp(service, port)
    print(proc.pid)
```

## Next Steps

1. Switch to code mode to implement scripts/real_assess.sh
2. Create the MCP runner helper script
3. Execute the audit script
4. Review generated proofs
5. Generate final CODEBASE_AUDIT.md report