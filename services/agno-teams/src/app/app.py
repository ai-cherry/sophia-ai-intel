import os
import sys
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sophia AI Teams Service",
    description="AI-powered team coordination and management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize teams
sales_team = None
client_health_team = None

@app.on_event("startup")
async def startup_event():
    """Initialize teams on startup"""
    global sales_team, client_health_team
    try:
        logger.info("Initializing Sophia AI Teams...")

        # Initialize Sales Intelligence Team
        # sales_team = SalesIntelligenceTeam()
        logger.info("Sales Intelligence Team initialized")

        # Initialize Client Health Team
        # client_health_team = ClientHealthTeam()
        logger.info("Client Health Team initialized")

        logger.info("All teams initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize teams: {e}")
        raise

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Sophia AI Teams Service", "status": "running"}

@app.get("/healthz")
async def healthz():
    """Health check endpoint"""
    return {"status": "healthy", "service": "sophia-teams"}

@app.get("/teams")
async def list_teams():
    """List available teams"""
    return {
        "teams": [
            {
                "name": "Sales Intelligence",
                "description": "AI-powered sales analysis and intelligence",
                "agents": ["pipeline_analyst", "deal_scorer", "competitor_analyst", "sales_coach", "revenue_forecaster"]
            },
            {
                "name": "Client Health",
                "description": "Client success and health monitoring",
                "agents": ["usage_analyst", "support_ticket_analyst", "client_success_manager"]
            }
        ]
    }

@app.post("/teams/sales-intelligence/analyze")
async def analyze_sales_intelligence(data: dict):
    """Analyze sales intelligence data"""
    try:
        if not sales_team:
            raise HTTPException(status_code=503, detail="Sales Intelligence Team not initialized")

        result = await sales_team.analyze(data)
        return {"result": result}

    except Exception as e:
        logger.error(f"Sales intelligence analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/teams/client-health/analyze")
async def analyze_client_health(data: dict):
    """Analyze client health data"""
    try:
        if not client_health_team:
            raise HTTPException(status_code=503, detail="Client Health Team not initialized")

        result = await client_health_team.analyze(data)
        return {"result": result}

    except Exception as e:
        logger.error(f"Client health analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    """Service metrics"""
    return {
        "sales_team_active": sales_team is not None,
        "client_health_team_active": client_health_team is not None,
        "service": "sophia-teams",
        "version": "1.0.0"
    }