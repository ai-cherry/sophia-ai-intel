# Production Secrets Replacement Checklist

## CRITICAL - MUST REPLACE BEFORE DEPLOYMENT:
- [ ] OPENAI_API_KEY - Get from OpenAI platform
- [ ] ANTHROPIC_API_KEY - Get from Anthropic console
- [ ] QDRANT_API_KEY - Get from Qdrant Cloud dashboard
- [ ] REDIS_URL - Get from Redis Cloud console
- [ ] POSTGRES_URL - Get from Neon console

## HIGH PRIORITY - BUSINESS INTEGRATIONS:
- [ ] HUBSPOT_API_KEY - Get from HubSpot developer settings
- [ ] GONG_ACCESS_KEY - Get from Gong admin settings
- [ ] SALESFORCE credentials - Get from Salesforce org
- [ ] SLACK tokens - Get from Slack app settings
- [ ] GITHUB_APP credentials - Create GitHub App

## MEDIUM PRIORITY - RESEARCH & MONITORING:
- [ ] SERPAPI_API_KEY - Get from SerpApi account
- [ ] TAVILY_API_KEY - Get from Tavily account  
- [ ] DNSIMPLE_API_KEY - Get from DNSimple account
- [ ] DOCKER_PAT - Generate from Docker Hub

## VALIDATION REQUIRED:
- [ ] Test all database connections
- [ ] Validate all API key permissions
- [ ] Verify service-to-service connectivity
- [ ] Test health check endpoints

## SECURITY VERIFICATION:
- [ ] Ensure no secrets in git history
- [ ] Validate Kubernetes secret creation
- [ ] Test secret rotation procedures
- [ ] Verify access control policies
