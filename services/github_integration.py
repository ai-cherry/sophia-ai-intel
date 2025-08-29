"""
GitHub Integration - Real functionality using Personal Access Token
"""

import os
import httpx
import base64
from typing import Dict, List, Optional
from datetime import datetime

class GitHubIntegration:
    """Real GitHub integration using PAT"""
    
    def __init__(self):
        # Get token from environment variable only
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            print("Warning: GITHUB_TOKEN not set in environment")
            self.token = None
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    async def get_user_repos(self) -> List[Dict]:
        """Get user's repositories"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/user/repos",
                headers=self.headers,
                params={"sort": "updated", "per_page": 10}
            )
            if response.status_code == 200:
                return response.json()
            return []
    
    async def create_file(self, repo: str, path: str, content: str, message: str) -> Dict:
        """Create or update a file in a repository"""
        # Encode content to base64
        encoded_content = base64.b64encode(content.encode()).decode()
        
        async with httpx.AsyncClient() as client:
            # Check if file exists
            check_response = await client.get(
                f"{self.base_url}/repos/{repo}/contents/{path}",
                headers=self.headers
            )
            
            data = {
                "message": message,
                "content": encoded_content
            }
            
            # If file exists, need to provide SHA
            if check_response.status_code == 200:
                existing = check_response.json()
                data["sha"] = existing["sha"]
            
            # Create/update file
            response = await client.put(
                f"{self.base_url}/repos/{repo}/contents/{path}",
                headers=self.headers,
                json=data
            )
            
            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "commit": response.json()["commit"],
                    "path": path
                }
            return {"success": False, "error": response.text}
    
    async def create_pull_request(self, repo: str, title: str, body: str, head: str, base: str = "main") -> Dict:
        """Create a pull request"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/repos/{repo}/pulls",
                headers=self.headers,
                json={
                    "title": title,
                    "body": body,
                    "head": head,
                    "base": base
                }
            )
            
            if response.status_code == 201:
                pr = response.json()
                return {
                    "success": True,
                    "pr_number": pr["number"],
                    "url": pr["html_url"]
                }
            return {"success": False, "error": response.text}
    
    async def create_branch(self, repo: str, branch_name: str, from_branch: str = "main") -> Dict:
        """Create a new branch"""
        async with httpx.AsyncClient() as client:
            # Get the SHA of the base branch
            ref_response = await client.get(
                f"{self.base_url}/repos/{repo}/git/refs/heads/{from_branch}",
                headers=self.headers
            )
            
            if ref_response.status_code != 200:
                return {"success": False, "error": "Could not get base branch"}
            
            sha = ref_response.json()["object"]["sha"]
            
            # Create new branch
            response = await client.post(
                f"{self.base_url}/repos/{repo}/git/refs",
                headers=self.headers,
                json={
                    "ref": f"refs/heads/{branch_name}",
                    "sha": sha
                }
            )
            
            if response.status_code == 201:
                return {"success": True, "branch": branch_name}
            return {"success": False, "error": response.text}
    
    async def search_code(self, query: str, repo: Optional[str] = None) -> List[Dict]:
        """Search code in repositories"""
        search_query = query
        if repo:
            search_query = f"repo:{repo} {query}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search/code",
                headers=self.headers,
                params={"q": search_query, "per_page": 10}
            )
            
            if response.status_code == 200:
                return response.json()["items"]
            return []

# Global instance
github = GitHubIntegration()

async def push_code_to_github(code: str, filename: str, repo: str, message: str = None) -> Dict:
    """Push code to GitHub and create a PR"""
    
    if not message:
        message = f"Add {filename} - Generated by Sophia AI"
    
    # Create a branch
    branch_name = f"sophia-ai-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    branch_result = await github.create_branch(repo, branch_name)
    
    if not branch_result["success"]:
        return branch_result
    
    # Create/update the file
    file_result = await github.create_file(
        repo=repo,
        path=filename,
        content=code,
        message=message
    )
    
    if not file_result["success"]:
        return file_result
    
    # Create a pull request
    pr_result = await github.create_pull_request(
        repo=repo,
        title=f"[Sophia AI] {message}",
        body=f"## Generated by Sophia AI\n\n{message}\n\n### Files Changed\n- {filename}\n\n🤖 This PR was automatically generated.",
        head=branch_name
    )
    
    return pr_result