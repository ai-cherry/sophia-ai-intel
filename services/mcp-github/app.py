import os, base64, time
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from github_app import gh_get

REPO = os.getenv("GITHUB_REPO", "ai-cherry/sophia-ai-intel")
DASHBOARD_ORIGIN = os.getenv("DASHBOARD_ORIGIN", "https://sophiaai-dashboard.fly.dev")

app = FastAPI(title="sophia-mcp-github", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[DASHBOARD_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
async def healthz():
    return {
        "status": "healthy",
        "service": "sophia-mcp-github", 
        "version": "1.0.0", 
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "uptime_ms": int(time.time() * 1000),
        "repo": REPO
    }

class FileResponse(BaseModel):
    path: str
    ref: str
    encoding: str
    content: str  # base64

@app.get("/repo/file", response_model=FileResponse)
async def repo_file(path: str = Query(...), ref: str = Query("main")):
    """
    Returns file content base64-encoded. Caller can JSON.stringify or decode as needed.
    """
    try:
        data = await gh_get(f"/repos/{REPO}/contents/{path}?ref={ref}")
        if isinstance(data, list):
            raise HTTPException(status_code=400, detail="Path is a directory")
        content = data.get("content", "")
        encoding = data.get("encoding", "base64")
        return {"path": path, "ref": ref, "encoding": encoding, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/repo/tree")
async def repo_tree(path: str = Query(""), ref: str = Query("main")):
    """
    Lists directory entries at path on ref.
    """
    api_path = f"/repos/{REPO}/contents/{path}?ref={ref}"
    try:
        data = await gh_get(api_path)
        if isinstance(data, dict) and data.get("type") == "file":
            return {"path": path, "ref": ref, "entries": [{"type":"file","name":data["name"],"path":data["path"]}]}
        entries = []
        for item in data:
            entries.append({"type": item["type"], "name": item["name"], "path": item["path"], "size": item.get("size", 0)})
        return {"path": path, "ref": ref, "entries": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

