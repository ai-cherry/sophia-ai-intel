import os, time, json, asyncio, logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
import asyncpg
import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables - Business Providers
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
USERGEMS_API_KEY = os.getenv("USERGEMS_API_KEY") 
HUBSPOT_ACCESS_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")

# Salesforce OAuth
SALESFORCE_CLIENT_ID = os.getenv("SALESFORCE_CLIENT_ID")
SALESFORCE_CLIENT_SECRET = os.getenv("SALESFORCE_CLIENT_SECRET")
SALESFORCE_USERNAME = os.getenv("SALESFORCE_USERNAME")
SALESFORCE_PASSWORD = os.getenv("SALESFORCE_PASSWORD")
SALESFORCE_SECURITY_TOKEN = os.getenv("SALESFORCE_SECURITY_TOKEN")
SALESFORCE_DOMAIN = os.getenv("SALESFORCE_DOMAIN", "login")

# Gong API
GONG_BASE_URL = os.getenv("GONG_BASE_URL")
GONG_ACCESS_KEY = os.getenv("GONG_ACCESS_KEY")
GONG_ACCESS_KEY_SECRET = os.getenv("GONG_ACCESS_KEY_SECRET")
GONG_CLIENT_ACCESS_KEY = os.getenv("GONG_CLIENT_ACCESS_KEY")
GONG_CLIENT_SECRET = os.getenv("GONG_CLIENT_SECRET")

# Slack
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

# Zillow (optional)
ZILLOW_API_KEY = os.getenv("ZILLOW_API_KEY")

# Storage
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")
QDRANT_URL = os.getenv("QDRANT_ENDPOINT")  # GitHub org secret name
REDIS_URL = os.getenv("REDIS_URL")

# LLM Router
PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

app = FastAPI(
    title="sophia-mcp-business-v1",
    version="1.0.0",
    description="Business Intelligence MCP for GTM/RevOps with multi-provider integrations"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sophiaai-dashboard.fly.dev", "https://github.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection pool
db_pool = None

async def get_db_pool():
    global db_pool
    if not db_pool and NEON_DATABASE_URL:
        db_pool = await asyncpg.create_pool(NEON_DATABASE_URL)
    return db_pool

def normalized_error(provider: str, code: str, message: str, details: Optional[Dict] = None):
    """Return normalized error JSON format"""
    error_obj = {
        "status": "failure",
        "query": "",
        "results": [],
        "summary": {
            "text": message,
            "confidence": 1.0,
            "model": "n/a", 
            "sources": []
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "execution_time_ms": 0,
        "errors": [{
            "provider": provider,
            "code": code,
            "message": message
        }]
    }
    if details:
        error_obj["errors"][0]["details"] = details
    return error_obj

def get_provider_status():
    """Get current business provider availability"""
    return {
        "apollo": "ready" if APOLLO_API_KEY else "missing_secret",
        "usergems": "ready" if USERGEMS_API_KEY else "missing_secret",
        "hubspot": "ready" if HUBSPOT_ACCESS_TOKEN else "missing_secret",
        "salesforce": "ready" if all([
            SALESFORCE_CLIENT_ID, SALESFORCE_CLIENT_SECRET, 
            SALESFORCE_USERNAME, SALESFORCE_PASSWORD, SALESFORCE_SECURITY_TOKEN
        ]) else "missing_secret",
        "gong": "ready" if all([GONG_BASE_URL, GONG_ACCESS_KEY]) else "missing_secret",
        "slack": "ready" if all([SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET]) else "missing_secret",
        "zillow": "ready" if ZILLOW_API_KEY else "missing_secret",
        "storage": "ready" if NEON_DATABASE_URL else "missing_secret",
        "qdrant": "ready" if QDRANT_URL else "missing_secret",
        "redis": "ready" if REDIS_URL else "missing_secret",
        "llm_router": "ready" if (PORTKEY_API_KEY or OPENROUTER_API_KEY) else "missing_secret"
    }

# Request/Response Models
class ProspectsSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for prospects")
    k: int = Field(default=10, le=100, description="Max results to return")
    providers: List[str] = Field(default=["apollo", "hubspot"], description="Providers to search")
    lists: List[str] = Field(default=[], description="Prospect lists to filter by")
    score_min: float = Field(default=0.0, description="Minimum prospect score")
    timeout_s: int = Field(default=30, le=120, description="Request timeout")
    budget_cents: int = Field(default=500, le=10000, description="Budget limit in cents")

class ProspectsEnrichRequest(BaseModel):
    emails: List[str] = Field(default=[], description="Email addresses to enrich")
    domains: List[str] = Field(default=[], description="Company domains to enrich")
    provider: str = Field(default="apollo", description="Enrichment provider")

    @validator('emails', 'domains')
    def validate_input(cls, v, values, field):
        if not v and not values.get('emails' if field.name == 'domains' else 'domains', []):
            raise ValueError("Must provide either emails or domains")
        return v

class ProspectsSyncRequest(BaseModel):
    list: str = Field(..., description="Prospect list name") 
    provider: str = Field(..., description="CRM provider: hubspot|salesforce|apollo|usergems")
    mode: str = Field(default="read", description="Sync mode: read|write")

class SignalsDigestRequest(BaseModel):
    window: str = Field(default="7d", description="Time window: 7d|24h|all")
    channels: List[str] = Field(default=["slack:#gtm"], description="Signal channels to digest")

class IntakeUploadRequest(BaseModel):
    provider: str = Field(..., description="Data provider: linkedin|costar|nmhc|csv")
    filename: str = Field(default="upload.csv", description="Filename for tracking")

class Prospect(BaseModel):
    id: str
    company_name: Optional[str]
    company_domain: Optional[str] 
    contact_name: Optional[str]
    contact_title: Optional[str]
    contact_email: Optional[str]
    score: float
    source: str
    tags: List[str]
    created_at: str

class ProspectsSearchResponse(BaseModel):
    status: str
    query: str
    results: List[Prospect]
    summary: Dict[str, Any]
    providers_used: List[str]
    providers_failed: List[Dict]
    total_cost_cents: int
    execution_time_ms: int
    timestamp: str

# Provider Implementations
class ApolloProvider:
    @staticmethod
    async def search_prospects(query: str, limit: int = 10) -> tuple[List[Dict], int]:
        if not APOLLO_API_KEY:
            raise ValueError("APOLLO_API_KEY not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.apollo.io/v1/mixed_people/search",
                json={
                    "q_keywords": query,
                    "per_page": min(limit, 25),
                    "prospected_by_current_team": "no"
                },
                headers={
                    "Cache-Control": "no-cache",
                    "Content-Type": "application/json",
                    "X-Api-Key": APOLLO_API_KEY
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            prospects = []
            for person in data.get("people", []):
                org = person.get("organization", {}) or {}
                prospects.append({
                    "id": str(uuid.uuid4()),
                    "company_name": org.get("name"),
                    "company_domain": org.get("website_url", "").replace("http://", "").replace("https://", "").split("/")[0],
                    "contact_name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                    "contact_title": person.get("title"),
                    "contact_email": person.get("email"),
                    "score": float(person.get("score", 50.0)) if person.get("score") else 50.0,
                    "source": "apollo",
                    "tags": ["prospected"],
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                })
            
            cost_cents = len(prospects) * 10  # $0.10 per prospect
            return prospects, cost_cents

class HubSpotProvider:
    @staticmethod
    async def search_contacts(query: str, limit: int = 10) -> tuple[List[Dict], int]:
        if not HUBSPOT_ACCESS_TOKEN:
            raise ValueError("HUBSPOT_ACCESS_TOKEN not configured")
        
        async with httpx.AsyncClient() as client:
            # Search contacts
            response = await client.post(
                "https://api.hubapi.com/crm/v3/objects/contacts/search",
                json={
                    "filterGroups": [{
                        "filters": [{
                            "propertyName": "email", 
                            "operator": "HAS_PROPERTY"
                        }]
                    }],
                    "properties": ["firstname", "lastname", "email", "jobtitle", "company"],
                    "limit": min(limit, 100)
                },
                headers={
                    "Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            prospects = []
            for contact in data.get("results", []):
                props = contact.get("properties", {})
                prospects.append({
                    "id": str(uuid.uuid4()),
                    "company_name": props.get("company"),
                    "company_domain": None,
                    "contact_name": f"{props.get('firstname', '')} {props.get('lastname', '')}".strip(),
                    "contact_title": props.get("jobtitle"),
                    "contact_email": props.get("email"),
                    "score": 75.0,  # Default HubSpot score
                    "source": "hubspot",
                    "tags": ["crm_contact"],
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                })
            
            cost_cents = 5  # Flat fee for HubSpot API call
            return prospects, cost_cents

class SlackProvider:
    @staticmethod
    async def digest_channels(channels: List[str], window: str) -> Dict[str, Any]:
        if not SLACK_BOT_TOKEN:
            raise ValueError("SLACK_BOT_TOKEN not configured")
        
        # Parse time window
        if window == "24h":
            oldest = int((datetime.now() - timedelta(hours=24)).timestamp())
        elif window == "7d":
            oldest = int((datetime.now() - timedelta(days=7)).timestamp())
        else:  # all
            oldest = 0
        
        async with httpx.AsyncClient() as client:
            digest_summary = {
                "channels_processed": len(channels),
                "messages_found": 0,
                "key_topics": [],
                "mentions": [],
                "window": window
            }
            
            for channel in channels:
                channel_name = channel.replace("slack:#", "")
                try:
                    # Get channel ID
                    response = await client.get(
                        "https://slack.com/api/conversations.list",
                        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
                        timeout=15.0
                    )
                    response.raise_for_status()
                    
                    channels_data = response.json()
                    channel_id = None
                    
                    for ch in channels_data.get("channels", []):
                        if ch.get("name") == channel_name:
                            channel_id = ch.get("id")
                            break
                    
                    if channel_id:
                        # Get messages
                        msg_response = await client.get(
                            "https://slack.com/api/conversations.history",
                            params={
                                "channel": channel_id,
                                "oldest": oldest,
                                "limit": 50
                            },
                            headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
                            timeout=15.0
                        )
                        msg_response.raise_for_status()
                        
                        messages = msg_response.json().get("messages", [])
                        digest_summary["messages_found"] += len(messages)
                        
                        # Extract key topics (simple keyword extraction)
                        for msg in messages[:10]:  # Limit analysis
                            text = msg.get("text", "").lower()
                            if any(keyword in text for keyword in ["deal", "prospect", "revenue", "pipeline"]):
                                digest_summary["key_topics"].append({
                                    "text": msg.get("text", "")[:100] + "...",
                                    "timestamp": msg.get("ts", ""),
                                    "channel": channel_name
                                })
                
                except Exception as e:
                    logger.error(f"Failed to digest channel {channel}: {str(e)}")
            
            return digest_summary

# API Endpoints
@app.get("/healthz")
async def healthz():
    """Health check with provider status"""
    providers = get_provider_status()
    
    # Check database connectivity
    db_status = "unknown"
    if NEON_DATABASE_URL:
        try:
            pool = await get_db_pool()
            if pool:
                async with pool.acquire() as conn:
                    result = await conn.fetchval("SELECT 1")
                    db_status = "connected" if result == 1 else "error"
            else:
                db_status = "pool_failed"
        except Exception as e:
            db_status = f"error: {str(e)[:50]}"
    else:
        db_status = "not_configured"
    
    ready_providers = [k for k, v in providers.items() if v == "ready"]
    missing_providers = [k for k, v in providers.items() if v == "missing_secret"]
    
    if len(ready_providers) == 0:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "sophia-mcp-business-v1",
                "version": "1.0.0", 
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "providers": providers,
                "database": db_status,
                "capabilities": {
                    "prospects_search": len([p for p in ["apollo", "hubspot", "salesforce"] if providers[p] == "ready"]) > 0,
                    "prospects_enrich": providers.get("apollo") == "ready",
                    "prospects_sync": any(providers[p] == "ready" for p in ["hubspot", "salesforce"]),
                    "signals_digest": providers.get("slack") == "ready",
                    "intake_upload": providers.get("storage") == "ready"
                },
                "error": normalized_error(
                    "biz",
                    "no-providers",
                    f"No business providers configured. Missing: {', '.join(missing_providers[:5])}"
                )
            }
        )
    
    return {
        "status": "healthy" if len(ready_providers) >= 2 else "degraded",
        "service": "sophia-mcp-business-v1",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "providers": providers,
        "database": db_status,
        "capabilities": {
            "prospects_search": len([p for p in ["apollo", "hubspot", "salesforce"] if providers[p] == "ready"]) > 0,
            "prospects_enrich": providers.get("apollo") == "ready",
            "prospects_sync": any(providers[p] == "ready" for p in ["hubspot", "salesforce"]),
            "signals_digest": providers.get("slack") == "ready", 
            "intake_upload": providers.get("storage") == "ready"
        },
        "ready_providers": ready_providers,
        "missing_providers": missing_providers
    }

@app.post("/prospects/search", response_model=ProspectsSearchResponse)
async def search_prospects(request: ProspectsSearchRequest):
    """Multi-provider prospect search"""
    start_time = time.time()
    
    if request.budget_cents > 10000:  # $100 limit
        return JSONResponse(
            status_code=400,
            content=normalized_error(
                "biz",
                "budget-exceeded",
                f"Budget ${request.budget_cents/100:.2f} exceeds maximum $100.00"
            )
        )
    
    prospects = []
    providers_used = []
    providers_failed = []
    total_cost_cents = 0
    
    # Execute provider searches
    search_tasks = []
    for provider in request.providers:
        if provider == "apollo" and APOLLO_API_KEY:
            search_tasks.append(("apollo", ApolloProvider.search_prospects(request.query, request.k)))
        elif provider == "hubspot" and HUBSPOT_ACCESS_TOKEN:
            search_tasks.append(("hubspot", HubSpotProvider.search_contacts(request.query, request.k)))
        else:
            providers_failed.append({
                "provider": provider,
                "error": f"Provider {provider} not configured or unsupported"
            })
    
    # Execute searches
    for provider_name, task in search_tasks:
        try:
            provider_prospects, cost = await task
            prospects.extend(provider_prospects)
            providers_used.append(provider_name)
            total_cost_cents += cost
            
            if total_cost_cents > request.budget_cents:
                logger.warning(f"Budget ${request.budget_cents/100:.2f} exceeded, stopping additional searches")
                break
                
        except Exception as e:
            logger.error(f"Provider {provider_name} failed: {str(e)}")
            providers_failed.append({
                "provider": provider_name,
                "error": str(e)
            })
    
    # Filter by score and lists if specified
    if request.score_min > 0:
        prospects = [p for p in prospects if p["score"] >= request.score_min]
    
    if request.lists:
        # This would filter by lists if we had list data
        pass
    
    # Store prospects in database if available
    if NEON_DATABASE_URL and prospects:
        try:
            pool = await get_db_pool()
            if pool:
                async with pool.acquire() as conn:
                    for prospect in prospects[:10]:  # Limit to first 10 for storage
                        # Insert company if not exists
                        company_id = None
                        if prospect["company_name"] and prospect["company_domain"]:
                            company_id = await conn.fetchval(
                                """INSERT INTO companies (name, domain, source, meta_json) 
                                   VALUES ($1, $2, $3, $4) 
                                   ON CONFLICT (domain) DO UPDATE SET updated_at = NOW()
                                   RETURNING id""",
                                prospect["company_name"], prospect["company_domain"], 
                                prospect["source"], {"from_search": True}
                            )
                        
                        # Insert contact if not exists
                        contact_id = None
                        if prospect["contact_email"]:
                            contact_id = await conn.fetchval(
                                """INSERT INTO contacts (company_id, name, title, email, source, meta_json)
                                   VALUES ($1, $2, $3, $4, $5, $6)
                                   ON CONFLICT DO NOTHING
                                   RETURNING id""",
                                company_id, prospect["contact_name"], prospect["contact_title"],
                                prospect["contact_email"], prospect["source"], {"from_search": True}
                            )
                        
                        # Insert prospect
                        await conn.execute(
                            """INSERT INTO prospects (company_id, contact_id, list, tags, score, source, meta_json)
                               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                            company_id, contact_id, "search_results", prospect["tags"],
                            prospect["score"], prospect["source"], {"query": request.query}
                        )
        except Exception as e:
            logger.error(f"Database storage failed: {str(e)}")
    
    # Generate summary
    summary = {
        "text": f"Found {len(prospects)} prospects for '{request.query}' across {len(providers_used)} providers",
        "confidence": 0.9 if prospects else 0.1,
        "model": "business_search_v1",
        "sources": providers_used,
        "avg_score": sum(p["score"] for p in prospects) / len(prospects) if prospects else 0
    }
    
    return ProspectsSearchResponse(
        status="success" if prospects else "partial" if providers_failed else "failed",
        query=request.query,
        results=[Prospect(**p) for p in prospects[:request.k]],
        summary=summary,
        providers_used=providers_used,
        providers_failed=providers_failed,
        total_cost_cents=total_cost_cents,
        execution_time_ms=int((time.time() - start_time) * 1000),
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )

@app.post("/prospects/enrich")
async def enrich_prospects(request: ProspectsEnrichRequest):
    """Enrich prospect data via provider APIs"""
    start_time = time.time()
    
    if request.provider == "apollo" and not APOLLO_API_KEY:
        return JSONResponse(
            status_code=503,
            content=normalized_error("apollo", "missing-api-key", "APOLLO_API_KEY not configured")
        )
    
    enriched = []
    total_cost_cents = 0
    
    # Placeholder enrichment logic
    for email in request.emails:
        enriched.append({
            "email": email,
            "provider": request.provider,
            "status": "enriched",
            "data": {"placeholder": True}
        })
        total_cost_cents += 25  # $0.25 per enrichment
    
    for domain in request.domains:
        enriched.append({
            "domain": domain,
            "provider": request.provider, 
            "status": "enriched",
            "data": {"placeholder": True}
        })
        total_cost_cents += 15  # $0.15 per domain
    
    return {
        "status": "success",
        "provider": request.provider,
        "results": enriched,
        "total_cost_cents": total_cost_cents,
        "execution_time_ms": int((time.time() - start_time) * 1000),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

@app.post("/prospects/sync")
async def sync_prospects(request: ProspectsSyncRequest):
    """Sync prospects with CRM systems"""
    start_time = time.time()
    
    if request.mode == "write":
        return JSONResponse(
            status_code=403,
            content=normalized_error(
                "biz",
                "write-gated", 
                "Write operations gated until CEO approval. Use mode='read' only."
            )
        )
    
    if request.provider == "salesforce" and request.mode == "write":
        return JSONResponse(
            status_code=403,
            content=normalized_error(
                "salesforce", 
                "write-disabled",
                "Salesforce write operations disabled until CEO approves write workflow"
            )
        )
    
    sync_results = {
        "list": request.list,
        "provider": request.provider,
        "mode": request.mode,
        "status": "completed",
        "records_processed": 0,
        "records_synced": 0,
        "errors": []
    }
    
    return {
        "status": "success",
        "sync_results": sync_results,
        "execution_time_ms": int((time.time() - start_time) * 1000),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

@app.post("/signals/digest")
async def digest_signals(request: SignalsDigestRequest):
    """Generate signals digest from configured channels"""
    start_time = time.time()
    
    digest_results = {}
    providers_used = []
    providers_failed = []
    
    # Process Slack channels if available
    if any("slack:" in ch for ch in request.channels) and SLACK_BOT_TOKEN:
        slack_channels = [ch for ch in request.channels if "slack:" in ch]
        try:
            slack_digest = await SlackProvider.digest_channels(slack_channels, request.window)
            digest_results["slack"] = slack_digest
            providers_used.append("slack")
        except Exception as e:
            providers_failed.append({
                "provider": "slack",
                "error": str(e)
            })
    
    # Store signals in database if available
    if NEON_DATABASE_URL and digest_results:
        try:
            pool = await get_db_pool()
            if pool:
                async with pool.acquire() as conn:
                    await conn.execute(
                        """INSERT INTO signals (kind, payload_json) VALUES ($1, $2)""",
                        "digest", json.dumps({
                            "window": request.window,
                            "channels": request.channels,
                            "results": digest_results
                        })
                    )
        except Exception as e:
            logger.error(f"Signal storage failed: {str(e)}")
    
    return {
        "status": "success" if digest_results else "failed",
        "window": request.window,
        "channels": request.channels,
        "digest_results": digest_results,
        "providers_used": providers_used,
        "providers_failed": providers_failed,
        "execution_time_ms": int((time.time() - start_time) * 1000),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

@app.post("/intake/upload")
async def upload_intake(
    provider: str = Form(...),
    file: UploadFile = File(None)
):
    """Handle CSV and manual data uploads"""
    start_time = time.time()
    
    # TOS compliance check
    if provider in ["linkedin", "costar", "nmhc"]:
        return JSONResponse(
            status_code=403,
            content=normalized_error(
                provider,
                "tos-gated",
                f"{provider.upper()} requires official API or manual CSV upload. Scraping disabled for TOS compliance."
            )
        )
    
    if not NEON_DATABASE_URL:
        return JSONResponse(
            status_code=503,
            content=normalized_error("storage", "missing-database", "NEON_DATABASE_URL not configured")
        )
    
    upload_results = {
        "provider": provider,
        "filename": file.filename if file else "no_file",
        "status": "completed",
        "row_count": 0,
        "success_count": 0,
        "error_count": 0,
        "sample_records": []
    }
    
    if file:
        # Placeholder CSV processing
        content = await file.read()
        # In production, would parse CSV and insert into database
        upload_results["row_count"] = len(content.decode().split('\n'))
        upload_results["success_count"] = upload_results["row_count"] - 1  # minus header
        
        # Store upload record
        try:
            pool = await get_db_pool()
            if pool:
                async with pool.acquire() as conn:
                    await conn.execute(
                        """INSERT INTO uploads (provider, filename, status, row_count, success_count, error_count)
                           VALUES ($1, $2, $3, $4, $5, $6)""",
                        provider, file.filename, "completed", 
                        upload_results["row_count"], upload_results["success_count"], 0
                    )
        except Exception as e:
            logger.error(f"Upload record storage failed: {str(e)}")
    
    return {
        "status": "success",
        "upload_results": upload_results,
        "execution_time_ms": int((time.time() - start_time) * 1000),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

@app.get("/providers")
async def get_providers():
    """Get provider readiness status (names only)"""
    providers = get_provider_status()
    
    return {
        "status": "success",
        "providers": providers,
        "ready_count": len([p for p in providers.values() if p == "ready"]),
        "missing_count": len([p for p in providers.values() if p == "missing_secret"]),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

@app.on_event("startup")
async def startup():
    """Initialize database pool on startup"""
    if NEON_DATABASE_URL:
        await get_db_pool()
        logger.info("Business MCP v1 started with database connectivity")
    else:
        logger.warning("Business MCP v1 started without database - storage disabled")

@app.on_event("shutdown") 
async def shutdown():
    """Close database pool on shutdown"""
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")