from typing import List, Optional

from pydantic import BaseModel


class ResearchRequest(BaseModel):
    """
    Represents a request to initiate a research task.
    """
    topic: str
    research_depth: Optional[str] = "surface"
    output_format: Optional[str] = "markdown"


class ResearchResponse(BaseModel):
    """
    Represents the response from a research task.
    """
    success: bool
    report_content: str
    sources: List[str]
    synthesis: str