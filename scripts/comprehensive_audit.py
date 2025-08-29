#!/usr/bin/env python3
"""
Comprehensive System Audit for Sophia AI
Broader and deeper analysis of all components
"""

import json
import os
import sys
import time
import subprocess
import socket
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import asyncio
import aiohttp
from colorama import init, Fore, Style

init(autoreset=True)

class ComprehensiveAuditor:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "sections": {},
            "issues": [],
            "warnings": [],
            "successes": [],
            "metrics": {},
            "recommendations": []
        }
        self.base_path = Path(".")
        
    def print_header(self, title: str):
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}{title.center(80)}")
        print(f"{Fore.CYAN}{'='*80}\n")
        
    def print_section(self, title: str):
        print(f"\n{Fore.YELLOW}▶ {title}")
        print(f"{Fore.YELLOW}{'─'*60}")
        
    async def audit_api_endpoints(self):
        """Deep audit of all API endpoints"""
        self.print_section("API Endpoints Audit")
        
        endpoints = [
            # Dashboard APIs
            ("http://localhost:3000/api/chat", "POST", {"message": "test"}),
            ("http://localhost:3000/api/health", "GET", None),
            ("http://localhost:3000/api/metrics", "GET", None),
            ("http://localhost:3000/api/metrics?target=health", "GET", None),
            ("http://localhost:3000/api/metrics?target=targets", "GET", None),
            ("http://localhost:3000/api/agents", "GET", None),
            ("http://localhost:3000/api/agents?action=activity", "GET", None),
            ("http://localhost:3000/api/agents", "POST", {"action": "list"}),
            ("http://localhost:3000/api/results", "GET", None),
            ("http://localhost:3000/api/status", "GET", None),
            
            # Backend Services
            ("http://localhost:8100/swarms", "GET", None),
            ("http://localhost:8100/agents", "GET", None),
            ("http://localhost:8100/health", "GET", None),
            ("http://localhost:8081/health", "GET", None),  # MCP Context
            ("http://localhost:8082/health", "GET", None),  # GitHub
            ("http://localhost:8095/health", "GET", None),  # Chat Coordinator
            ("http://localhost:8099/health", "GET", None),  # Sophia Brain
            ("http://localhost:8200/health", "GET", None),  # Direct Swarm
            ("http://localhost:8300/health", "GET", None),  # Sophia Supreme
            ("http://localhost:9090/-/healthy", "GET", None),  # Prometheus
        ]
        
        results = []
        async with aiohttp.ClientSession() as session:
            for url, method, data in endpoints:
                try:
                    start = time.time()
                    if method == "GET":
                        async with session.get(url, timeout=5) as resp:
                            latency = (time.time() - start) * 1000
                            status = resp.status
                            body = await resp.text()
                    else:
                        async with session.post(url, json=data, timeout=5) as resp:
                            latency = (time.time() - start) * 1000
                            status = resp.status
                            body = await resp.text()
                    
                    # Analyze response
                    is_mock = self._detect_mock_response(body)
                    has_error = status >= 400
                    
                    result = {
                        "url": url,
                        "method": method,
                        "status": status,
                        "latency_ms": round(latency, 2),
                        "is_mock": is_mock,
                        "has_error": has_error,
                        "body_preview": body[:200] if body else None
                    }
                    
                    if has_error:
                        self.results["issues"].append(f"API Error: {url} returned {status}")
                        print(f"  {Fore.RED}✗ {url}: {status}")
                    elif is_mock:
                        self.results["warnings"].append(f"Mock Data: {url}")
                        print(f"  {Fore.YELLOW}⚠ {url}: Mock response detected")
                    else:
                        self.results["successes"].append(f"API OK: {url}")
                        print(f"  {Fore.GREEN}✓ {url}: {status} ({latency:.0f}ms)")
                    
                    results.append(result)
                    
                except asyncio.TimeoutError:
                    self.results["issues"].append(f"Timeout: {url}")
                    print(f"  {Fore.RED}✗ {url}: Timeout")
                    results.append({"url": url, "error": "timeout"})
                except Exception as e:
                    self.results["issues"].append(f"Connection Failed: {url}")
                    print(f"  {Fore.RED}✗ {url}: {str(e)[:50]}")
                    results.append({"url": url, "error": str(e)})
        
        self.results["sections"]["api_endpoints"] = results
        return results
    
    def _detect_mock_response(self, body: str) -> bool:
        """Detect if response contains mock data"""
        mock_indicators = [
            "mock", "Mock", "MOCK",
            "dummy", "Dummy", "DUMMY",
            "placeholder", "Placeholder",
            "TODO", "todo",
            "fake", "Fake", "FAKE",
            "sample", "Sample", "SAMPLE",
            "test data", "Test Data",
            "Lorem ipsum",
            "example.com",
            "Agent-1", "agent-1",  # Common mock IDs
        ]
        return any(indicator in body for indicator in mock_indicators)
    
    def audit_websocket_connections(self):
        """Audit WebSocket endpoints"""
        self.print_section("WebSocket Connections Audit")
        
        ws_endpoints = [
            ("localhost", 8100, "/ws/swarm/test"),
            ("localhost", 3000, "/ws"),
            ("localhost", 8200, "/ws"),
        ]
        
        results = []
        for host, port, path in ws_endpoints:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    print(f"  {Fore.GREEN}✓ WebSocket ready: ws://{host}:{port}{path}")
                    self.results["successes"].append(f"WebSocket ready: {host}:{port}")
                    results.append({"endpoint": f"ws://{host}:{port}{path}", "status": "ready"})
                else:
                    print(f"  {Fore.RED}✗ WebSocket offline: ws://{host}:{port}{path}")
                    self.results["issues"].append(f"WebSocket offline: {host}:{port}")
                    results.append({"endpoint": f"ws://{host}:{port}{path}", "status": "offline"})
            except Exception as e:
                print(f"  {Fore.RED}✗ WebSocket error: ws://{host}:{port}{path}: {str(e)}")
                self.results["issues"].append(f"WebSocket error: {host}:{port}")
                results.append({"endpoint": f"ws://{host}:{port}{path}", "error": str(e)})
        
        self.results["sections"]["websockets"] = results
        return results
    
    def audit_file_structure(self):
        """Deep audit of file structure and organization"""
        self.print_section("File Structure & Organization Audit")
        
        critical_paths = {
            "Backend Services": [
                "services/planning/intelligent_planner_v2.py",
                "services/real_swarm_executor.py",
                "libs/agents/swarm_manager.py",
                "backend/agents/agent_orchestrator.py",
            ],
            "Dashboard Components": [
                "apps/sophia-dashboard/src/app/page.tsx",
                "apps/sophia-dashboard/src/app/page-unified.tsx",
                "apps/sophia-dashboard/src/lib/swarm-client.ts",
                "apps/sophia-dashboard/src/components/ChatRenderer.tsx",
            ],
            "API Routes": [
                "apps/sophia-dashboard/src/app/api/chat/route.ts",
                "apps/sophia-dashboard/src/app/api/chat/unified-route.ts",
                "apps/sophia-dashboard/src/app/api/health/route.ts",
                "apps/sophia-dashboard/src/app/api/metrics/route.ts",
            ],
            "MCP Servers": [
                "services/mcp-context/server.py",
                "services/mcp-github/server.py",
                "services/mcp-memory/server.py",
            ],
            "Configuration": [
                "docker-compose.yml",
                "pyproject.toml",
                "package.json",
                ".env",
                ".env.production",
            ]
        }
        
        results = {}
        for category, paths in critical_paths.items():
            category_results = []
            for path in paths:
                file_path = self.base_path / path
                exists = file_path.exists()
                
                if exists:
                    size = file_path.stat().st_size
                    modified = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    
                    # Check for issues
                    is_empty = size == 0
                    is_too_large = size > 1_000_000  # 1MB
                    
                    if is_empty:
                        print(f"  {Fore.YELLOW}⚠ {path}: Empty file")
                        self.results["warnings"].append(f"Empty file: {path}")
                    elif is_too_large:
                        print(f"  {Fore.YELLOW}⚠ {path}: Large file ({size/1024:.1f}KB)")
                        self.results["warnings"].append(f"Large file: {path}")
                    else:
                        print(f"  {Fore.GREEN}✓ {path}: OK ({size} bytes)")
                        self.results["successes"].append(f"File OK: {path}")
                    
                    category_results.append({
                        "path": path,
                        "exists": True,
                        "size": size,
                        "modified": modified,
                        "issues": []
                    })
                else:
                    print(f"  {Fore.RED}✗ {path}: Missing")
                    self.results["issues"].append(f"Missing file: {path}")
                    category_results.append({
                        "path": path,
                        "exists": False
                    })
            
            results[category] = category_results
        
        self.results["sections"]["file_structure"] = results
        return results
    
    def audit_dependencies(self):
        """Audit Python and Node.js dependencies"""
        self.print_section("Dependencies Audit")
        
        results = {}
        
        # Python dependencies
        if Path("requirements.txt").exists():
            with open("requirements.txt") as f:
                py_deps = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            
            critical_deps = ["langchain", "fastapi", "redis", "qdrant-client", "openai"]
            missing = [dep for dep in critical_deps if not any(dep in line for line in py_deps)]
            
            if missing:
                print(f"  {Fore.YELLOW}⚠ Missing Python deps: {', '.join(missing)}")
                self.results["warnings"].append(f"Missing Python deps: {missing}")
            else:
                print(f"  {Fore.GREEN}✓ All critical Python dependencies present")
                self.results["successes"].append("Python dependencies OK")
            
            results["python"] = {
                "total": len(py_deps),
                "critical": critical_deps,
                "missing": missing
            }
        
        # Node.js dependencies
        if Path("package.json").exists():
            with open("package.json") as f:
                pkg = json.load(f)
                node_deps = list(pkg.get("dependencies", {}).keys())
            
            critical_node = ["next", "react", "typescript", "tailwindcss"]
            missing_node = [dep for dep in critical_node if dep not in node_deps]
            
            if missing_node:
                print(f"  {Fore.YELLOW}⚠ Missing Node deps: {', '.join(missing_node)}")
                self.results["warnings"].append(f"Missing Node deps: {missing_node}")
            else:
                print(f"  {Fore.GREEN}✓ All critical Node dependencies present")
                self.results["successes"].append("Node dependencies OK")
            
            results["nodejs"] = {
                "total": len(node_deps),
                "critical": critical_node,
                "missing": missing_node
            }
        
        self.results["sections"]["dependencies"] = results
        return results
    
    def audit_docker_services(self):
        """Audit Docker services and containers"""
        self.print_section("Docker Services Audit")
        
        try:
            # Check docker-compose services
            result = subprocess.run(
                ["docker-compose", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                services = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            service = json.loads(line)
                            services.append(service)
                            
                            if service.get("State") == "running":
                                print(f"  {Fore.GREEN}✓ {service.get('Service')}: Running")
                                self.results["successes"].append(f"Docker service running: {service.get('Service')}")
                            else:
                                print(f"  {Fore.YELLOW}⚠ {service.get('Service')}: {service.get('State')}")
                                self.results["warnings"].append(f"Docker service not running: {service.get('Service')}")
                        except json.JSONDecodeError:
                            pass
                
                self.results["sections"]["docker_services"] = services
            else:
                print(f"  {Fore.YELLOW}⚠ No Docker services running")
                self.results["warnings"].append("No Docker services running")
                
        except subprocess.TimeoutExpired:
            print(f"  {Fore.RED}✗ Docker command timeout")
            self.results["issues"].append("Docker command timeout")
        except FileNotFoundError:
            print(f"  {Fore.YELLOW}⚠ Docker Compose not installed")
            self.results["warnings"].append("Docker Compose not installed")
        except Exception as e:
            print(f"  {Fore.RED}✗ Docker error: {str(e)}")
            self.results["issues"].append(f"Docker error: {str(e)}")
    
    def audit_security(self):
        """Security audit - check for exposed secrets, API keys, etc."""
        self.print_section("Security Audit")
        
        sensitive_patterns = [
            "api_key",
            "API_KEY",
            "secret",
            "SECRET",
            "password",
            "PASSWORD",
            "token",
            "TOKEN",
            "private_key",
            "PRIVATE_KEY"
        ]
        
        # Check for .env files
        env_files = [".env", ".env.local", ".env.production"]
        for env_file in env_files:
            if Path(env_file).exists():
                print(f"  {Fore.YELLOW}⚠ Found {env_file} - ensure it's in .gitignore")
                self.results["warnings"].append(f"Environment file exists: {env_file}")
        
        # Check .gitignore
        if Path(".gitignore").exists():
            with open(".gitignore") as f:
                gitignore = f.read()
            
            for env_file in env_files:
                if env_file not in gitignore:
                    print(f"  {Fore.RED}✗ {env_file} not in .gitignore!")
                    self.results["issues"].append(f"Security: {env_file} not in .gitignore")
                else:
                    print(f"  {Fore.GREEN}✓ {env_file} properly ignored")
                    self.results["successes"].append(f"Security: {env_file} in .gitignore")
        
        # Check for hardcoded secrets in code files
        code_extensions = [".py", ".ts", ".js", ".tsx", ".jsx"]
        hardcoded_secrets = []
        
        for ext in code_extensions:
            for file_path in Path(".").rglob(f"*{ext}"):
                if "node_modules" in str(file_path) or ".next" in str(file_path):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        for pattern in sensitive_patterns:
                            if f'{pattern}="' in content or f"{pattern}='" in content:
                                # Check if it's not a placeholder
                                if not any(placeholder in content for placeholder in ["process.env", "os.environ", "${", "example", "your-"]):
                                    hardcoded_secrets.append(str(file_path))
                                    break
                except Exception:
                    pass
        
        if hardcoded_secrets:
            print(f"  {Fore.RED}✗ Possible hardcoded secrets in {len(hardcoded_secrets)} files")
            self.results["issues"].append(f"Hardcoded secrets found in {len(hardcoded_secrets)} files")
            for file_path in hardcoded_secrets[:5]:  # Show first 5
                print(f"    - {file_path}")
        else:
            print(f"  {Fore.GREEN}✓ No hardcoded secrets detected")
            self.results["successes"].append("No hardcoded secrets found")
        
        self.results["sections"]["security"] = {
            "env_files": env_files,
            "hardcoded_secrets_count": len(hardcoded_secrets),
            "files_with_secrets": hardcoded_secrets[:10]  # Limit to 10 for report
        }
    
    def audit_performance(self):
        """Performance metrics audit"""
        self.print_section("Performance Metrics")
        
        metrics = {}
        
        # Check bundle size for Next.js
        next_dir = Path("apps/sophia-dashboard/.next")
        if next_dir.exists():
            total_size = sum(f.stat().st_size for f in next_dir.rglob("*") if f.is_file())
            metrics["next_build_size_mb"] = round(total_size / 1024 / 1024, 2)
            
            if metrics["next_build_size_mb"] > 100:
                print(f"  {Fore.YELLOW}⚠ Large Next.js build: {metrics['next_build_size_mb']}MB")
                self.results["warnings"].append(f"Large build size: {metrics['next_build_size_mb']}MB")
            else:
                print(f"  {Fore.GREEN}✓ Next.js build size: {metrics['next_build_size_mb']}MB")
                self.results["successes"].append(f"Build size OK: {metrics['next_build_size_mb']}MB")
        
        # Count total files
        total_files = len(list(Path(".").rglob("*")))
        metrics["total_files"] = total_files
        print(f"  {Fore.CYAN}ℹ Total files in project: {total_files}")
        
        # Count lines of code
        loc = 0
        for ext in [".py", ".ts", ".tsx", ".js", ".jsx"]:
            for file_path in Path(".").rglob(f"*{ext}"):
                if "node_modules" not in str(file_path) and ".next" not in str(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            loc += len(f.readlines())
                    except:
                        pass
        
        metrics["lines_of_code"] = loc
        print(f"  {Fore.CYAN}ℹ Total lines of code: {loc:,}")
        
        self.results["sections"]["performance"] = metrics
        self.results["metrics"] = metrics
    
    def generate_recommendations(self):
        """Generate actionable recommendations based on audit"""
        self.print_section("Recommendations")
        
        recommendations = []
        
        # Based on issues found
        if len(self.results["issues"]) > 10:
            recommendations.append({
                "priority": "HIGH",
                "category": "Stability",
                "action": "Address critical issues immediately",
                "details": f"Found {len(self.results['issues'])} critical issues that need immediate attention"
            })
        
        if any("Mock" in warning for warning in self.results["warnings"]):
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Data Integrity",
                "action": "Replace remaining mock data with real implementations",
                "details": "Some endpoints still return mock data"
            })
        
        if any("WebSocket offline" in issue for issue in self.results["issues"]):
            recommendations.append({
                "priority": "HIGH",
                "category": "Real-time Features",
                "action": "Start WebSocket services for real-time updates",
                "details": "WebSocket connections are required for live swarm monitoring"
            })
        
        if any("Docker" in warning for warning in self.results["warnings"]):
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Deployment",
                "action": "Configure and start Docker services",
                "details": "Docker services provide consistent development environment"
            })
        
        if self.results.get("metrics", {}).get("next_build_size_mb", 0) > 100:
            recommendations.append({
                "priority": "LOW",
                "category": "Performance",
                "action": "Optimize Next.js bundle size",
                "details": "Consider code splitting and lazy loading"
            })
        
        # Print recommendations
        for rec in recommendations:
            color = Fore.RED if rec["priority"] == "HIGH" else Fore.YELLOW if rec["priority"] == "MEDIUM" else Fore.CYAN
            print(f"  {color}[{rec['priority']}] {rec['category']}: {rec['action']}")
            print(f"    {rec['details']}")
        
        self.results["recommendations"] = recommendations
        return recommendations
    
    def save_report(self):
        """Save comprehensive audit report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path("audit_results") / timestamp
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON report
        with open(report_dir / "audit_report.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Save summary markdown
        with open(report_dir / "summary.md", "w") as f:
            f.write(f"# Comprehensive Audit Report\n\n")
            f.write(f"**Date:** {self.results['timestamp']}\n\n")
            
            f.write(f"## Summary\n\n")
            f.write(f"- **Critical Issues:** {len(self.results['issues'])}\n")
            f.write(f"- **Warnings:** {len(self.results['warnings'])}\n")
            f.write(f"- **Successes:** {len(self.results['successes'])}\n\n")
            
            f.write(f"## Critical Issues\n\n")
            for issue in self.results["issues"][:20]:  # Top 20
                f.write(f"- ❌ {issue}\n")
            
            f.write(f"\n## Warnings\n\n")
            for warning in self.results["warnings"][:20]:  # Top 20
                f.write(f"- ⚠️ {warning}\n")
            
            f.write(f"\n## Recommendations\n\n")
            for rec in self.results["recommendations"]:
                f.write(f"### [{rec['priority']}] {rec['category']}\n")
                f.write(f"**Action:** {rec['action']}\n")
                f.write(f"{rec['details']}\n\n")
            
            f.write(f"\n## Metrics\n\n")
            for key, value in self.results.get("metrics", {}).items():
                f.write(f"- **{key}:** {value}\n")
        
        print(f"\n{Fore.GREEN}Report saved to: {report_dir}")
        return report_dir
    
    async def run_full_audit(self):
        """Run complete comprehensive audit"""
        self.print_header("COMPREHENSIVE SYSTEM AUDIT")
        
        # Run all audit sections
        await self.audit_api_endpoints()
        self.audit_websocket_connections()
        self.audit_file_structure()
        self.audit_dependencies()
        self.audit_docker_services()
        self.audit_security()
        self.audit_performance()
        self.generate_recommendations()
        
        # Print summary
        self.print_header("AUDIT SUMMARY")
        print(f"{Fore.RED}Critical Issues: {len(self.results['issues'])}")
        print(f"{Fore.YELLOW}Warnings: {len(self.results['warnings'])}")
        print(f"{Fore.GREEN}Successes: {len(self.results['successes'])}")
        
        # Save report
        report_dir = self.save_report()
        
        # Return exit code based on issues
        if len(self.results['issues']) > 0:
            print(f"\n{Fore.RED}Audit completed with {len(self.results['issues'])} critical issues")
            return 1
        else:
            print(f"\n{Fore.GREEN}Audit completed successfully!")
            return 0

async def main():
    auditor = ComprehensiveAuditor()
    exit_code = await auditor.run_full_audit()
    sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())
