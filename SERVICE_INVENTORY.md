# Sophia AI Microservice Inventory - Phase 1

## Overview
This document catalogs all 23+ microservices identified in the Sophia AI platform, including their dependencies, environment variables, and deployment status.

## Services from services/ Directory

### 1. agno-coordinator
- **Type**: AI Team Coordination Service
- **Language**: TypeScript
- **Port**: 8080
- **Dependencies**: Node.js, Express
- **Environment Variables**: AGNO_API_KEY, TENANT
- **Health Check**: /healthz endpoint
- **Status**: Manifest exists (agno-coordinator.yaml)

### 2. agno-teams
- **Type**: AI Team Management Platform
- **Language**: Python (FastAPI)
- **Port**: 8080
- **Dependencies**: fastapi, uvicorn
- **Environment Variables**: AGNO_API_KEY, TENANT
- **Health Check**: /healthz endpoint
- **Status**: Manifest exists (agno-teams.yaml)

### 3. agno-wrappers
- **Type**: AI Wrapper Services
- **Language**: Python
- **Port**: 8080
- **Dependencies**: TBD
- **Environment Variables**: TBD
- **Status**: No manifest found

### 4. mcp-agents
- **Type**: Agent Coordination Service
- **Language**: Python
- **Port**: 8002
- **Dependencies**: fastapi, uvicorn, redis
- **Environment Variables**: OPENROUTER_API_KEY, REDIS_URL, MCP_MODE
- **Health Check**: TBD
- **Status**: Manifest exists (mcp-agents.yaml)

### 5. mcp-apollo
- **Type**: AI-Powered Music Intelligence
- **Language**: Python (FastAPI)
- **Port**: 8080
- **Dependencies**: fastapi, uvicorn
- **Environment Variables**: APOLLO_API_KEY, TENANT
- **Health Check**: /healthz endpoint
- **Status**: **MISSING MANIFEST** (needs creation)

### 6. mcp-business
- **Type**: Business Intelligence Service
- **Language**: Python
- **Port**: 8080
- **Dependencies**: TBD
- **Environment Variables**: TBD
- **Status**: Manifest exists (mcp-business.yaml)

### 7. mcp-context
- **Type**: Context/Embeddings Service
- **Language**: Python
- **Port**: 8080
- **Dependencies**: fastapi, uvicorn, redis, vector databases
- **Environment Variables**: OPENROUTER_API_KEY, REDIS_URL, etc.
- **Health Check**: /healthz endpoint
- **Status**: Manifest exists (mcp-context.yaml)

### 8. mcp-github
- **Type**: GitHub Integration Service
- **Language**: Python
- **Port**: 8080
- **Dependencies**: fastapi, uvicorn, PyGitHub
- **Environment Variables**: GITHUB_TOKEN, GITHUB_WEBHOOK_SECRET
- **Health Check**: /healthz endpoint
- **Status**: Manifest exists (mcp-github.yaml)

### 9. mcp-gong
- **Type**: Revenue Intelligence Integration
- **Language**: Python (FastAPI)
- **Port**: 8080
- **Dependencies**: fastapi, uvicorn, aiohttp
- **Environment Variables**: GONG_ACCESS_TOKEN, GONG_ACCESS_KEY, TENANT
- **Health Check**: /healthz endpoint
- **Status**: **MISSING MANIFEST** (needs creation)

### 10. mcp-hubspot
- **Type**: HubSpot CRM Integration
- **Language**: Python
- **Port**: 8080
- **Dependencies**: fastapi, uvicorn, hubspot-api-client
- **Environment Variables**: HUBSPOT_API_KEY, HUBSPOT_CLIENT_ID, HUBSPOT_CLIENT_SECRET
- **Health Check**: /healthz endpoint
- **Status**: Manifest exists (mcp-hubspot.yaml)

### 11. mcp-lambda
- **Type**: Lambda Labs GPU Orchestration
- **Language**: Python
- **Port**: 8080
- **Dependencies**: fastapi, uvicorn, boto3
- **Environment Variables**: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, LAMBDA_API_KEY
- **Health Check**: /healthz endpoint
- **Status**: Manifest exists (mcp-lambda.yaml)

### 12. mcp-research
- **Type**: Research Service with GPU Access
- **Language**: Python
- **Port**: 8080
- **Dependencies**: fastapi, uvicorn, transformers, torch
- **Environment Variables**: OPENROUTER_API_KEY, CUDA_VISIBLE_DEVICES
- **Health Check**: /healthz endpoint
- **Status**: Manifest exists (mcp-research.yaml)

### 13. mcp-salesforce
- **Type**: Salesforce CRM Integration
- **Language**: Python (FastAPI)
- **Port**: 8080
- **Dependencies**: fastapi, uvicorn, aiohttp, base64
- **Environment Variables**: SALESFORCE_CLIENT_ID, SALESFORCE_CLIENT_SECRET, SALESFORCE_USERNAME, SALESFORCE_PASSWORD, SALESFORCE_INSTANCE_URL, TENANT
- **Health Check**: /healthz endpoint
- **Status**: **MISSING MANIFEST** (needs creation)

### 14. mcp-slack
- **Type**: Communication Integration
- **Language**: Python (FastAPI)
- **Port**: 8080
- **Dependencies**: fastapi, uvicorn, aiohttp
- **Environment Variables**: SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, TENANT
- **Health Check**: /healthz endpoint
- **Status**: **MISSING MANIFEST** (needs creation)

### 15. orchestrator
- **Type**: Service Orchestration Platform
- **Language**: Python
- **Port**: 8080
- **Dependencies**: fastapi, uvicorn, redis, kubernetes-client
- **Environment Variables**: REDIS_URL, KUBECONFIG
- **Health Check**: /healthz endpoint
- **Status**: Manifest exists (orchestrator.yaml)

## Services from mcp/ Directory

### 16. agents-swarm
- **Type**: AI Agent Swarm Coordination
- **Language**: Python
- **Port**: 8080
- **Dependencies**: fastapi, uvicorn, redis
- **Environment Variables**: REDIS_URL, OPENROUTER_API_KEY
- **Status**: No manifest found

### 17. analytics-mcp
- **Type**: Analytics and Metrics Service
- **Language**: Python
- **Port**: 8080
- **Dependencies**: fastapi, uvicorn, pandas, matplotlib
- **Environment Variables**: DATABASE_URL, ANALYTICS_API_KEY
- **Status**: No manifest found

### 18. comms-mcp
- **Type**: Communications MCP Service
- **Language**: Python
- **Port**: 8080
- **Dependencies**: fastapi, uvicorn, twilio, sendgrid
- **Environment Variables**: TWILIO_SID, TWILIO_TOKEN, SENDGRID_API_KEY
- **Status**: No manifest found

### 19. crm-mcp
- **Type**: CRM Integration Service
- **Language**: Python
- **Port**: 8080
- **Dependencies**: fastapi, uvicorn, salesforce-api
- **Environment Variables**: SALESFORCE_CLIENT_ID, SALESFORCE_CLIENT_SECRET
- **Status**: No manifest found

### 20. enrichment-mcp
- **Type**: Data Enrichment Service
- **Language**: Python (FastAPI)
- **Port**: 8080
- **Dependencies**: httpx, fastapi, pydantic, uvicorn, asyncio
- **Environment Variables**: PORTKEY_API_KEY, USERGEMS_API_KEY, APOLLO_API_KEY, SALESNAV_ACCESS_TOKEN, PHANTOMBUSTER_API_KEY, COSTAR_API_KEY, SEARCH_API_KEY
- **Health Check**: /healthz endpoint
- **Status**: No manifest found

### 21. gong-mcp
- **Type**: Gong Integration Service
- **Language**: Python
- **Port**: 8080
- **Dependencies**: fastapi, uvicorn, aiohttp
- **Environment Variables**: GONG_ACCESS_TOKEN, GONG_ACCESS_KEY
- **Status**: No manifest found

### 22. projects-mcp
- **Type**: Project Management Service
- **Language**: Python
- **Port**: 8080
- **Dependencies**: fastapi, uvicorn, jira, asana
- **Environment Variables**: JIRA_API_TOKEN, ASANA_ACCESS_TOKEN
- **Status**: No manifest found

### 23. support-mcp
- **Type**: Customer Support Integration
- **Language**: Python (FastAPI)
- **Port**: 8080
- **Dependencies**: httpx, fastapi, pydantic, uvicorn, hashlib, hmac
- **Environment Variables**: INTERCOM_ACCESS_TOKEN, INTERCOM_APP_ID, INTERCOM_WEBHOOK_SECRET, PORTKEY_API_KEY
- **Health Check**: /healthz endpoint
- **Status**: No manifest found

## Common Dependencies Across Services

### Python Services (Majority)
- **Core**: fastapi, uvicorn, pydantic
- **HTTP Clients**: aiohttp, httpx
- **Async**: asyncio
- **Security**: hashlib, hmac, base64
- **Environment**: python-dotenv

### Infrastructure Dependencies
- **Database**: redis, postgresql
- **Message Queue**: redis
- **Secrets**: kubernetes-secrets
- **Monitoring**: prometheus, grafana

## Environment Variables Summary

### Authentication & API Keys
- OPENROUTER_API_KEY (multiple services)
- GONG_ACCESS_TOKEN, GONG_ACCESS_KEY
- SALESFORCE_CLIENT_ID, SALESFORCE_CLIENT_SECRET, SALESFORCE_USERNAME, SALESFORCE_PASSWORD
- SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET
- APOLLO_API_KEY
- AGNO_API_KEY
- GITHUB_TOKEN, GITHUB_WEBHOOK_SECRET
- HUBSPOT_API_KEY, HUBSPOT_CLIENT_ID, HUBSPOT_CLIENT_SECRET
- AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, LAMBDA_API_KEY
- INTERCOM_ACCESS_TOKEN, INTERCOM_APP_ID, INTERCOM_WEBHOOK_SECRET
- PORTKEY_API_KEY
- USERGEMS_API_KEY
- SALESNAV_ACCESS_TOKEN
- PHANTOMBUSTER_API_KEY
- COSTAR_API_KEY
- SEARCH_API_KEY

### Infrastructure
- REDIS_URL
- DATABASE_URL
- TENANT
- MCP_MODE
- CUDA_VISIBLE_DEVICES
- KUBECONFIG

## Deployment Status

### Existing Manifests (13 services)
- agno-coordinator.yaml
- agno-teams.yaml
- mcp-agents.yaml
- mcp-business.yaml
- mcp-context.yaml
- mcp-github.yaml
- mcp-hubspot.yaml
- mcp-lambda.yaml
- mcp-research.yaml
- orchestrator.yaml
- sophia-business.yaml
- sophia-dashboard.yaml
- sophia-github.yaml
- sophia-hubspot.yaml
- sophia-lambda.yaml

### Missing Manifests (10+ services)
- **Priority 1 (Task Specified)**: mcp-gong, mcp-salesforce, mcp-slack, mcp-apollo
- **Priority 2**: agno-wrappers, agents-swarm, analytics-mcp, comms-mcp, crm-mcp, enrichment-mcp, gong-mcp, projects-mcp, support-mcp

## Health Check Endpoints

Most FastAPI services implement:
- `/healthz` - Basic health check
- `/` - Service info and status
- Various service-specific endpoints

## Next Steps

1. Create missing Kubernetes manifests for priority services
2. Implement automated Docker build pipelines
3. Establish comprehensive health check validation
4. Create container management scripts
5. Set up monitoring and alerting
6. Implement secrets management
7. Configure ingress and load balancing
8. Set up CI/CD pipelines

---

*Generated on: 2025-08-27*
*Total Services Cataloged: 23*
*Services with Manifests: 15*
*Services Missing Manifests: 8*