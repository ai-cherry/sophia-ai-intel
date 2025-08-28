from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

app = FastAPI(title="MCP GitHub Integration Service")

# Simulated repository storage
repositories = {}
commits = {}
pull_requests = {}

class Repository(BaseModel):
    owner: str
    name: str
    description: Optional[str] = ""
    private: Optional[bool] = False

class CommitRequest(BaseModel):
    repo_id: str
    message: str
    files: Dict[str, str]  # filename -> content
    branch: Optional[str] = "main"

class PullRequest(BaseModel):
    repo_id: str
    title: str
    description: str
    source_branch: str
    target_branch: Optional[str] = "main"

@app.get("/")
async def root():
    return {
        "service": "MCP GitHub Integration",
        "status": "active",
        "capabilities": ["repo_management", "code_commit", "pull_requests", "issue_tracking"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "repos": len(repositories), "commits": len(commits)}

@app.post("/repos/create")
async def create_repository(repo: Repository):
    """Create a new repository"""
    repo_id = f"{repo.owner}/{repo.name}"
    
    if repo_id in repositories:
        raise HTTPException(status_code=409, detail="Repository already exists")
    
    repositories[repo_id] = {
        "id": repo_id,
        "owner": repo.owner,
        "name": repo.name,
        "description": repo.description,
        "private": repo.private,
        "created_at": datetime.now().isoformat(),
        "default_branch": "main",
        "url": f"https://github.com/{repo_id}"
    }
    
    return {
        "repo_id": repo_id,
        "status": "created",
        "url": repositories[repo_id]["url"],
        "message": f"Repository {repo.name} created successfully"
    }

@app.get("/repos")
async def list_repositories():
    """List all repositories"""
    return {"repositories": list(repositories.values()), "total": len(repositories)}

@app.post("/commit")
async def create_commit(commit: CommitRequest):
    """Create a new commit"""
    if commit.repo_id not in repositories:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    commit_id = str(uuid.uuid4())[:8]
    
    commits[commit_id] = {
        "id": commit_id,
        "repo_id": commit.repo_id,
        "message": commit.message,
        "branch": commit.branch,
        "files_changed": len(commit.files),
        "files": commit.files,
        "author": "AI Assistant",
        "timestamp": datetime.now().isoformat()
    }
    
    return {
        "commit_id": commit_id,
        "status": "committed",
        "message": commit.message,
        "files_changed": len(commit.files),
        "branch": commit.branch,
        "url": f"https://github.com/{commit.repo_id}/commit/{commit_id}"
    }

@app.post("/push")
async def push_code(push_data: Dict[str, Any]):
    """Push code to repository"""
    repo_id = push_data.get("repo_id")
    code = push_data.get("code", {})
    message = push_data.get("message", "Code update via API")
    
    if not repo_id:
        raise HTTPException(status_code=400, detail="repo_id required")
    
    # Create automatic commit
    commit_request = CommitRequest(
        repo_id=repo_id,
        message=message,
        files=code
    )
    
    commit_result = await create_commit(commit_request)
    
    return {
        "status": "pushed",
        "commit": commit_result,
        "message": "Code pushed successfully"
    }

@app.post("/pr/create")
async def create_pull_request(pr: PullRequest):
    """Create a pull request"""
    if pr.repo_id not in repositories:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    pr_id = len(pull_requests) + 1
    
    pull_requests[pr_id] = {
        "id": pr_id,
        "repo_id": pr.repo_id,
        "title": pr.title,
        "description": pr.description,
        "source_branch": pr.source_branch,
        "target_branch": pr.target_branch,
        "status": "open",
        "created_at": datetime.now().isoformat(),
        "url": f"https://github.com/{pr.repo_id}/pull/{pr_id}"
    }
    
    return {
        "pr_id": pr_id,
        "status": "created",
        "url": pull_requests[pr_id]["url"],
        "message": f"Pull request '{pr.title}' created"
    }

@app.get("/repos/{owner}/{name}")
async def get_repository(owner: str, name: str):
    """Get repository details"""
    repo_id = f"{owner}/{name}"
    
    if repo_id not in repositories:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    return repositories[repo_id]

@app.post("/clone")
async def clone_repository(data: Dict[str, str]):
    """Clone a repository"""
    repo_url = data.get("url", "")
    
    # Simulate cloning
    return {
        "status": "cloned",
        "url": repo_url,
        "local_path": f"/tmp/repos/{repo_url.split('/')[-1]}",
        "message": "Repository cloned successfully"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)
