import os, base64, time
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from github_app import gh_get, MissingCredentialsError

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

def normalized_error(provider: str, code: str, message: str):
    """Return normalized error JSON format"""
    return {
        "error": {
            "provider": provider,
            "code": code,
            "message": message
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

@app.get("/healthz")
async def healthz():
    # Check for credentials
    missing = []
    if not os.getenv("GITHUB_APP_ID"):
        missing.append("GITHUB_APP_ID")
    if not os.getenv("GITHUB_INSTALLATION_ID"):
        missing.append("GITHUB_INSTALLATION_ID")
    if not os.getenv("GITHUB_PRIVATE_KEY"):
        missing.append("GITHUB_PRIVATE_KEY")
    
    if missing:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "sophia-mcp-github",
                "version": "1.0.0",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "uptime_ms": int(time.time() * 1000),
                "repo": REPO,
                "error": normalized_error(
                    "github_app",
                    "MISSING_CREDENTIALS",
                    f"Missing required credentials: {', '.join(missing)}"
                )
            }
        )
    
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
    except MissingCredentialsError as e:
        return JSONResponse(
            status_code=503,
            content=normalized_error("github_app", "MISSING_CREDENTIALS", str(e))
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=normalized_error("github_app", "API_ERROR", str(e))
        )

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
    except MissingCredentialsError as e:
        return JSONResponse(
            status_code=503,
            content=normalized_error("github_app", "MISSING_CREDENTIALS", str(e))
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=normalized_error("github_app", "API_ERROR", str(e))
        )