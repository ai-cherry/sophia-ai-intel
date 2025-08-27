#!/usr/bin/env python3
# scripts/neon_rest.py
"""
Neon REST API Client
Manages Neon PostgreSQL branches, endpoints, and JWT/JWKS configuration
"""

import os
import sys
import json
import argparse
import asyncio
import aiohttp
from urllib.parse import urljoin

# ---- env (with your provided defaults; override in shell or CI) ----
NEON_API_KEY            = os.getenv("NEON_API_KEY", "napi_r3gsuacduzw44nqdqav1u0hr2uv4bb2if48r8627jkxo7e4b2sxn92wsgf6zlxby")
NEON_REST_API_ENDPOINT  = os.getenv("NEON_REST_API_ENDPOINT", "https://console.neon.tech/api/v2")
NEON_PROJECT_ID         = os.getenv("NEON_PROJECT_ID", "rough-union-72390895")
NEON_BRANCH_ID          = os.getenv("NEON_BRANCH_ID", "br-green-firefly-afykrx78")
NEON_AUTH_JWKS_URL      = os.getenv("NEON_AUTH_JWKS_URL", "https://api.stack-auth.com/api/v1/projects/b17512e4-eb5b-4466-a90c-5b5255217ff7/.well-known/jwks.json")
NEON_PASSWORD           = os.getenv("NEON_PASSWORD", "Huskers1983$")  # used only for DSN assembly

# sensible defaults; adjust if your role/db differ
DEFAULT_USER            = os.getenv("NEON_ROLE", "neondb_owner")
DEFAULT_DB              = os.getenv("NEON_DB", "neondb")
DEFAULT_REGION          = os.getenv("NEON_REGION", "aws-us-west-2")

def _normalize_base(base: str) -> str:
    b = base.strip().rstrip("/")
    # If someone passed a project app URL, ensure it still hits the REST surface.
    if "/api/" not in b:
        # default REST surface
        if "console.neon.tech" not in b:
            # fallback to official REST
            return "https://console.neon.tech/api/v2"
        return b + "/api/v2"
    return b

BASE = _normalize_base(NEON_REST_API_ENDPOINT)

def auth_headers():
    return {
        "Authorization": f"Bearer {NEON_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

async def _req(method: str, path: str, payload=None, session: aiohttp.ClientSession = None):
    url = urljoin(BASE + "/", path.lstrip("/"))
    close = False
    s = session
    if s is None:
        s = aiohttp.ClientSession()
        close = True
    try:
        async with s.request(method, url, headers=auth_headers(), json=payload) as r:
            txt = await r.text()
            if r.status >= 400:
                raise RuntimeError(f"{method} {url} -> {r.status} {txt[:240]}")
            return json.loads(txt) if txt else {}
    finally:
        if close:
            await s.close()

# ---------------- Neon REST helpers ----------------
async def list_projects():
    return await _req("GET", f"projects")

async def get_branch(project_id: str, branch_id: str):
    return await _req("GET", f"projects/{project_id}/branches/{branch_id}")

async def create_branch(project_id: str, name: str):
    payload = {"branch": {"name": name}}
    return await _req("POST", f"projects/{project_id}/branches", payload)

async def list_endpoints(project_id: str):
    return await _req("GET", f"projects/{project_id}/endpoints")

async def create_endpoint(project_id: str, branch_id: str, region_id: str = DEFAULT_REGION, type_: str = "read_write"):
    payload = {"endpoint": {"branch_id": branch_id, "type": type_, "region_id": region_id}}
    return await _req("POST", f"projects/{project_id}/endpoints", payload)

async def add_jwks(project_id: str, jwks_url: str, provider_name: str = "custom-idp"):
    payload = {"jwks": {"provider_name": provider_name, "url": jwks_url}}
    return await _req("POST", f"projects/{project_id}/jwks", payload)

def build_dsn(host: str, user: str = DEFAULT_USER, db: str = DEFAULT_DB, password: str = NEON_PASSWORD) -> str:
    # Neon default port is 5432; override via env if needed
    port = int(os.getenv("NEON_PORT", "5432"))
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"

# ---------------- CLI ----------------
async def main():
    ap = argparse.ArgumentParser(description="Neon REST client")
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("projects")
    g = sub.add_parser("branch-get"); g.add_argument("--project", default=NEON_PROJECT_ID); g.add_argument("--branch", default=NEON_BRANCH_ID)
    c = sub.add_parser("branch-create"); c.add_argument("--project", default=NEON_PROJECT_ID); c.add_argument("--name", required=True)

    le = sub.add_parser("endpoints"); le.add_argument("--project", default=NEON_PROJECT_ID)
    ce = sub.add_parser("endpoint-create"); ce.add_argument("--project", default=NEON_PROJECT_ID); ce.add_argument("--branch", default=NEON_BRANCH_ID); ce.add_argument("--region", default=DEFAULT_REGION); ce.add_argument("--type", default="read_write")

    jw = sub.add_parser("jwks-add"); jw.add_argument("--project", default=NEON_PROJECT_ID); jw.add_argument("--url", default=NEON_AUTH_JWKS_URL); jw.add_argument("--provider", default="custom-idp")

    ds = sub.add_parser("dsn"); ds.add_argument("--host", required=True); ds.add_argument("--user", default=DEFAULT_USER); ds.add_argument("--db", default=DEFAULT_DB)

    args = ap.parse_args()
    if args.cmd == "projects":
        out = await list_projects(); print(json.dumps(out, indent=2)); return
    if args.cmd == "branch-get":
        out = await get_branch(args.project, args.branch); print(json.dumps(out, indent=2)); return
    if args.cmd == "branch-create":
        out = await create_branch(args.project, args.name); print(json.dumps(out, indent=2)); return
    if args.cmd == "endpoints":
        out = await list_endpoints(args.project); print(json.dumps(out, indent=2)); return
    if args.cmd == "endpoint-create":
        out = await create_endpoint(args.project, args.branch, args.region, args.type); print(json.dumps(out, indent=2)); return
    if args.cmd == "jwks-add":
        out = await add_jwks(args.project, args.url, args.provider); print(json.dumps(out, indent=2)); return
    if args.cmd == "dsn":
        print(build_dsn(args.host, args.user, args.db)); return

    ap.print_help()

if __name__ == "__main__":
    if not NEON_API_KEY:
        print("ERROR: NEON_API_KEY not set", file=sys.stderr); sys.exit(1)
    asyncio.run(main())