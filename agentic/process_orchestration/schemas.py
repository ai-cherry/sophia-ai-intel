from typing import List
from pydantic import BaseModel

class ProcessOrchestrationRequest(BaseModel):
    """
    Represents a request to the process orchestrator.
    """
    github_pr_url: str
    event_type: str

class ProcessOrchestrationResponse(BaseModel):
    """
    Represents a response from the process orchestrator.
    """
    success: bool
    impact_analysis: str
    deployment_suggestions: List[str]
    release_notes: str