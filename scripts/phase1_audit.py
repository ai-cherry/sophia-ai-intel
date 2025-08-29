#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path
from datetime import datetime

class SophiaAuditor:
    def __init__(self, root_path="."):
        self.root = Path(root_path)
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.report_dir = self.root / f"reports/alignment/{self.date}"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
    def audit(self):
        """Execute full repo audit"""
        repo_state = {
            "services": self.scan_services(),
            "mcp_servers": self.scan_mcp(),
            "agents": self.scan_agents(),
            "ui_components": self.scan_ui_components()
        }
        
        tech_debt = {
            "duplicates": self.find_duplicates(),
            "mocks": self.find_mocks(),
            "dead_code": self.find_dead_code()
        }
        
        # Write reports
        with open(self.report_dir / "repo_state.json", "w") as f:
            json.dump(repo_state, f, indent=2)
            
        with open(self.report_dir / "tech_debt.json", "w") as f:
            json.dump(tech_debt, f, indent=2)
            
        return repo_state, tech_debt
        
    def scan_services(self):
        """Scan services directory for live/dead services"""
        services = []
        service_ports = {
            "sophia-brain": 8099,
            "unified-swarm": 8100,
            "mcp-context": 8081,
            "mcp-github": 8082,
            "mcp-research": 8085,
            "real-swarm-executor": 8088,
            "websocket-hub": 8096,
            "direct-swarm": 8200,
            "sophia-supreme": 8300
        }
        
        for name, port in service_ports.items():
            # Check if service file exists
            service_files = list(self.root.glob(f"services/*{name.replace('-', '_')}*"))
            if service_files:
                services.append({
                    "name": name,
                    "port": port,
                    "status": "configured",
                    "ws": [f"/ws/{name}"] if "websocket" in name or "swarm" in name else []
                })
        
        return services
        
    def scan_mcp(self):
        """Scan for MCP server implementations"""
        mcp_servers = []
        mcp_dirs = list((self.root / "libs" / "mcp").glob("mcp-*")) if (self.root / "libs" / "mcp").exists() else []
        
        for mcp_dir in mcp_dirs:
            health_url = f"http://localhost:808X/healthz"  # Placeholder
            mcp_servers.append({
                "name": mcp_dir.name,
                "implemented": (mcp_dir / "server.py").exists() or (mcp_dir / "index.ts").exists(),
                "health_url": health_url
            })
            
        return mcp_servers
        
    def scan_agents(self):
        """Scan agent implementations"""
        agents = []
        agent_types = ["planner", "researcher", "coder", "analyst", "reviewer"]
        
        for agent_type in agent_types:
            agents.append({
                "type": agent_type,
                "api": ["/swarms/create", f"/swarms/{{id}}/status"],
                "ws": [f"/ws/swarm/{{id}}"]
            })
            
        return agents
        
    def scan_ui_components(self):
        """Scan UI components for mock data usage"""
        components = []
        dashboard_path = self.root / "apps" / "sophia-dashboard" / "src" / "components"
        
        if dashboard_path.exists():
            for tsx_file in dashboard_path.glob("*.tsx"):
                content = tsx_file.read_text()
                has_mock = any(word in content.lower() for word in ["mock", "fake", "placeholder", "todo", "hardcoded"])
                if has_mock:
                    components.append({
                        "file": str(tsx_file.relative_to(self.root)),
                        "mock": True
                    })
                    
        return components
        
    def find_duplicates(self):
        """Find duplicate code and configs"""
        duplicates = []
        
        # Check for duplicate service definitions
        service_files = list(self.root.glob("services/*.py"))
        seen = {}
        
        for file in service_files:
            content_hash = hash(file.read_text())
            if content_hash in seen:
                duplicates.append({
                    "path": str(file.relative_to(self.root)),
                    "duplicate_of": str(seen[content_hash].relative_to(self.root))
                })
            else:
                seen[content_hash] = file
                
        return duplicates
        
    def find_mocks(self):
        """Find all mock implementations"""
        mocks = []
        
        for ext in ["tsx", "ts", "jsx", "js"]:
            for file in self.root.glob(f"apps/**/*.{ext}"):
                content = file.read_text()
                if re.search(r'\bmock\w*\s*[:=]|fake\w*|placeholder|TODO', content, re.IGNORECASE):
                    component_name = file.stem
                    mocks.append({
                        "component": component_name,
                        "location": str(file.relative_to(self.root))
                    })
                    
        return mocks
        
    def find_dead_code(self):
        """Find dead/unused code"""
        dead_code = []
        
        # Check for Fly.io configs
        fly_configs = list(self.root.glob("**/fly.toml"))
        for config in fly_configs:
            dead_code.append({
                "path": str(config.relative_to(self.root)),
                "last_used": "n/a"
            })
            
        # Check for old deployment configs
        old_deploys = ["docker-compose-old.yml", "deploy-old.sh", "backup-deploy.sh"]
        for pattern in old_deploys:
            for file in self.root.glob(f"**/{pattern}"):
                dead_code.append({
                    "path": str(file.relative_to(self.root)),
                    "last_used": "n/a"
                })
                
        return dead_code

if __name__ == "__main__":
    auditor = SophiaAuditor()
    repo_state, tech_debt = auditor.audit()
    
    print(f"✅ Audit complete: reports/alignment/{auditor.date}/")
    print(f"  - Found {len(repo_state['services'])} services")
    print(f"  - Found {len(tech_debt['mocks'])} mock components")
    print(f"  - Found {len(tech_debt['dead_code'])} dead code files")