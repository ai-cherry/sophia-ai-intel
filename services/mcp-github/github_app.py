import os
import time
import httpx
import jwt  # PyJWT

GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_INSTALLATION_ID = os.getenv("GITHUB_INSTALLATION_ID")
GITHUB_PRIVATE_KEY = os.getenv("GITHUB_PRIVATE_KEY")  # PEM (base64 or literal)

class MissingCredentialsError(Exception):
    """Raised when required GitHub App credentials are missing"""
    pass

def check_credentials():
    """Check if all required credentials are present"""
    missing = []
    if not GITHUB_APP_ID:
        missing.append("GITHUB_APP_ID")
    if not GITHUB_INSTALLATION_ID:
        missing.append("GITHUB_INSTALLATION_ID")
    if not GITHUB_PRIVATE_KEY:
        missing.append("GITHUB_PRIVATE_KEY")
    
    if missing:
        raise MissingCredentialsError(f"Missing required credentials: {', '.join(missing)}")

def _load_private_key() -> str:
    key = GITHUB_PRIVATE_KEY or ""
    # allow base64-encoded PEM
    if "BEGIN PRIVATE KEY" in key:
        return key
    try:
        import base64
        return base64.b64decode(key).decode("utf-8")
    except Exception:
        return key

def _jwt_for_app() -> str:
    check_credentials()
    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + 540, "iss": GITHUB_APP_ID}
    token = jwt.encode(payload, _load_private_key(), algorithm="RS256")
    return token

async def _installation_token() -> str:
    app_jwt = _jwt_for_app()
    url = f"https://api.github.com/app/installations/{GITHUB_INSTALLATION_ID}/access_tokens"
    headers = {"Authorization": f"Bearer {app_jwt}", "Accept": "application/vnd.github+json"}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(url, headers=headers)
        r.raise_for_status()
        return r.json()["token"]

async def gh_get(path: str):
    check_credentials()
    token = await _installation_token()
    url = f"https://api.github.com{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        return r.json()