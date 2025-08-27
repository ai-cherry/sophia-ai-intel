from pydantic import BaseModel, Field
from typing import List, Dict

class BusinessIntelligenceRequest(BaseModel):
    """
    Represents a request for business intelligence analysis.
    """
    query: str = Field(..., description="The business question to be answered.")
    data_sources: List[str] = Field(..., description="A list of data sources to use for the analysis (e.g., 'yfinance', 'news_headlines').")
    analysis_type: str = Field(..., description="The type of analysis to perform (e.g., 'risk_assessment', 'sentiment_analysis').")

class BusinessIntelligenceResponse(BaseModel):
    """
    Represents the response from a business intelligence analysis.
    """
    success: bool = Field(..., description="Indicates whether the analysis was successful.")
    analysis_summary: str = Field(..., description="A summary of the analysis findings.")
    data_points: List[Dict] = Field(..., description="A list of relevant data points supporting the analysis.")
    confidence_score: float = Field(..., ge=0, le=1, description="The confidence score of the analysis, between 0 and 1.")