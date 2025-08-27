import os
import redis
from agno.client import AgnoClient
from agno.tools.core import Generalist, CodeWriter, Tool, tool
from agentic.coding_swarms.schemas import CodingTaskRequest, CodingTaskResponse

# Initialize AgnoClient
agno_client = AgnoClient()

# Define the agents
CodeArchitect = agno_client.agent(
    "CodeArchitect",
    "The master agent responsible for orchestrating the other agents.",
)

MicroserviceSpecialist = agno_client.agent(
    "MicroserviceSpecialist",
    "Specializes in working with microservices in the `services/` directory.",
)

FrontendVirtuoso = agno_client.agent(
    "FrontendVirtuoso", "Specializes in frontend code in the `apps/` directory."
)

BackendGuru = agno_client.agent(
    "BackendGuru",
    "Specializes in backend logic in the `platform/` and `libs/` directories.",
)

SecuritySentinel = agno_client.agent(
    "SecuritySentinel",
    "Responsible for auditing the code for security vulnerabilities.",
)

def run_coding_swarm(task: CodingTaskRequest) -> CodingTaskResponse:
    """
    This function instantiates and runs the coding swarm to complete the given task.
    """
    # 1. Connect to Redis for context persistence
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url, decode_responses=True)

    # 2. Instantiate the CodeArchitect and assign the team
    architect = CodeArchitect(
        tools=[CodeWriter],
        team=[
            MicroserviceSpecialist(tools=[CodeWriter]),
            FrontendVirtuoso(tools=[CodeWriter]),
            BackendGuru(tools=[CodeWriter]),
            SecuritySentinel(tools=[CodeWriter]),
        ],
        session_id=task.session_id, # Use session_id for persistent memory
        redis_client=redis_client,
    )

    # 3. Break down the task and delegate to specialists
    subtasks = architect.execute(
        f"Break down the following task into subtasks for the team: {task.task}"
    )

    # 4. Peer-review cycle (placeholder)
    # In a real implementation, this would be a more complex workflow
    for subtask in subtasks:
        # Delegate to the appropriate specialist
        specialist = architect.get_agent(subtask.agent)
        result = specialist.execute(subtask.task)

        # Peer-review
        # For now, we'll just have the architect review the code
        architect.execute(f"Review the following code: {result}")

    # 5. Consolidate patches and generate a commit message
    patches = [] # This will be populated with the generated patches
    commit_message = architect.execute("Generate a commit message for the changes.")

    return CodingTaskResponse(
        patches=patches,
        commit_message=commit_message,
        session_id=task.session_id,
    )