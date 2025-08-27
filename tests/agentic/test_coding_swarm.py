import pytest
from agentic.api import CodingTaskRequest, CodingTaskResponse
from agentic.coding_swarms.dev_swarm import run_coding_swarm

def test_run_coding_swarm():
    """
    Tests that the run_coding_swarm function returns a valid response.
    """
    # Create a mock task request
    mock_task = CodingTaskRequest(
        task_description="Implement a new feature.",
        context={"repo_url": "https://github.com/example/repo"}
    )

    # Call the function
    response = run_coding_swarm(mock_task)

    # Assert that the response is valid
    assert isinstance(response, CodingTaskResponse)
    assert isinstance(response.patches, list)
    assert isinstance(response.commit_message, str)
    assert response.commit_message == "Initial implementation of the coding swarm."