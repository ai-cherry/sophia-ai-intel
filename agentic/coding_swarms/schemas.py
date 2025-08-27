from pydantic import BaseModel
from typing import List

class CodingTaskRequest(BaseModel):
    task: str
    session_id: str = None

class Patch(BaseModel):
    file_path: str
    diff: str

class CodingTaskResponse(BaseModel):
    patches: List[Patch]
    commit_message: str
    session_id: str