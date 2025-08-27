import pytest
from agentic.api import ResearchRequest, ResearchResponse
from agentic.research_swarms.trend_swarm import run_research_swarm

def test_run_research_swarm():
    """
    Tests that the run_research_swarm function returns a valid ResearchResponse.
    """
    # 1. Create a mock research task
    mock_task = ResearchRequest(query="Test query")

    # 2. Run the research swarm
    response = run_research_swarm(mock_task)

    # 3. Assert that the response is a valid ResearchResponse
    assert isinstance(response, ResearchResponse)
    assert isinstance(response.report, str)
    assert response.report  # Ensure the report is not empty