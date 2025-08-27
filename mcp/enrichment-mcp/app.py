"""
Enrichment MCP Service - FastAPI service for data enrichment integrations
Handles UserGems, Apollo, SalesNavigator, Phantombuster, CoStar integrations
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import HTTPException, Request, Response, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import httpx
import json

# Try to import from platform.common, fall back to local if not available
try:
    from platform.common.service_base import create_app
except ImportError:
    # Fallback for development without platform package
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from platform.common.service_base import create_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY", "")
USERGEMS_API_KEY = os.getenv("USERGEMS_API_KEY", "")
USERGEMS_BASE_URL = os.getenv("USERGEMS_BASE_URL", "https://api.usergems.com")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")
APOLLO_BASE_URL = os.getenv("APOLLO_BASE_URL", "https://api.apollo.io/v1")
SALESNAV_ACCESS_TOKEN = os.getenv("SALESNAV_ACCESS_TOKEN", "")
SALESNAV_API_URL = os.getenv("SALESNAV_API_URL", "https://api.linkedin.com/v2")
PHANTOMBUSTER_API_KEY = os.getenv("PHANTOMBUSTER_API_KEY", "")
PHANTOMBUSTER_BASE_URL = os.getenv("PHANTOMBUSTER_BASE_URL", "https://api.phantombuster.com/api/v2")
COSTAR_API_KEY = os.getenv("COSTAR_API_KEY", "")
COSTAR_BASE_URL = os.getenv("COSTAR_BASE_URL", "https://api.costar.com/v1")
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "")  # Generic search API key

SERVICE_NAME = "enrichment-mcp"
SERVICE_VERSION = "1.0.0"

# Startup and shutdown handlers
async def startup_handler():
    """Startup event handler"""
    logger.info(f"Starting {SERVICE_NAME} v{SERVICE_VERSION}")

async def shutdown_handler():
    """Shutdown event handler"""
    logger.info(f"Shutting down {SERVICE_NAME}")

# Initialize FastAPI app using factory
app = create_app(
    name="Enrichment MCP Service",
    desc="MCP service for data enrichment from multiple providers",
    version=SERVICE_VERSION,
    startup_handler=startup_handler,
    shutdown_handler=shutdown_handler
)

# Request/Response models
class PersonEnrichmentRequest(BaseModel):
    """Request model for person enrichment"""
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    providers: List[str] = ["apollo", "usergems"]  # Which providers to use

class CompanyEnrichmentRequest(BaseModel):
    """Request model for company enrichment"""
    domain: Optional[str] = None
    company_name: Optional[str] = None
    linkedin_url: Optional[str] = None
    providers: List[str] = ["apollo", "costar"]

class JobChangeRequest(BaseModel):
    """Request model for job change tracking"""
    company_domains: List[str]
    include_promotions: bool = True
    include_new_hires: bool = True
    date_from: Optional[str] = None  # ISO format date

class LeadScoringRequest(BaseModel):
    """Request model for lead scoring"""
    email: str
    company_domain: Optional[str] = None
    engagement_data: Optional[Dict[str, Any]] = {}

class WebScrapingRequest(BaseModel):
    """Request model for web scraping via Phantombuster"""
    url: str
    scraping_type: str = "profile"  # profile, company, posts
    additional_params: Optional[Dict[str, Any]] = {}

class SearchRequest(BaseModel):
    """Request model for people/company search"""
    search_type: str  # "people" or "company"
    filters: Dict[str, Any]
    limit: int = 25
    offset: int = 0


# Person Enrichment endpoints
@app.post("/api/enrich/person")
async def enrich_person(request: PersonEnrichmentRequest):
    """Enrich person data from multiple providers"""
    enrichment_results = {}
    errors = []
    
    # Apollo enrichment
    if "apollo" in request.providers and APOLLO_API_KEY:
        try:
            apollo_data = await apollo_person_enrichment(
                email=request.email,
                full_name=request.full_name,
                company_name=request.company_name,
                linkedin_url=request.linkedin_url
            )
            enrichment_results["apollo"] = apollo_data
        except Exception as e:
            logger.error(f"Apollo enrichment error: {str(e)}")
            errors.append({"provider": "apollo", "error": str(e)})
    
    # UserGems enrichment
    if "usergems" in request.providers and USERGEMS_API_KEY:
        try:
            usergems_data = await usergems_person_enrichment(
                email=request.email,
                linkedin_url=request.linkedin_url
            )
            enrichment_results["usergems"] = usergems_data
        except Exception as e:
            logger.error(f"UserGems enrichment error: {str(e)}")
            errors.append({"provider": "usergems", "error": str(e)})
    
    # SalesNavigator enrichment
    if "salesnav" in request.providers and SALESNAV_ACCESS_TOKEN:
        try:
            salesnav_data = await salesnav_person_enrichment(
                linkedin_url=request.linkedin_url,
                email=request.email
            )
            enrichment_results["salesnav"] = salesnav_data
        except Exception as e:
            logger.error(f"SalesNavigator enrichment error: {str(e)}")
            errors.append({"provider": "salesnav", "error": str(e)})
    
    # Merge results
    merged_data = merge_person_data(enrichment_results)
    
    return {
        "merged_data": merged_data,
        "raw_results": enrichment_results,
        "errors": errors,
        "timestamp": datetime.utcnow().isoformat()
    }

async def apollo_person_enrichment(
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    company_name: Optional[str] = None,
    linkedin_url: Optional[str] = None
) -> Dict[str, Any]:
    """Enrich person data using Apollo API"""
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": APOLLO_API_KEY
    }
    
    data = {}
    if email:
        data["email"] = email
    if full_name:
        data["name"] = full_name
    if company_name:
        data["organization_name"] = company_name
    if linkedin_url:
        data["linkedin_url"] = linkedin_url
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{APOLLO_BASE_URL}/people/match",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

async def usergems_person_enrichment(
    email: Optional[str] = None,
    linkedin_url: Optional[str] = None
) -> Dict[str, Any]:
    """Enrich person data using UserGems API"""
    headers = {
        "Authorization": f"Bearer {USERGEMS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {}
    if email:
        data["email"] = email
    if linkedin_url:
        data["linkedin_url"] = linkedin_url
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{USERGEMS_BASE_URL}/api/v1/person/enrich",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

async def salesnav_person_enrichment(
    linkedin_url: Optional[str] = None,
    email: Optional[str] = None
) -> Dict[str, Any]:
    """Enrich person data using SalesNavigator API"""
    headers = {
        "Authorization": f"Bearer {SALESNAV_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Extract LinkedIn ID from URL if provided
    linkedin_id = None
    if linkedin_url:
        # Parse LinkedIn URL to get the profile ID
        parts = linkedin_url.split("/")
        if "linkedin.com/in/" in linkedin_url:
            linkedin_id = parts[-1].strip("/")
    
    params = {}
    if linkedin_id:
        params["id"] = linkedin_id
    elif email:
        params["email"] = email
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SALESNAV_API_URL}/people",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return response.json()

def merge_person_data(results: Dict[str, Any]) -> Dict[str, Any]:
    """Merge person data from multiple sources"""
    merged = {
        "email": None,
        "full_name": None,
        "title": None,
        "company": None,
        "linkedin_url": None,
        "phone": None,
        "location": None,
        "seniority": None,
        "department": None,
        "confidence_score": 0
    }
    
    # Priority order: Apollo > UserGems > SalesNavigator
    for provider in ["apollo", "usergems", "salesnav"]:
        if provider not in results:
            continue
        
        data = results[provider]
        
        # Map provider-specific fields to standard fields
        if provider == "apollo" and data.get("person"):
            person = data["person"]
            merged["email"] = merged["email"] or person.get("email")
            merged["full_name"] = merged["full_name"] or person.get("name")
            merged["title"] = merged["title"] or person.get("title")
            merged["company"] = merged["company"] or person.get("organization", {}).get("name")
            merged["linkedin_url"] = merged["linkedin_url"] or person.get("linkedin_url")
            merged["phone"] = merged["phone"] or person.get("phone_numbers", [{}])[0].get("raw_number")
            merged["location"] = merged["location"] or person.get("city")
            merged["seniority"] = merged["seniority"] or person.get("seniority")
            merged["department"] = merged["department"] or person.get("departments", [None])[0]
        
        elif provider == "usergems":
            merged["email"] = merged["email"] or data.get("email")
            merged["full_name"] = merged["full_name"] or data.get("name")
            merged["title"] = merged["title"] or data.get("job_title")
            merged["company"] = merged["company"] or data.get("company")
            merged["linkedin_url"] = merged["linkedin_url"] or data.get("linkedin_url")
            
        elif provider == "salesnav":
            merged["full_name"] = merged["full_name"] or data.get("firstName", "") + " " + data.get("lastName", "")
            merged["title"] = merged["title"] or data.get("headline")
    
    # Calculate confidence score based on data completeness
    filled_fields = sum(1 for v in merged.values() if v is not None and v != 0)
    merged["confidence_score"] = filled_fields / len(merged) * 100
    
    return merged

# Company Enrichment endpoints
@app.post("/api/enrich/company")
async def enrich_company(request: CompanyEnrichmentRequest):
    """Enrich company data from multiple providers"""
    enrichment_results = {}
    errors = []
    
    # Apollo enrichment
    if "apollo" in request.providers and APOLLO_API_KEY:
        try:
            apollo_data = await apollo_company_enrichment(
                domain=request.domain,
                company_name=request.company_name
            )
            enrichment_results["apollo"] = apollo_data
        except Exception as e:
            logger.error(f"Apollo company enrichment error: {str(e)}")
            errors.append({"provider": "apollo", "error": str(e)})
    
    # CoStar enrichment
    if "costar" in request.providers and COSTAR_API_KEY:
        try:
            costar_data = await costar_company_enrichment(
                company_name=request.company_name,
                domain=request.domain
            )
            enrichment_results["costar"] = costar_data
        except Exception as e:
            logger.error(f"CoStar enrichment error: {str(e)}")
            errors.append({"provider": "costar", "error": str(e)})
    
    # Merge results
    merged_data = merge_company_data(enrichment_results)
    
    return {
        "merged_data": merged_data,
        "raw_results": enrichment_results,
        "errors": errors,
        "timestamp": datetime.utcnow().isoformat()
    }

async def apollo_company_enrichment(
    domain: Optional[str] = None,
    company_name: Optional[str] = None
) -> Dict[str, Any]:
    """Enrich company data using Apollo API"""
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": APOLLO_API_KEY
    }
    
    data = {}
    if domain:
        data["domain"] = domain
    if company_name:
        data["name"] = company_name
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{APOLLO_BASE_URL}/organizations/enrich",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

async def costar_company_enrichment(
    company_name: Optional[str] = None,
    domain: Optional[str] = None
) -> Dict[str, Any]:
    """Enrich company data using CoStar API"""
    headers = {
        "Authorization": f"Bearer {COSTAR_API_KEY}",
        "Content-Type": "application/json"
    }
    
    params = {}
    if company_name:
        params["name"] = company_name
    if domain:
        params["website"] = domain
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{COSTAR_BASE_URL}/companies/search",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return response.json()

def merge_company_data(results: Dict[str, Any]) -> Dict[str, Any]:
    """Merge company data from multiple sources"""
    merged = {
        "name": None,
        "domain": None,
        "industry": None,
        "employee_count": None,
        "revenue": None,
        "headquarters": None,
        "founded_year": None,
        "description": None,
        "linkedin_url": None,
        "technologies": [],
        "confidence_score": 0
    }
    
    # Priority order: Apollo > CoStar
    for provider in ["apollo", "costar"]:
        if provider not in results:
            continue
        
        data = results[provider]
        
        if provider == "apollo" and data.get("organization"):
            org = data["organization"]
            merged["name"] = merged["name"] or org.get("name")
            merged["domain"] = merged["domain"] or org.get("primary_domain")
            merged["industry"] = merged["industry"] or org.get("industry")
            merged["employee_count"] = merged["employee_count"] or org.get("estimated_num_employees")
            merged["revenue"] = merged["revenue"] or org.get("annual_revenue")
            merged["headquarters"] = merged["headquarters"] or org.get("headquarters_location")
            merged["founded_year"] = merged["founded_year"] or org.get("founded_year")
            merged["description"] = merged["description"] or org.get("short_description")
            merged["linkedin_url"] = merged["linkedin_url"] or org.get("linkedin_url")
            merged["technologies"] = merged["technologies"] or org.get("technologies", [])
        
        elif provider == "costar" and data.get("companies"):
            if len(data["companies"]) > 0:
                company = data["companies"][0]
                merged["name"] = merged["name"] or company.get("name")
                merged["industry"] = merged["industry"] or company.get("industry")
                merged["employee_count"] = merged["employee_count"] or company.get("employees")
                merged["revenue"] = merged["revenue"] or company.get("revenue")
                merged["headquarters"] = merged["headquarters"] or company.get("address")
    
    # Calculate confidence score
    filled_fields = sum(1 for v in merged.values() if v and (v != [] if isinstance(v, list) else True))
    merged["confidence_score"] = filled_fields / len(merged) * 100
    
    return merged

# Job Change Tracking endpoints
@app.post("/api/jobchanges/track")
async def track_job_changes(request: JobChangeRequest):
    """Track job changes for target companies using UserGems"""
    if not USERGEMS_API_KEY:
        raise HTTPException(status_code=503, detail="UserGems integration not configured")
    
    headers = {
        "Authorization": f"Bearer {USERGEMS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "company_domains": request.company_domains,
        "include_promotions": request.include_promotions,
        "include_new_hires": request.include_new_hires
    }
    
    if request.date_from:
        data["date_from"] = request.date_from
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{USERGEMS_BASE_URL}/api/v1/job-changes",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        
        job_changes = response.json()
        
        # Process and categorize job changes
        categorized = {
            "promotions": [],
            "new_hires": [],
            "job_changes": [],
            "total": 0
        }
        
        for change in job_changes.get("changes", []):
            categorized["total"] += 1
            
            if change.get("type") == "promotion":
                categorized["promotions"].append(change)
            elif change.get("type") == "new_hire":
                categorized["new_hires"].append(change)
            else:
                categorized["job_changes"].append(change)
        
        return {
            "categorized_changes": categorized,
            "raw_data": job_changes,
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/api/jobchanges/alerts")
async def get_job_change_alerts(days: int = 7):
    """Get recent job change alerts"""
    if not USERGEMS_API_KEY:
        raise HTTPException(status_code=503, detail="UserGems integration not configured")
    
    headers = {
        "Authorization": f"Bearer {USERGEMS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    date_from = datetime.utcnow().replace(microsecond=0) - timedelta(days=days)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{USERGEMS_BASE_URL}/api/v1/alerts",
            headers=headers,
            params={"date_from": date_from.isoformat()}
        )
        response.raise_for_status()
        return response.json()

# Web Scraping endpoints
@app.post("/api/scrape")
async def scrape_web_data(request: WebScrapingRequest):
    """Scrape web data using Phantombuster"""
    if not PHANTOMBUSTER_API_KEY:
        raise HTTPException(status_code=503, detail="Phantombuster integration not configured")
    
    headers = {
        "X-Phantombuster-Key": PHANTOMBUSTER_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Select appropriate Phantombuster agent based on scraping type
    agent_id = get_phantombuster_agent(request.scraping_type)
    
    data = {
        "agentId": agent_id,
        "argument": {
            "urls": [request.url],
            **request.additional_params
        }
    }
    
    async with httpx.AsyncClient() as client:
        # Launch the agent
        response = await client.post(
            f"{PHANTOMBUSTER_BASE_URL}/agents/launch",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        
        container_id = response.json().get("containerId")
        
        # Wait for results (simplified - in production, use webhooks)
        await asyncio.sleep(10)
        
        # Fetch results
        response = await client.get(
            f"{PHANTOMBUSTER_BASE_URL}/containers/{container_id}/output",
            headers=headers
        )
        response.raise_for_status()
        
        return {
            "container_id": container_id,
            "results": response.json(),
            "timestamp": datetime.utcnow().isoformat()
        }

def get_phantombuster_agent(scraping_type: str) -> str:
    """Get Phantombuster agent ID based on scraping type"""
    agents = {
        "profile": "linkedin-profile-scraper",
        "company": "linkedin-company-scraper",
        "posts": "linkedin-posts-scraper",
        "sales_nav": "sales-navigator-scraper"
    }
    return agents.get(scraping_type, "generic-web-scraper")

# Search endpoints
@app.post("/api/search")
async def search_entities(request: SearchRequest):
    """Search for people or companies"""
    if request.search_type == "people":
        return await search_people(request.filters, request.limit, request.offset)
    elif request.search_type == "company":
        return await search_companies(request.filters, request.limit, request.offset)
    else:
        raise HTTPException(status_code=400, detail="Invalid search_type")

async def search_people(filters: Dict[str, Any], limit: int, offset: int) -> Dict[str, Any]:
    """Search for people using Apollo API"""
    if not APOLLO_API_KEY:
        raise HTTPException(status_code=503, detail="Apollo integration not configured")
    
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": APOLLO_API_KEY
    }
    
    data = {
        "per_page": limit,
        "page": (offset // limit) + 1
    }
    
    # Map filters to Apollo parameters
    if "title" in filters:
        data["titles"] = [filters["title"]]
    if "company" in filters:
        data["organization_names"] = [filters["company"]]
    if "location" in filters:
        data["locations"] = [filters["location"]]
    if "seniority" in filters:
        data["seniorities"] = [filters["seniority"]]
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{APOLLO_BASE_URL}/mixed_people/search",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

async def search_companies(filters: Dict[str, Any], limit: int, offset: int) -> Dict[str, Any]:
    """Search for companies using Apollo API"""
    if not APOLLO_API_KEY:
        raise HTTPException(status_code=503, detail="Apollo integration not configured")
    
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": APOLLO_API_KEY
    }
    
    data = {
        "per_page": limit,
        "page": (offset // limit) + 1
    }
    
    # Map filters to Apollo parameters
    if "industry" in filters:
        data["industries"] = [filters["industry"]]
    if "employee_count_min" in filters:
        data["num_employees_min"] = filters["employee_count_min"]
    if "employee_count_max" in filters:
        data["num_employees_max"] = filters["employee_count_max"]
    if "revenue_min" in filters:
        data["revenue_min"] = filters["revenue_min"]
    if "technologies" in filters:
        data["technologies"] = filters["technologies"]
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{APOLLO_BASE_URL}/mixed_companies/search",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

# Lead Scoring endpoint
@app.post("/api/score/lead")
async def score_lead(request: LeadScoringRequest):
    """Score a lead based on enrichment data and engagement"""
    # Enrich the person first
    person_enrichment = await enrich_person(
        PersonEnrichmentRequest(
            email=request.email,
            providers=["apollo", "usergems"]
        )
    )
    
    # Enrich the company if domain provided
    company_enrichment = None
    if request.company_domain:
        company_enrichment = await enrich_company(
            CompanyEnrichmentRequest(
                domain=request.company_domain,
                providers=["apollo"]
            )
        )
    
    # Calculate lead score
    score = calculate_lead_score(
        person_enrichment.get("merged_data", {}),
        company_enrichment.get("merged_data", {}) if company_enrichment else {},
        request.engagement_data
    )
    
    return {
        "email": request.email,
        "score": score["total_score"],
        "score_breakdown": score["breakdown"],
        "recommendations": score["recommendations"],
        "person_data": person_enrichment.get("merged_data"),
        "company_data": company_enrichment.get("merged_data") if company_enrichment else None,
        "timestamp": datetime.utcnow().isoformat()
    }

def calculate_lead_score(
    person_data: Dict[str, Any],
    company_data: Dict[str, Any],
    engagement_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate lead score based on multiple factors"""
    score_breakdown = {
        "title_score": 0,
        "seniority_score": 0,
        "company_score": 0,
        "engagement_score": 0,
        "data_completeness_score": 0
    }
    
    recommendations = []
    
    # Title scoring (0-25 points)
    title = person_data.get("title", "").lower()
    if any(keyword in title for keyword in ["ceo", "cto", "vp", "president", "director"]):
        score_breakdown["title_score"] = 25
    elif any(keyword in title for keyword in ["manager", "head", "lead"]):
        score_breakdown["title_score"] = 15
    else:
        score_breakdown["title_score"] = 5
    
    # Seniority scoring (0-20 points)
    seniority = person_data.get("seniority", "").lower()
    seniority_scores = {
        "executive": 20,
        "vp": 18,
        "director": 15,
        "manager": 10,
        "senior": 8,
        "entry": 3
    }
    score_breakdown["seniority_score"] = seniority_scores.get(seniority, 5)
    
    # Company scoring (0-30 points)
    if company_data:
        employee_count = company_data.get("employee_count", 0)
        if employee_count > 1000:
            score_breakdown["company_score"] += 15
        elif employee_count > 100:
            score_breakdown["company_score"] += 10
        else:
            score_breakdown["company_score"] += 5
        
        # Add points for revenue
        revenue = company_data.get("revenue", 0)
        if revenue > 100000000:  # $100M+
            score_breakdown["company_score"] += 15
        elif revenue > 10000000:  # $10M+
            score_breakdown["company_score"] += 10
        else:
            score_breakdown["company_score"] += 5
    
    # Engagement scoring (0-15 points)
    if engagement_data:
        email_opens = engagement_data.get("email_opens", 0)
        website_visits = engagement_data.get("website_visits", 0)
        content_downloads = engagement_data.get("content_downloads", 0)
        
        score_breakdown["engagement_score"] = min(15, 
            (email_opens * 2) + (website_visits * 3) + (content_downloads * 5)
        )
    
    # Data completeness (0-10 points)
    completeness = person_data.get("confidence_score", 0) / 10
    score_breakdown["data_completeness_score"] = min(10, completeness)
    
    # Calculate total score
    total_score = sum(score_breakdown.values())
    
    # Generate recommendations
    if total_score >= 75:
        recommendations.append("High priority lead - immediate outreach recommended")
    elif total_score >= 50:
        recommendations.append("Qualified lead - add to nurture campaign")
    else:
        recommendations.append("Low priority - continue monitoring")
    
    if score_breakdown["engagement_score"] < 5:
        recommendations.append("Low engagement - consider warming campaign")
    
    if score_breakdown["data_completeness_score"] < 5:
        recommendations.append("Incomplete data - additional enrichment recommended")
    
    return {
        "total_score": total_score,
        "breakdown": score_breakdown,
        "recommendations": recommendations
    }

# Bulk operations endpoints
@app.post("/api/bulk/enrich")
async def bulk_enrichment(
    enrichment_type: str,
    items: List[Dict[str, Any]],
    providers: List[str] = ["apollo"]
):
    """Bulk enrichment for people or companies"""
    results = []
    errors = []
    
    for item in items[:100]:  # Limit to 100 items per request
        try:
            if enrichment_type == "person":
                request = PersonEnrichmentRequest(**item, providers=providers)
                result = await enrich_person(request)
            elif enrichment_type == "company":
                request = CompanyEnrichmentRequest(**item, providers=providers)
                result = await enrich_company(request)
            else:
                raise ValueError(f"Invalid enrichment_type: {enrichment_type}")
            
            results.append(result)
        except Exception as e:
            errors.append({"item": item, "error": str(e)})
    
    return {
        "success_count": len(results),
        "error_count": len(errors),
        "results": results,
        "errors": errors,
        "timestamp": datetime.utcnow().isoformat()
    }

# Analytics endpoints
@app.get("/api/analytics/enrichment-stats")
async def get_enrichment_stats(days: int = 30):
    """Get enrichment usage statistics"""
    # This would typically query a database for actual stats
    # For now, returning sample data
    return {
        "period_days": days,
        "total_enrichments": 1250,
        "by_provider": {
            "apollo": 650,
            "usergems": 350,
            "salesnav": 150,
            "costar": 100
        },
        "by_type": {
            "person": 850,
            "company": 400
        },
        "average_confidence_score": 78.5,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/analytics/provider-health")
async def get_provider_health():
    """Check health status of all enrichment providers"""
    provider_status = {}
    
    # Check Apollo
    if APOLLO_API_KEY:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{APOLLO_BASE_URL}/auth/health",
                    headers={"X-Api-Key": APOLLO_API_KEY},
                    timeout=5
                )
                provider_status["apollo"] = "healthy" if response.status_code == 200 else "degraded"
        except:
            provider_status["apollo"] = "unhealthy"
    else:
        provider_status["apollo"] = "not_configured"
    
    # Check UserGems
    if USERGEMS_API_KEY:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{USERGEMS_BASE_URL}/health",
                    headers={"Authorization": f"Bearer {USERGEMS_API_KEY}"},
                    timeout=5
                )
                provider_status["usergems"] = "healthy" if response.status_code == 200 else "degraded"
        except:
            provider_status["usergems"] = "unhealthy"
    else:
        provider_status["usergems"] = "not_configured"
    
    # Similar checks for other providers
    provider_status["salesnav"] = "healthy" if SALESNAV_ACCESS_TOKEN else "not_configured"
    provider_status["phantombuster"] = "healthy" if PHANTOMBUSTER_API_KEY else "not_configured"
    provider_status["costar"] = "healthy" if COSTAR_API_KEY else "not_configured"
    
    return {
        "providers": provider_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# Import required for async operations
import asyncio
from datetime import timedelta

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)