# Research MCP v2 - Multi-Provider Meta-Aggregator

**Service**: [`sophiaai-mcp-research-v2`](https://sophiaai-mcp-research-v2.fly.dev)  
**Version**: 2.0.0  
**Status**: Production-ready with CEO-gated operations  

## Overview

The Research MCP v2 is a comprehensive multi-provider research meta-aggregator that combines search, scraping, and AI summarization capabilities. It provides normalized error handling, cost controls, and proof-first operations through the Sophia Infrastructure control plane.

### Key Features

- **Multi-Provider Search**: Tavily, Serper, Perplexity, Exa
- **Web Scraping**: Apify, ZenRows, Bright Data  
- **AI Summarization**: Portkey, OpenRouter LLM routing
- **Cost Controls**: Per-operation limits and provider cost tracking
- **Normalized Errors**: Consistent JSON error format across all providers
- **Proof Artifacts**: All operations generate audit trails in `proofs/research/`
- **CEO-Gated Deployment**: Production changes require manual approval

## Endpoints

### Health Check
```http
GET /healthz
```

**Response**:
```json
{
  "status": "healthy|degraded",
  "service": "sophia-mcp-research-v2",
  "version": "2.0.0",
  "providers": {
    "search_providers": {
      "tavily": "ready|missing_secret",
      "serper": "ready|missing_secret", 
      "perplexity": "ready|missing_secret",
      "exa": "ready|missing_secret"
    },
    "scraping_providers": {
      "apify": "ready|missing_secret",
      "zenrows": "ready|missing_secret",
      "brightdata": "ready|missing_secret"
    },
    "llm_routing": {
      "portkey": "ready|missing_secret",
      "openrouter": "ready|missing_secret"
    },
    "caching": {
      "redis": "ready|missing_secret"
    }
  },
  "capabilities": {
    "search": true,
    "scrape": true,
    "summarize": true,
    "cache": false
  }
}
```

### Multi-Provider Search
```http
POST /search
```

**Request**:
```json
{
  "query": "AI research and development trends",
  "providers": ["tavily", "serper"],
  "max_results": 10,
  "summarize": true,
  "cost_limit_usd": 1.0
}
```

**Response**:
```json
{
  "status": "success|partial|failed",
  "query": "AI research and development trends",
  "results": [
    {
      "title": "Article Title",
      "url": "https://example.com/article",
      "snippet": "Article excerpt...",
      "source": "web",
      "score": 0.95,
      "provider": "tavily",
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ],
  "summary": {
    "text": "AI research is focusing on...",
    "model": "gpt-4o-mini",
    "provider": "portkey",
    "confidence": 0.8
  },
  "providers_used": ["tavily", "serper"],
  "providers_failed": [],
  "cost_breakdown": {
    "tavily": 0.005,
    "serper": 0.005,
    "summarization": 0.002
  },
  "total_cost_usd": 0.012,
  "execution_time_ms": 2500,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Web Scraping
```http
POST /scrape
```

**Request**:
```json
{
  "url": "https://example.com/article",
  "providers": ["zenrows"],
  "extract_type": "content",
  "javascript_enabled": false
}
```

**Response**:
```json
{
  "status": "success|failed",
  "url": "https://example.com/article",
  "results": [
    {
      "url": "https://example.com/article",
      "content": "Scraped content...",
      "status_code": 200,
      "provider": "zenrows",
      "extraction_type": "full_content",
      "timestamp": "2024-01-01T12:00:00Z",
      "metadata": {
        "content_length": 5420
      }
    }
  ],
  "providers_used": ["zenrows"],
  "providers_failed": [],
  "cost_breakdown": {
    "zenrows": 0.005
  },
  "total_cost_usd": 0.005,
  "execution_time_ms": 1200,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### AI Summarization
```http
POST /summarize
```

**Request**:
```json
{
  "content": "Long article content to summarize...",
  "style": "concise|detailed|bullet_points",
  "max_length": 500
}
```

**Response**:
```json
{
  "status": "success",
  "summary": "Generated summary...",
  "style": "concise",
  "input_length": 2450,
  "output_length": 145,
  "model_used": "gpt-4o-mini",
  "cost_usd": 0.003,
  "execution_time_ms": 800,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Provider Status
```http
GET /providers
```

Returns current provider availability and configuration status.

## Provider Configuration

### Search Providers

| Provider | Secret | Status | Capabilities |
|----------|--------|---------|-------------|
| Tavily | `TAVILY_API_KEY` | ✅ Ready | Advanced search, answer generation |
| Serper | `SERPER_API_KEY` | ✅ Ready | Google search results |
| Perplexity | `PERPLEXITY_API_KEY` | ❌ Missing | AI-powered search |
| Exa | `EXA_API_KEY` | ❌ Missing | Semantic search |

### Scraping Providers

| Provider | Secret | Status | Capabilities |
|----------|--------|---------|-------------|
| Apify | `APIFY_API_KEY` | ❌ Missing | Large-scale scraping |
| ZenRows | `ZENROWS_API_KEY` | ❌ Missing | Residential proxies, JS rendering |
| Bright Data | `BRIGHTDATA_API_KEY` | ❌ Missing | Enterprise scraping |

### LLM Routing

| Provider | Secret | Status | Capabilities |
|----------|--------|---------|-------------|
| Portkey | `PORTKEY_API_KEY` | ✅ Ready | Multi-LLM routing, cost tracking |
| OpenRouter | `OPENROUTER_API_KEY` | ❌ Missing | Alternative LLM access |

### Caching

| Provider | Secret | Status | Capabilities |
|----------|--------|---------|-------------|
| Redis | `REDIS_URL` | ❌ Missing | Response caching, rate limiting |

## Cost Controls

### Per-Operation Limits
- **Search**: Default `$1.00` per request (configurable up to `$10.00`)
- **Scraping**: `$0.005-$0.01` per URL (JS rendering costs more)
- **Summarization**: `~$0.001-$0.005` per operation (token-based)

### Provider Cost Estimates
- **Tavily**: `$0.001` per result
- **Serper**: `$0.001` per result  
- **ZenRows**: `$0.005` standard, `$0.01` with JS
- **Portkey**: Token-based pricing (GPT-4o-mini: `$0.15/1M input`, `$0.60/1M output`)

## Error Handling

All errors return normalized JSON format:

```json
{
  "error": {
    "provider": "tavily",
    "code": "API_KEY_INVALID", 
    "message": "API key is invalid or expired",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### Common Error Codes
- `MISSING_CREDENTIALS`: Required API keys not configured
- `NO_SEARCH_PROVIDERS`: No search providers available  
- `NO_LLM_PROVIDERS`: No LLM providers for summarization
- `COST_LIMIT_EXCEEDED`: Operation cost exceeds limit
- `API_KEY_INVALID`: Provider API key authentication failed
- `RATE_LIMITED`: Provider rate limit reached

## CEO-Gated Operations

All Research MCP v2 operations are controlled through the **Sophia Infrastructure** control plane with mandatory CEO approval for production changes.

### Deployment Process

1. **Code Changes**: Update [`services/mcp-research/app.py`](../services/mcp-research/app.py)
2. **CEO Approval**: Use GitHub Actions manually triggered workflow
3. **Deploy All**: Runs [`deploy_all.yml`](../.github/workflows/deploy_all.yml) with Pay Ready org enforcement
4. **Proof Generation**: Automatic health checks and operational proofs
5. **Validation**: Service health confirmed at [`/healthz`](https://sophiaai-mcp-research-v2.fly.dev/healthz)

### Sophia Infra Integration

Research operations are available through the centralized control plane:

```yaml
# Trigger research operations via Sophia Infra
inputs:
  provider: research
  action: search|scrape|summarize|validate_all|health_check
  payload: |
    {
      "query": "AI trends",
      "providers": ["tavily", "serper"],
      "max_results": 10
    }
```

### Manual Operations

For direct access (debugging/testing only):

```bash
# Health check
curl https://sophiaai-mcp-research-v2.fly.dev/healthz

# Search operation
curl -X POST https://sophiaai-mcp-research-v2.fly.dev/search \
  -H "Content-Type: application/json" \
  -d '{"query": "AI research trends", "max_results": 5}'

# Provider status
curl https://sophiaai-mcp-research-v2.fly.dev/providers
```

## Compliance & Security

### Data Handling
- **No PII Storage**: All requests are processed and discarded
- **Cost Tracking**: Operation costs logged for audit
- **Rate Limiting**: Provider-specific rate limits enforced
- **Content Filtering**: Inappropriate content detection (planned)

### Secret Management
- **GitHub Secrets**: All API keys stored as repository secrets
- **Fly Secrets**: Automatically synchronized during deployment
- **Secret Rotation**: Manual process through GitHub secrets update
- **Access Control**: Secrets limited to Pay Ready organization

### Audit Trail
All operations generate proof artifacts in [`proofs/research/`](../proofs/research/):
- `healthz.txt` - Service health status
- `search_results.json` - Search operation results  
- `scrape_results.json` - Scraping operation results
- `summarize_results.json` - Summarization results
- `validation_comprehensive.json` - Provider validation status
- `provider_summary.json` - Provider readiness summary

## Usage Examples

### Basic Search
```bash
curl -X POST https://sophiaai-mcp-research-v2.fly.dev/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "latest AI developments 2024",
    "providers": ["tavily", "serper"],
    "max_results": 8,
    "summarize": true,
    "cost_limit_usd": 0.50
  }'
```

### Web Scraping
```bash
curl -X POST https://sophiaai-mcp-research-v2.fly.dev/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://arxiv.org/abs/2401.12345",
    "providers": ["zenrows"],
    "javascript_enabled": false
  }'
```

### Content Summarization
```bash
curl -X POST https://sophiaai-mcp-research-v2.fly.dev/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Long research paper content...",
    "style": "bullet_points",
    "max_length": 300
  }'
```

## Troubleshooting

### Common Issues

**503 Service Unavailable**
- Check [`/healthz`](https://sophiaai-mcp-research-v2.fly.dev/healthz) for provider status
- Verify required secrets are configured
- At least one LLM provider (Portkey/OpenRouter) must be available

**Provider Failures**
- Check `providers_failed` field in responses
- Review [`proofs/research/validation_comprehensive.json`](../proofs/research/validation_comprehensive.json)
- Verify API key validity directly with provider

**Cost Limit Errors**
- Increase `cost_limit_usd` in requests (max $10.00)
- Review `cost_breakdown` to identify expensive operations
- Consider reducing `max_results` or disabling summarization

### Support Escalation

1. **Check Service Health**: [`/healthz`](https://sophiaai-mcp-research-v2.fly.dev/healthz)
2. **Review Recent Proofs**: [`proofs/research/`](../proofs/research/)
3. **Validate Providers**: Run validation via Sophia Infra
4. **CEO Escalation**: For production issues or secret management

## Architecture

### Service Stack
- **Runtime**: Python 3.11 + FastAPI + Uvicorn
- **Deployment**: Fly.io (Pay Ready org) + Docker
- **Secrets**: GitHub Secrets → Fly Secrets (automatic sync)
- **Monitoring**: Health checks + proof artifacts
- **Cost Control**: Per-request limits + provider tracking

### Integration Points
- **Sophia Dashboard**: Research widget (planned)
- **Sophia Infra**: CEO-gated operations control plane
- **GitHub Actions**: Automated deployment and validation
- **MCP Protocol**: Model Context Protocol compliance (planned)

---

**Last Updated**: 2025-01-01  
**Next Review**: CEO discretion based on provider expansion  
**Owner**: Sophia AI Infrastructure Team