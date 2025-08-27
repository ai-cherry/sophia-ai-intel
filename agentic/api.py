from fastapi import FastAPI
from agentic.research_swarms.schemas import ResearchRequest, ResearchResponse
from agentic.research_swarms.trend_swarm import run_research_swarm
from agentic.business_swarms.schemas import BusinessIntelligenceRequest, BusinessIntelligenceResponse
from agentic.business_swarms.market_swarm import run_business_intelligence_swarm
from agentic.process_orchestration.schemas import ProcessOrchestrationRequest, ProcessOrchestrationResponse
from agentic.process_orchestration.main import process_orchestration_entrypoint
from agentic.coding_swarms.schemas import CodingTaskRequest, CodingTaskResponse
from agentic.coding_swarms.dev_swarm import run_coding_swarm

app = FastAPI()

@app.post("/agentic/process_orchestration", response_model=ProcessOrchestrationResponse)
async def process_orchestration_endpoint(request: ProcessOrchestrationRequest):
    """
    API endpoint to trigger the process orchestration swarm.
    """
    return await process_orchestration_entrypoint(request)

@app.post("/agentic/research", response_model=ResearchResponse)
async def research_endpoint(request: ResearchRequest):
    """
    API endpoint to trigger the deep-research scraping swarm.
    """
    return await run_research_swarm(request)

@app.post("/agentic/business_intelligence", response_model=BusinessIntelligenceResponse)
async def business_intelligence_endpoint(request: BusinessIntelligenceRequest):
    """
    API endpoint to trigger the business intelligence swarm.
    """
    return await run_business_intelligence_swarm(request)

@app.post("/agentic/coding", response_model=CodingTaskResponse)
async def invoke_dev_swarm(request: CodingTaskRequest):
    """
    API endpoint to trigger the coding swarm.
    """
    return run_coding_swarm(request)
