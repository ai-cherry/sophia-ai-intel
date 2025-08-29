#!/usr/bin/env python3
"""
Repo Audit Script - Find all mocks, dead code, and duplicates
Output: JSON only, no essays
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any
import subprocess
import asyncio
import aiohttp

class RepoAuditor:
    def __init__(self, repo_root="."):
        self.repo_root = Path(repo_root)
        self.results = {
            "services": [],
            "mcp_servers": [],
            "agents": [],
            "ui_components": [],
            "duplicates": [],
            "mocks": [],
            "dead_code": [],
            "tech_debt": []
        }
    
    def scan_services(self):
        """Find all services and their status"""
        services_dir = self.repo_root / "services"
        if not services_dir.exists():
            return
        
        for service_path in services_dir.iterdir():
            if service_path.is_dir() and not service_path.name.startswith('.'):
                service = {
                    "name": service_path.name,
                    "path": str(service_path),
                    "status": "unknown",
                    "port": None,
                    "has_dockerfile": (service_path / "Dockerfile").exists(),
                    "has_main": any((service_path / f).exists() for f in ["main.py", "app.py", "server.py", "index.js"])
                }
                
                # Check if it's an MCP server
                if service_path.name.startswith("mcp-"):
                    mcp_info = {
                        "name": service_path.name,
                        "implemented": service["has_main"],
                        "path": str(service_path),
                        "health_url": None
                    }
                    
                    # Look for port in config
                    for file in ["config.py", "main.py", "app.py"]:
                        filepath = service_path / file
                        if filepath.exists():
                            content = filepath.read_text()
                            port_match = re.search(r'port["\s=:]+(\d{4,5})', content, re.IGNORECASE)
                            if port_match:
                                port = int(port_match.group(1))
                                service["port"] = port
                                mcp_info["health_url"] = f"http://localhost:{port}/health"
                                break
                    
                    self.results["mcp_servers"].append(mcp_info)
                
                # Check if service is actually running
                if service["port"]:
                    try:
                        result = subprocess.run(
                            f"lsof -i :{service['port']} | grep LISTEN",
                            shell=True, capture_output=True, text=True
                        )
                        service["status"] = "live" if result.returncode == 0 else "dead"
                    except:
                        pass
                
                self.results["services"].append(service)
    
    def scan_ui_components(self):
        """Find all UI components and check for mocks"""
        dashboard_dir = self.repo_root / "apps" / "sophia-dashboard" / "src"
        if not dashboard_dir.exists():
            return
        
        mock_patterns = [
            r'mock[a-zA-Z]*\s*[=:]',
            r'fake[a-zA-Z]*\s*[=:]',
            r'placeholder',
            r'TODO',
            r'hardcoded',
            r'dummy[a-zA-Z]*\s*[=:]',
            r'sample[a-zA-Z]*\s*[=:]',
            r'"status":\s*"ok"',  # Generic OK responses
            r'useState\(\[\]\)',  # Empty state arrays
            r'return\s+\{\s*status:\s*["\']ok["\']',
        ]
        
        for tsx_file in dashboard_dir.rglob("*.tsx"):
            content = tsx_file.read_text()
            component = {
                "file": str(tsx_file.relative_to(self.repo_root)),
                "uses_mock_data": False,
                "mock_locations": []
            }
            
            for pattern in mock_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    component["uses_mock_data"] = True
                    line_num = content[:match.start()].count('\n') + 1
                    component["mock_locations"].append({
                        "line": line_num,
                        "pattern": pattern,
                        "match": match.group(0)[:50]
                    })
            
            if component["uses_mock_data"]:
                self.results["ui_components"].append(component)
                self.results["mocks"].append({
                    "path": component["file"],
                    "count": len(component["mock_locations"])
                })
    
    def scan_agents(self):
        """Find agent definitions and swarm configs"""
        agents_dir = self.repo_root / "libs" / "agents"
        if agents_dir.exists():
            for py_file in agents_dir.rglob("*.py"):
                content = py_file.read_text()
                
                # Look for agent class definitions
                agent_matches = re.finditer(r'class\s+(\w*Agent\w*)', content)
                for match in agent_matches:
                    agent_name = match.group(1)
                    self.results["agents"].append({
                        "type": agent_name,
                        "file": str(py_file.relative_to(self.repo_root)),
                        "api_endpoints": self._extract_endpoints(content),
                        "ws_endpoints": self._extract_ws_endpoints(content)
                    })
    
    def _extract_endpoints(self, content: str) -> List[str]:
        """Extract API endpoint patterns"""
        endpoints = []
        patterns = [
            r'@app\.(get|post|put|delete)\(["\']([^"\']+)',
            r'router\.(get|post|put|delete)\(["\']([^"\']+)',
            r'path\s*=\s*["\']([^"\']+)'
        ]
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                endpoint = match.group(2) if len(match.groups()) > 1 else match.group(1)
                endpoints.append(endpoint)
        return list(set(endpoints))
    
    def _extract_ws_endpoints(self, content: str) -> List[str]:
        """Extract WebSocket endpoint patterns"""
        ws_endpoints = []
        patterns = [
            r'ws://[^"\'\s]+',
            r'WebSocket\(["\']([^"\']+)',
            r'@websocket\(["\']([^"\']+)'
        ]
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                ws_endpoints.append(match.group(0))
        return list(set(ws_endpoints))
    
    def find_duplicates(self):
        """Find duplicate code and configs"""
        seen_configs = {}
        
        # Check for duplicate env keys
        env_files = list(self.repo_root.glob(".env*"))
        all_keys = set()
        duplicate_keys = set()
        
        for env_file in env_files:
            if env_file.is_file():
                content = env_file.read_text()
                keys = re.findall(r'^([A-Z_]+)=', content, re.MULTILINE)
                for key in keys:
                    if key in all_keys:
                        duplicate_keys.add(key)
                    all_keys.add(key)
        
        if duplicate_keys:
            self.results["duplicates"].append({
                "type": "env_keys",
                "items": list(duplicate_keys)
            })
        
        # Check for duplicate service names
        service_names = [s["name"] for s in self.results["services"]]
        duplicate_services = [s for s in service_names if service_names.count(s) > 1]
        if duplicate_services:
            self.results["duplicates"].append({
                "type": "services",
                "items": list(set(duplicate_services))
            })
    
    def find_dead_code(self):
        """Find unused files and dead imports"""
        # Find files not imported anywhere
        all_py_files = list(self.repo_root.rglob("*.py"))
        all_ts_files = list(self.repo_root.rglob("*.ts"))
        all_tsx_files = list(self.repo_root.rglob("*.tsx"))
        
        # Check for files with no recent git activity (>60 days)
        try:
            result = subprocess.run(
                'git ls-files | xargs -I {} git log -1 --format="%ar {}" -- "{}" | grep -E "months|year"',
                shell=True, capture_output=True, text=True, cwd=self.repo_root
            )
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(' ', 3)
                        if len(parts) >= 4:
                            self.results["dead_code"].append({
                                "path": parts[3],
                                "last_modified": ' '.join(parts[:3])
                            })
        except:
            pass
    
    def calculate_tech_debt(self):
        """Calculate technical debt score"""
        debt_score = 0
        issues = []
        
        # Mock data penalty
        mock_count = len(self.results["mocks"])
        if mock_count > 0:
            debt_score += mock_count * 10
            issues.append(f"{mock_count} components using mock data")
        
        # Dead code penalty
        dead_count = len(self.results["dead_code"])
        if dead_count > 0:
            debt_score += dead_count * 5
            issues.append(f"{dead_count} potentially dead files")
        
        # Unimplemented MCP penalty
        unimplemented = [m for m in self.results["mcp_servers"] if not m["implemented"]]
        if unimplemented:
            debt_score += len(unimplemented) * 15
            issues.append(f"{len(unimplemented)} MCP servers not implemented")
        
        # Dead services penalty
        dead_services = [s for s in self.results["services"] if s["status"] == "dead"]
        if dead_services:
            debt_score += len(dead_services) * 8
            issues.append(f"{len(dead_services)} services not running")
        
        self.results["tech_debt"] = {
            "score": debt_score,
            "issues": issues,
            "priority_fixes": self._get_priority_fixes()
        }
    
    def _get_priority_fixes(self) -> List[Dict[str, Any]]:
        """Get prioritized fix list"""
        fixes = []
        
        # Priority 1: Remove mocks
        for mock in self.results["mocks"][:5]:  # Top 5
            fixes.append({
                "priority": 1,
                "action": "replace_mock",
                "target": mock["path"],
                "reason": f"{mock['count']} mock data instances"
            })
        
        # Priority 2: Implement missing MCPs
        for mcp in self.results["mcp_servers"]:
            if not mcp["implemented"]:
                fixes.append({
                    "priority": 2,
                    "action": "implement_or_delete",
                    "target": mcp["name"],
                    "reason": "MCP declared but not implemented"
                })
        
        # Priority 3: Delete dead code
        for dead in self.results["dead_code"][:3]:  # Top 3
            fixes.append({
                "priority": 3,
                "action": "delete",
                "target": dead["path"],
                "reason": f"Unused for {dead['last_modified']}"
            })
        
        return sorted(fixes, key=lambda x: x["priority"])
    
    async def test_health_endpoints(self):
        """Test all health endpoints"""
        async with aiohttp.ClientSession() as session:
            for service in self.results["services"]:
                if service["port"]:
                    health_url = f"http://localhost:{service['port']}/health"
                    try:
                        async with session.get(health_url, timeout=2) as resp:
                            service["health_status"] = resp.status
                            service["health_check"] = "pass" if resp.status == 200 else "fail"
                    except:
                        service["health_status"] = None
                        service["health_check"] = "timeout"
    
    def run_audit(self):
        """Run complete audit"""
        print("🔍 Scanning services...")
        self.scan_services()
        
        print("🔍 Scanning UI components...")
        self.scan_ui_components()
        
        print("🔍 Scanning agents...")
        self.scan_agents()
        
        print("🔍 Finding duplicates...")
        self.find_duplicates()
        
        print("🔍 Finding dead code...")
        self.find_dead_code()
        
        print("🔍 Calculating tech debt...")
        self.calculate_tech_debt()
        
        print("🔍 Testing health endpoints...")
        asyncio.run(self.test_health_endpoints())
        
        # Save results
        output_dir = self.repo_root / "audit_results"
        output_dir.mkdir(exist_ok=True)
        
        # repo_state.json
        repo_state = {
            "services": self.results["services"],
            "mcp_servers": self.results["mcp_servers"],
            "agents": self.results["agents"],
            "ui_components": self.results["ui_components"]
        }
        
        with open(output_dir / "repo_state.json", "w") as f:
            json.dump(repo_state, f, indent=2)
        
        # tech_debt.json
        tech_debt = {
            "duplicates": self.results["duplicates"],
            "mocks": self.results["mocks"],
            "dead_code": self.results["dead_code"],
            "summary": self.results["tech_debt"]
        }
        
        with open(output_dir / "tech_debt.json", "w") as f:
            json.dump(tech_debt, f, indent=2)
        
        # Print summary
        print("\n" + "="*50)
        print("AUDIT COMPLETE")
        print("="*50)
        print(f"📊 Tech Debt Score: {self.results['tech_debt']['score']}")
        print(f"🚨 Issues Found:")
        for issue in self.results['tech_debt']['issues']:
            print(f"  - {issue}")
        print(f"\n📁 Results saved to: {output_dir}")
        print(f"  - repo_state.json")
        print(f"  - tech_debt.json")
        
        # Print immediate actions
        print(f"\n🔥 IMMEDIATE ACTIONS:")
        for fix in self.results['tech_debt']['priority_fixes'][:5]:
            print(f"  P{fix['priority']}: {fix['action'].upper()} → {fix['target']}")
            print(f"       Reason: {fix['reason']}")

if __name__ == "__main__":
    auditor = RepoAuditor()
    auditor.run_audit()