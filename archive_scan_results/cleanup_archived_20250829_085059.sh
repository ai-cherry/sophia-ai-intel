#!/bin/bash
# Auto-generated cleanup script for archived files
# Review carefully before running!

echo 'This script will remove archived files. Continue? (y/n)'
read -r response
if [[ ! $response =~ ^[Yy]$ ]]; then
    echo 'Aborted'
    exit 1
fi

# Remove temp files
rm -f '.env.production.real.backup'
rm -f '.env.production'
rm -f '.env.production.deployment'
rm -f '.env.local'
rm -f '.htpasswd'
rm -f '.env.production.template'
rm -f '.dockerignore'
rm -f '.env'
rm -f '.env.production.real'
rm -f '.env.example'
rm -f '.env.production.secure'
rm -f '.env.development'
rm -f '.env.production.secure.bak'
rm -f 'context/.env.example'
rm -f 'k8s-deploy/scripts/.srl'
rm -f 'jobs/.dockerignore'
rm -f 'services/mcp-context/.dockerignore'
rm -f 'services/mcp-research/.dockerignore'
rm -f 'services/mcp-agents/.dockerignore'
rm -f 'services/mcp-business/.dockerignore'
rm -f 'services/mcp-lambda/.dockerignore'
rm -f 'services/mcp-github/.dockerignore'
rm -f 'services/mcp-hubspot/.dockerignore'
rm -f 'services/orchestrator/.dockerignore'

# Remove small archive files
rm -f '.env.production.real.backup'
rm -f 'DEPLOYMENT_REMEDIATION_SUMMARY_20250827_133501.md'
rm -f '.env.production.secure.bak'
rm -f 'SOPHIA_AI_FINAL_REPORT_20250826_071324.md'
rm -f 'DEPLOYMENT_READINESS_REPORT_20250827_133501.json'
rm -f 'agentic/research_swarms/trend_swarm.py.deprecated'
rm -f 'agentic/coding_swarms/main.py.deprecated'
rm -f 'scripts/run-sophia-locally.sh.backup'
rm -f 'scripts/synthetic_checks.py.backup'
