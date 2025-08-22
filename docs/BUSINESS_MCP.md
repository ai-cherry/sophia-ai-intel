# Business MCP v1 - GTM/RevOps Integrations

**Service**: [`sophiaai-mcp-business-v2`](https://sophiaai-mcp-business-v2.fly.dev)  
**Version**: 1.0.0  
**Status**: Production-ready with CEO-gated operations  

## Overview

The Business MCP v1 is a comprehensive GTM/RevOps intelligence platform that integrates with leading business systems including Apollo, UserGems, HubSpot, Salesforce, Gong, and Slack. It provides prospect search, enrichment, CRM synchronization, revenue signal analysis, and compliant data intake capabilities.

### Key Features

- **Multi-CRM Integration**: Apollo, HubSpot, Salesforce with read/write controls
- **Revenue Intelligence**: UserGems job change alerts, Gong call insights
- **Communication Analysis**: Slack channel digests and GTM signal extraction
- **Data Intake**: CSV uploads with TOS-compliant manual processing
- **Normalized Error Handling**: Consistent JSON error format across providers
- **CEO-Gated Operations**: All write operations require manual approval
- **Database Integration**: PostgreSQL storage with optional vector search

## API Endpoints

### Health Check
```http
GET /healthz
```

**Response**:
```json
{
  "status": "healthy|degraded|unhealthy",
  "service": "sophia-mcp-business-v1",
  "version": "1.0.0",
  "providers": {
    "apollo": "ready|missing_secret",
    "usergems": "ready|missing_secret",
    "hubspot": "ready|missing_secret",
    "salesforce": "ready|missing_secret",
    "gong": "ready|missing_secret",
    "slack": "ready|missing_secret",
    "zillow": "ready|missing_secret",
    "storage": "ready|missing_secret",
    "qdrant": "ready|missing_secret",
    "redis": "ready|missing_secret",
    "llm_router": "ready|missing_secret"
  },
  "database": "connected|error|not_configured",
  "capabilities": {
    "prospects_search": true,
    "prospects_enrich": false,
    "prospects_sync": true,
    "signals_digest": false,
    "intake_upload": true
  }
}
```

### Prospects Search
```http
POST /prospects/search
```

**Request**:
```json
{
  "query": "multifamily AI delinquency prevention",
  "k": 10,
  "providers": ["apollo", "hubspot"],
  "lists": ["q1-targets"],
  "score_min": 50.0,
  "timeout_s": 30,
  "budget_cents": 500
}
```

**Response**:
```json
{
  "status": "success|partial|failed",
  "query": "multifamily AI delinquency prevention",
  "results": [
    {
      "id": "uuid-string",
      "company_name": "PropTech Corp",
      "company_domain": "proptech.com",
      "contact_name": "Jane Smith",
      "contact_title": "VP of Operations",
      "contact_email": "jane@proptech.com",
      "score": 85.5,
      "source": "apollo",
      "tags": ["prospected", "ai-focus"],
      "created_at": "2025-08-22T19:45:00Z"
    }
  ],
  "summary": {
    "text": "Found 10 prospects across 2 providers",
    "confidence": 0.9,
    "model": "business_search_v1",
    "sources": ["apollo", "hubspot"],
    "avg_score": 75.2
  },
  "providers_used": ["apollo", "hubspot"],
  "providers_failed": [],
  "total_cost_cents": 250,
  "execution_time_ms": 2500,
  "timestamp": "2025-08-22T19:45:00Z"
}
```

### Prospects Enrichment
```http
POST /prospects/enrich
```

**Request**:
```json
{
  "emails": ["jane@proptech.com", "john@aistart.io"],
  "domains": ["proptech.com"],
  "provider": "apollo"
}
```

**Response**:
```json
{
  "status": "success",
  "provider": "apollo",
  "results": [
    {
      "email": "jane@proptech.com",
      "provider": "apollo",
      "status": "enriched",
      "data": {
        "company_info": "PropTech Corp - 50-200 employees",
        "social_links": ["linkedin.com/in/janesmith"],
        "verification_status": "valid"
      }
    }
  ],
  "total_cost_cents": 50,
  "execution_time_ms": 1200,
  "timestamp": "2025-08-22T19:45:00Z"
}
```

### Prospects Synchronization
```http
POST /prospects/sync
```

**Request**:
```json
{
  "list": "q1-multifamily-targets",
  "provider": "hubspot",
  "mode": "read"
}
```

**Response**:
```json
{
  "status": "success",
  "sync_results": {
    "list": "q1-multifamily-targets",
    "provider": "hubspot",
    "mode": "read",
    "status": "completed",
    "records_processed": 150,
    "records_synced": 145,
    "errors": []
  },
  "execution_time_ms": 5000,
  "timestamp": "2025-08-22T19:45:00Z"
}
```

### Revenue Signals Digest
```http
POST /signals/digest
```

**Request**:
```json
{
  "window": "7d",
  "channels": ["slack:#gtm", "slack:#revenue"]
}
```

**Response**:
```json
{
  "status": "success",
  "window": "7d",
  "channels": ["slack:#gtm"],
  "digest_results": {
    "slack": {
      "channels_processed": 1,
      "messages_found": 47,
      "key_topics": [
        {
          "text": "New pipeline opportunity with PropTech Corp - $50K ARR potential",
          "timestamp": "1724356800",
          "channel": "gtm"
        }
      ],
      "mentions": ["@sales", "@marketing"],
      "window": "7d"
    }
  },
  "providers_used": ["slack"],
  "providers_failed": [],
  "execution_time_ms": 1800,
  "timestamp": "2025-08-22T19:45:00Z"
}
```

### Data Intake Upload
```http
POST /intake/upload
```

**Form Data**:
- `provider`: linkedin|costar|nmhc|csv
- `file`: CSV file upload

**Response**:
```json
{
  "status": "success",
  "upload_results": {
    "provider": "csv",
    "filename": "prospects_q1.csv",
    "status": "completed",
    "row_count": 250,
    "success_count": 240,
    "error_count": 10,
    "sample_records": [
      {
        "company": "PropTech Solutions",
        "contact": "Sarah Johnson",
        "title": "CTO"
      }
    ]
  },
  "execution_time_ms": 3000,
  "timestamp": "2025-08-22T19:45:00Z"
}
```

### Provider Status
```http
GET /providers
```

Returns current provider configuration and readiness status (names only).

## Provider Configuration Matrix

### CRM Providers

| Provider | Secrets Required | Status | Capabilities | Cost Model |
|----------|-----------------|---------|-------------|------------|
| **Apollo** | `APOLLO_API_KEY` | ❌ Missing | Contact enrichment, company search, prospect scoring | $0.10 per prospect |
| **HubSpot** | `HUBSPOT_ACCESS_TOKEN` | ❌ Missing | CRM sync, contact management, deal pipeline | $0.05 per API call |
| **Salesforce** | `SALESFORCE_CLIENT_ID`<br>`SALESFORCE_CLIENT_SECRET`<br>`SALESFORCE_USERNAME`<br>`SALESFORCE_PASSWORD`<br>`SALESFORCE_SECURITY_TOKEN`<br>`SALESFORCE_DOMAIN` | ❌ Missing | Full CRM access (read-only until CEO approval) | Included in license |

### Revenue Intelligence

| Provider | Secrets Required | Status | Capabilities | Cost Model |
|----------|-----------------|---------|-------------|------------|
| **UserGems** | `USERGEMS_API_KEY` | ❌ Missing | Job change alerts, buyer intent signals | $0.25 per signal |
| **Gong** | `GONG_BASE_URL`<br>`GONG_ACCESS_KEY`<br>`GONG_ACCESS_KEY_SECRET`<br>`GONG_CLIENT_ACCESS_KEY`<br>`GONG_CLIENT_SECRET` | ❌ Missing | Call recordings, meeting insights, revenue forecasting | Included in license |

### Communication & Signals

| Provider | Secrets Required | Status | Capabilities | Cost Model |
|----------|-----------------|---------|-------------|------------|
| **Slack** | `SLACK_BOT_TOKEN`<br>`SLACK_SIGNING_SECRET` | ❌ Missing | Channel digests, GTM signal extraction, notifications | Free (bot usage) |

### Optional Integrations

| Provider | Secrets Required | Status | Capabilities | Cost Model |
|----------|-----------------|---------|-------------|------------|
| **Zillow** | `ZILLOW_API_KEY` | ❌ Missing | Property data, market insights (multifamily focus) | $0.01 per query |

### Storage & Infrastructure

| Provider | Secrets Required | Status | Capabilities | Cost Model |
|----------|-----------------|---------|-------------|------------|
| **Neon PostgreSQL** | `NEON_DATABASE_URL` | ✅ Ready | Primary database, prospect storage | $0.10/GB/month |
| **Qdrant** | `QDRANT_URL` | ❌ Missing | Vector search, prospect similarity | $0.50/1M vectors |
| **Redis** | `REDIS_URL` | ❌ Missing | Caching, rate limiting | $0.05/GB/month |
| **Portkey** | `PORTKEY_API_KEY` | ✅ Ready | LLM routing for summarization | $0.002/1K tokens |

## CSV Templates for Manual Data Intake

### LinkedIn Sales Navigator Export (TOS Compliant)
```csv
company_name,contact_name,contact_title,contact_email,company_domain,company_size,industry,location
PropTech Solutions,Sarah Johnson,CTO,sarah@proptech.com,proptech.com,51-200,Real Estate Technology,San Francisco
```

**TOS Note**: LinkedIn data must be manually exported through official Sales Navigator interface. Automated scraping is prohibited.

### CoStar Property Data (TOS Compliant)
```csv
property_name,property_type,owner_company,contact_name,contact_email,units,market,submarket
Maple Heights Apartments,Multifamily,ABC Properties,John Smith,john@abcprops.com,150,Dallas,Richardson
```

**TOS Note**: CoStar data must be accessed through official API or manually exported. Screen scraping violates terms of service.

### NMHC Membership Directory (TOS Compliant)
```csv
member_company,primary_contact,title,email,phone,properties_managed,focus_area
Multifamily Partners,Lisa Chen,Director of Operations,lisa@mfpartners.com,(555) 123-4567,2500,Affordable Housing
```

**TOS Note**: NMHC member data should be manually collected or accessed through official membership benefits only.

### General Prospect CSV Template
```csv
list_name,company_name,company_domain,contact_name,contact_title,contact_email,contact_phone,source,score,tags
Q1 Targets,AI Innovations Inc,aiinnovations.com,Mike Wilson,VP Engineering,mike@aiinnovations.com,(555) 987-6543,manual,75.0,"ai,proptech,series-b"
```

## Terms of Service & Compliance

### Prohibited Data Sources
- **LinkedIn Scraping**: Automated extraction from LinkedIn profiles or company pages
- **CoStar Screen Scraping**: Automated collection of property or contact data
- **NMHC Unauthorized Access**: Collection beyond official membership benefits
- **Email Harvesting**: Bulk collection of email addresses without consent

### Approved Data Collection Methods
- **Official APIs**: Using provider-approved API endpoints with proper authentication
- **Manual Exports**: Hand-copying or officially exported data files
- **Opt-in Forms**: Contacts who have explicitly provided information
- **Public Business Information**: Publicly available company and contact data

### Data Handling Compliance
- **GDPR**: EU contact data requires explicit consent for processing
- **CAN-SPAM**: Email outreach must include unsubscribe mechanisms
- **CCPA**: California residents have right to data deletion
- **SOX**: Financial data handling for public companies requires audit trails

## Sophia Infra Integration Examples

### Search Operations
```yaml
# Via GitHub Actions: sophia_infra.yml
inputs:
  provider: biz
  action: search
  payload_json: |
    {
      "query": "AI PropTech multifamily portfolio management",
      "k": 20,
      "providers": ["apollo", "hubspot"],
      "score_min": 60.0,
      "budget_cents": 1000
    }
```

### Enrichment Operations
```yaml
inputs:
  provider: biz
  action: enrich
  payload_json: |
    {
      "emails": ["cto@proptech.com", "vp@aistart.io"],
      "provider": "apollo"
    }
```

### CRM Synchronization (Read-Only)
```yaml
inputs:
  provider: biz
  action: sync
  payload_json: |
    {
      "list": "q2-enterprise-targets",
      "provider": "hubspot",
      "mode": "read"
    }
```

### Revenue Signals Digest
```yaml
inputs:
  provider: biz
  action: digest
  payload_json: |
    {
      "window": "24h",
      "channels": ["slack:#gtm", "slack:#revenue", "slack:#customer-success"]
    }
```

### CSV Data Upload
```yaml
inputs:
  provider: biz
  action: upload
  payload_json: |
    {
      "provider": "csv",
      "filename": "q1_linkedin_prospects.csv"
    }
```

## Error Handling & Troubleshooting

### Common Error Codes

| Error Code | Provider | Description | Resolution |
|------------|----------|-------------|------------|
| `no-providers` | biz | No business providers configured | Add at least one CRM provider secret |
| `missing-api-key` | apollo | Apollo API key not found | Add `APOLLO_API_KEY` to GitHub secrets |
| `tos-gated` | linkedin | LinkedIn scraping attempted | Use manual CSV upload method |
| `write-disabled` | salesforce | Write operation blocked | CEO must approve write workflow |
| `budget-exceeded` | biz | Cost limit exceeded | Increase `budget_cents` parameter |
| `database-error` | storage | Database connection failed | Check `NEON_DATABASE_URL` configuration |

### Normalized Error Format
```json
{
  "status": "failure",
  "query": "operation_name",
  "results": [],
  "summary": {
    "text": "Human-readable error description",
    "confidence": 1.0,
    "model": "n/a",
    "sources": []
  },
  "timestamp": "2025-08-22T19:45:00Z",
  "execution_time_ms": 0,
  "errors": [
    {
      "provider": "apollo",
      "code": "MISSING_API_KEY",
      "message": "APOLLO_API_KEY not configured for prospect search"
    }
  ]
}
```

## CEO Dashboard Usage

### GTM Tab Features
The CEO GTM tab in the Sophia Dashboard provides:

- **Real-time Prospect View**: Top prospects with scores and provider badges
- **Revenue Signals**: 7-day digest of Slack GTM channel activity
- **Quick Actions**: One-click access to search, sync, and digest operations
- **Service Health**: Direct monitoring of Business MCP availability

### Security Controls
- **Read Operations**: Direct API calls to Business MCP (no CEO approval)
- **Write Operations**: Redirected to Sophia Infra workflows (CEO approval required)
- **Salesforce Writes**: Explicitly gated until CEO approves write workflow
- **Cost Controls**: Maximum $100 per operation, configurable budgets

### Quick Action Links
All action buttons in the GTM dashboard generate deep links to GitHub Actions workflows:
- `https://github.com/ai-cherry/sophia-ai-intel/actions/workflows/sophia_infra.yml`
- Pre-filled with provider=biz, action, and payload parameters
- Maintains CEO approval gate for all production operations

## Database Schema

### Core Tables
```sql
-- Companies: Master company records
CREATE TABLE companies (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE,
    source VARCHAR(100) NOT NULL,
    meta_json JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Contacts: Individual contacts within companies  
CREATE TABLE contacts (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    source VARCHAR(100) NOT NULL,
    meta_json JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prospects: Qualified leads with scoring
CREATE TABLE prospects (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    contact_id UUID REFERENCES contacts(id),
    list VARCHAR(100) NOT NULL,
    tags TEXT[] DEFAULT '{}',
    score DECIMAL(5,2) DEFAULT 0.0,
    source VARCHAR(100) NOT NULL,
    meta_json JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Signals: Business intelligence events
CREATE TABLE signals (
    id UUID PRIMARY KEY,
    kind VARCHAR(100) NOT NULL,
    payload_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Uploads: CSV and manual data tracking
CREATE TABLE uploads (
    id UUID PRIMARY KEY,
    provider VARCHAR(100) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'processing',
    row_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Deployment Architecture

### Service Stack
- **Runtime**: Python 3.11 + FastAPI + Uvicorn
- **Database**: Neon PostgreSQL with connection pooling
- **Deployment**: Fly.io (Pay Ready org) + Docker containers
- **Secrets**: GitHub Secrets → Fly Secrets (automatic sync)
- **Monitoring**: Health checks + proof artifacts + error logging

### CEO-Controlled Operations
- **Manual Deployment**: Deploy All workflow via GitHub Actions UI
- **Database Migrations**: Applied automatically during deployment
- **Secret Management**: GitHub repository secrets with Fly synchronization
- **Write Operation Approval**: All CRM writes require CEO manual trigger

### Integration Points
- **Sophia Dashboard**: CEO GTM tab with real-time data
- **Sophia Infra**: CEO-gated operations control plane
- **GitHub Actions**: Automated validation and proof collection
- **External APIs**: Direct integration with business providers

## Production Readiness

### Current Status
- ✅ **Service Implementation**: 607 lines of production FastAPI code
- ✅ **Database Schema**: Complete PostgreSQL schema with indexing
- ✅ **CEO Dashboard**: GTM tab with full functionality
- ✅ **Sophia Infra Integration**: 5 business operations (search, enrich, sync, digest, upload)
- ✅ **Deployment Configuration**: Fly.io + Docker with secret management
- ⚠️ **Provider Configuration**: Storage + LLM ready, business providers await secrets

### Missing Secrets for Full Functionality
**Critical for Search/Enrichment**:
- `APOLLO_API_KEY` - Apollo.io prospect search and enrichment
- `HUBSPOT_ACCESS_TOKEN` - HubSpot CRM synchronization

**Optional for Enhanced Features**:
- `USERGEMS_API_KEY` - Job change alerts and buyer signals
- `SLACK_BOT_TOKEN` + `SLACK_SIGNING_SECRET` - GTM channel analysis
- `SALESFORCE_CLIENT_ID` + related OAuth secrets - Full CRM integration
- `GONG_BASE_URL` + `GONG_ACCESS_KEY` - Revenue intelligence

### Next Steps for CEO
1. **Deploy Services**: Run "Deploy All" workflow from GitHub Actions
2. **Add Provider Secrets**: Configure business provider API keys as needed
3. **Test GTM Dashboard**: Access new GTM tab for prospect and signal data
4. **Approve Write Operations**: Enable Salesforce write mode when ready

---

**Last Updated**: 2025-08-22  
**Next Review**: After provider secret configuration  
**Owner**: CEO - Sophia AI Infrastructure Team  
**Support**: Review proofs/biz/ directory for operational status