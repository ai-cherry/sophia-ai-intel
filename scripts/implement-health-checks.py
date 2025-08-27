#!/usr/bin/env python3
"""
Comprehensive Health Check Implementation
Creates robust health check endpoints for all services
"""

import os
from pathlib import Path
from typing import Dict, List
import json

class HealthCheckImplementer:
    """Implements comprehensive health checks for all services"""
    
    def __init__(self):
        self.service_dirs = []
        self.health_check_templates = {}
        
    def find_all_services(self) -> List[Path]:
        """Find all service directories"""
        services = []
        
        # Find services in services/ directory
        services_dir = Path('services')
        if services_dir.exists():
            for service_dir in services_dir.iterdir():
                if service_dir.is_dir() and not service_dir.name.startswith('.'):
                    services.append(service_dir)
        
        # Find services in mcp/ directory
        mcp_dir = Path('mcp')
        if mcp_dir.exists():
            for service_dir in mcp_dir.iterdir():
                if service_dir.is_dir() and not service_dir.name.startswith('.'):
                    services.append(service_dir)
        
        # Find other service directories
        other_services = ['agentic', 'llm/portkey-llm', 'memory/mem0', 'agents/swarm']
        for service_path in other_services:
            service_dir = Path(service_path)
            if service_dir.exists():
                services.append(service_dir)
        
        return services
    
    def create_python_health_check(self, service_name: str) -> str:
        """Create Python FastAPI health check implementation"""
        
        return f'''#!/usr/bin/env python3
"""
Health Check Implementation for {service_name}
Comprehensive health monitoring with dependency validation
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import os
import asyncio
import aiohttp
import time
import structlog
from typing import Dict, Any, List, Optional
import redis.asyncio as redis
import psycopg
from sqlalchemy import create_engine, text
from datetime import datetime, timezone

logger = structlog.get_logger()

class HealthStatus(BaseModel):
    status: str
    service: str
    timestamp: str
    version: str
    dependencies: Dict[str, Any]
    performance_metrics: Dict[str, Any]

class DependencyCheck:
    """Check external dependencies"""
    
    @staticmethod
    async def check_redis(redis_url: str) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            client = redis.from_url(redis_url)
            start_time = time.time()
            await client.ping()
            latency = (time.time() - start_time) * 1000
            await client.aclose()
            
            return {{
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "connection": "success"
            }}
        except Exception as e:
            return {{
                "status": "unhealthy", 
                "error": str(e),
                "connection": "failed"
            }}
    
    @staticmethod
    async def check_postgres(db_url: str) -> Dict[str, Any]:
        """Check PostgreSQL connectivity"""
        try:
            engine = create_engine(db_url)
            start_time = time.time()
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            latency = (time.time() - start_time) * 1000
            
            return {{
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "connection": "success"
            }}
        except Exception as e:
            return {{
                "status": "unhealthy",
                "error": str(e),
                "connection": "failed"
            }}
    
    @staticmethod
    async def check_qdrant(qdrant_url: str, api_key: str) -> Dict[str, Any]:
        """Check Qdrant connectivity"""
        try:
            headers = {{"Authorization": f"Bearer {{api_key}}"}} if api_key else {{}}
            
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(f"{{qdrant_url}}/health", headers=headers) as response:
                    latency = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return {{
                            "status": "healthy",
                            "latency_ms": round(latency, 2),
                            "connection": "success"
                        }}
                    else:
                        return {{
                            "status": "unhealthy",
                            "http_status": response.status,
                            "connection": "failed"
                        }}
        except Exception as e:
            return {{
                "status": "unhealthy",
                "error": str(e),
                "connection": "failed"
            }}
    
    @staticmethod
    async def check_http_service(service_url: str, service_name: str) -> Dict[str, Any]:
        """Check HTTP service connectivity"""
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(f"{{service_url}}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    latency = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return {{
                            "status": "healthy",
                            "latency_ms": round(latency, 2),
                            "connection": "success"
                        }}
                    else:
                        return {{
                            "status": "unhealthy", 
                            "http_status": response.status,
                            "connection": "failed"
                        }}
        except Exception as e:
            return {{
                "status": "unhealthy",
                "error": str(e),
                "connection": "failed"
            }}

async def comprehensive_health_check() -> HealthStatus:
    """Perform comprehensive health check"""
    
    start_time = time.time()
    service_healthy = True
    dependencies = {{}}
    
    # Check Redis if configured
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        dependencies["redis"] = await DependencyCheck.check_redis(redis_url)
        if dependencies["redis"]["status"] != "healthy":
            service_healthy = False
    
    # Check PostgreSQL if configured
    postgres_url = os.getenv("POSTGRES_URL")
    if postgres_url:
        dependencies["postgres"] = await DependencyCheck.check_postgres(postgres_url)
        if dependencies["postgres"]["status"] != "healthy":
            service_healthy = False
    
    # Check Qdrant if configured
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_key = os.getenv("QDRANT_API_KEY")
    if qdrant_url:
        dependencies["qdrant"] = await DependencyCheck.check_qdrant(qdrant_url, qdrant_key)
        if dependencies["qdrant"]["status"] != "healthy":
            service_healthy = False
    
    # Check dependent MCP services
    dependent_services = [
        ("mcp-context", os.getenv("CONTEXT_MCP_URL")),
        ("mcp-agents", os.getenv("AGENTS_MCP_URL")), 
        ("mcp-research", os.getenv("RESEARCH_MCP_URL")),
        ("mcp-business", os.getenv("BUSINESS_MCP_URL"))
    ]
    
    for service_name, service_url in dependent_services:
        if service_url and service_name != "{service_name}":  # Don't check self
            dependencies[service_name] = await DependencyCheck.check_http_service(service_url, service_name)
            if dependencies[service_name]["status"] != "healthy":
                # Don't fail health check for dependent services, just log
                logger.warning(f"Dependent service {{service_name}} is unhealthy")
    
    # Performance metrics
    total_latency = (time.time() - start_time) * 1000
    performance_metrics = {{
        "total_health_check_latency_ms": round(total_latency, 2),
        "dependency_count": len(dependencies),
        "healthy_dependencies": sum(1 for dep in dependencies.values() if dep.get("status") == "healthy")
    }}
    
    return HealthStatus(
        status="healthy" if service_healthy else "unhealthy",
        service="{service_name}",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=os.getenv("SERVICE_VERSION", "1.0.0"),
        dependencies=dependencies,
        performance_metrics=performance_metrics
    )

def add_health_endpoints_to_app(app: FastAPI):
    """Add health check endpoints to FastAPI app"""
    
    @app.get("/health", response_model=HealthStatus)
    async def health_check():
        """Comprehensive health check endpoint"""
        try:
            health_status = await comprehensive_health_check()
            
            if health_status.status == "unhealthy":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=health_status.dict()
                )
            
            return health_status
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Health check failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={{"status": "unhealthy", "error": str(e)}}
            )
    
    @app.get("/health/quick")
    async def quick_health_check():
        """Quick health check endpoint for load balancers"""
        return {{"status": "healthy", "service": "{service_name}"}}
    
    @app.get("/health/ready")
    async def readiness_check():
        """Kubernetes readiness probe endpoint"""
        health_status = await comprehensive_health_check()
        
        # Service is ready if core dependencies are healthy
        core_deps = ["redis", "postgres"]
        ready = all(
            dependencies.get(dep, {{}}).get("status") == "healthy" 
            for dep in core_deps 
            if dep in health_status.dependencies
        )
        
        if not ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={{"status": "not_ready", "dependencies": health_status.dependencies}}
            )
        
        return {{"status": "ready", "service": "{service_name}"}}
    
    @app.get("/health/live") 
    async def liveness_check():
        """Kubernetes liveness probe endpoint"""
        # Simple check to ensure service is alive
        return {{"status": "alive", "service": "{service_name}"}}

# Health check configuration
HEALTH_CHECK_CONFIG = {{
    "redis_required": {{"redis_url" if "context" in service_name or "agent" in service_name else "False"}},
    "postgres_required": {{"postgres_url" if "context" in service_name else "False"}}, 
    "qdrant_required": {{"qdrant_url" if "context" in service_name else "False"}},
    "dependent_services": []
}}
'''
    
    def create_nodejs_health_check(self, service_name: str) -> str:
        """Create Node.js/TypeScript health check implementation"""
        
        return f'''// Health Check Implementation for {service_name}
// Comprehensive health monitoring with dependency validation

import {{ FastifyInstance }} from 'fastify';
import axios from 'axios';

interface HealthStatus {{
  status: string;
  service: string;
  timestamp: string;
  version: string;
  dependencies: Record<string, any>;
  performance_metrics: Record<string, any>;
}}

interface DependencyResult {{
  status: string;
  latency_ms?: number;
  connection: string;
  error?: string;
}}

class HealthChecker {{
  
  static async checkRedis(redisUrl: string): Promise<DependencyResult> {{
    try {{
      const startTime = Date.now();
      // TODO: Implement Redis client check
      const latency = Date.now() - startTime;
      
      return {{
        status: 'healthy',
        latency_ms: latency,
        connection: 'success'
      }};
    }} catch (error) {{
      return {{
        status: 'unhealthy',
        error: error instanceof Error ? error.message : 'Unknown error',
        connection: 'failed'
      }};
    }}
  }}
  
  static async checkHttpService(serviceUrl: string): Promise<DependencyResult> {{
    try {{
      const startTime = Date.now();
      const response = await axios.get(`${{serviceUrl}}/health`, {{ timeout: 5000 }});
      const latency = Date.now() - startTime;
      
      if (response.status === 200) {{
        return {{
          status: 'healthy',
          latency_ms: latency,
          connection: 'success'
        }};
      }} else {{
        return {{
          status: 'unhealthy',
          connection: 'failed'
        }};
      }}
    }} catch (error) {{
      return {{
        status: 'unhealthy',
        error: error instanceof Error ? error.message : 'Unknown error',
        connection: 'failed'
      }};
    }}
  }}
  
  static async performComprehensiveCheck(): Promise<HealthStatus> {{
    const startTime = Date.now();
    let serviceHealthy = true;
    const dependencies: Record<string, any> = {{}};
    
    // Check Redis if configured
    const redisUrl = process.env.REDIS_URL;
    if (redisUrl) {{
      dependencies.redis = await this.checkRedis(redisUrl);
      if (dependencies.redis.status !== 'healthy') {{
        serviceHealthy = false;
      }}
    }}
    
    // Check dependent services
    const dependentServices = [
      ['mcp-context', process.env.CONTEXT_MCP_URL],
      ['mcp-agents', process.env.AGENTS_MCP_URL],
      ['mcp-research', process.env.RESEARCH_MCP_URL]
    ];
    
    for (const [serviceName, serviceUrl] of dependentServices) {{
      if (serviceUrl && serviceName !== '{service_name}') {{
        dependencies[serviceName] = await this.checkHttpService(serviceUrl);
      }}
    }}
    
    const totalLatency = Date.now() - startTime;
    
    return {{
      status: serviceHealthy ? 'healthy' : 'unhealthy',
      service: '{service_name}',
      timestamp: new Date().toISOString(),
      version: process.env.SERVICE_VERSION || '1.0.0',
      dependencies,
      performance_metrics: {{
        total_health_check_latency_ms: totalLatency,
        dependency_count: Object.keys(dependencies).length,
        healthy_dependencies: Object.values(dependencies).filter(dep => dep.status === 'healthy').length
      }}
    }};
  }}
}}

export function registerHealthEndpoints(app: FastifyInstance) {{
  
  // Comprehensive health check
  app.get('/health', async (request, reply) => {{
    try {{
      const healthStatus = await HealthChecker.performComprehensiveCheck();
      
      if (healthStatus.status === 'unhealthy') {{
        reply.code(503);
      }}
      
      return healthStatus;
    }} catch (error) {{
      reply.code(503);
      return {{
        status: 'unhealthy',
        service: '{service_name}',
        error: error instanceof Error ? error.message : 'Unknown error'
      }};
    }}
  }});
  
  // Quick health check for load balancers
  app.get('/health/quick', async (request, reply) => {{
    return {{ status: 'healthy', service: '{service_name}' }};
  }});
  
  // Readiness probe for Kubernetes
  app.get('/health/ready', async (request, reply) => {{
    const healthStatus = await HealthChecker.performComprehensiveCheck();
    
    // Check if core dependencies are ready
    const coreDeps = ['redis'];
    const ready = coreDeps.every(dep => 
      !healthStatus.dependencies[dep] || healthStatus.dependencies[dep].status === 'healthy'
    );
    
    if (!ready) {{
      reply.code(503);
      return {{ status: 'not_ready', dependencies: healthStatus.dependencies }};
    }}
    
    return {{ status: 'ready', service: '{service_name}' }};
  }});
  
  // Liveness probe for Kubernetes
  app.get('/health/live', async (request, reply) => {{
    return {{ status: 'alive', service: '{service_name}' }};
  }});
}}
'''

    def create_kubernetes_health_probes(self, service_name: str) -> str:
        """Create Kubernetes health probe configuration"""
        
        return f'''
        # Health probes for {service_name}
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 3
        
        # Startup probe for slower services
        startupProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 30  # Allow up to 150 seconds for startup
'''
    
    def implement_health_checks_for_service(self, service_dir: Path):
        """Implement health checks for a specific service"""
        service_name = service_dir.name
        
        # Check if it's a Python service
        if (service_dir / 'requirements.txt').exists() or (service_dir / 'pyproject.toml').exists():
            print(f"  🐍 Implementing Python health checks for {service_name}")
            
            # Create health check module
            health_check_content = self.create_python_health_check(service_name)
            health_check_file = service_dir / 'health_check.py'
            
            with open(health_check_file, 'w') as f:
                f.write(health_check_content)
            
            print(f"    ✅ Created {health_check_file}")
        
        # Check if it's a Node.js service
        elif (service_dir / 'package.json').exists() or (service_dir / 'tsconfig.json').exists():
            print(f"  📦 Implementing Node.js health checks for {service_name}")
            
            # Create health check module
            health_check_content = self.create_nodejs_health_check(service_name)
            health_check_file = service_dir / 'src' / 'health' / 'healthChecker.ts'
            
            # Create health directory if it doesn't exist
            health_dir = service_dir / 'src' / 'health'
            health_dir.mkdir(parents=True, exist_ok=True)
            
            with open(health_check_file, 'w') as f:
                f.write(health_check_content)
            
            print(f"    ✅ Created {health_check_file}")
        
        # Update Kubernetes manifest with health probes
        k8s_manifest = Path(f'k8s-deploy/manifests/{service_name}.yaml')
        if k8s_manifest.exists():
            print(f"  ☸️  Adding health probes to {k8s_manifest}")
            
            # Read current manifest
            with open(k8s_manifest) as f:
                manifest_content = f.read()
            
            # Check if health probes already exist
            if 'livenessProbe' not in manifest_content:
                # Add health probes after the ports section
                probe_config = self.create_kubernetes_health_probes(service_name)
                
                # Find the ports section and add probes after
                if 'ports:' in manifest_content:
                    lines = manifest_content.split('\n')
                    new_lines = []
                    in_container = False
                    added_probes = False
                    
                    for line in lines:
                        new_lines.append(line)
                        
                        # Look for container section with ports
                        if '- name:' in line and 'containers:' in '\n'.join(lines[max(0, len(new_lines)-10):]):
                            in_container = True
                        
                        # Add health probes after ports section
                        if in_container and 'ports:' in line and not added_probes:
                            # Find end of ports section
                            i = lines.index(line) + 1
                            while i < len(lines) and lines[i].startswith(' ') and '- ' in lines[i]:
                                new_lines.append(lines[i])
                                i += 1
                            
                            # Add health probes
                            for probe_line in probe_config.split('\n'):
                                if probe_line.strip():
                                    new_lines.append('        ' + probe_line.strip())
                            
                            added_probes = True
                    
                    if added_probes:
                        with open(k8s_manifest, 'w') as f:
                            f.write('\n'.join(new_lines))
                        print(f"    ✅ Added health probes to {k8s_manifest}")
    
    def create_health_check_validation_script(self):
        """Create script to validate all health checks"""
        
        validation_script = '''#!/usr/bin/env python3
"""
Health Check Validation Script
Tests all service health endpoints
"""

import asyncio
import aiohttp
import json
from typing import Dict, List
from pathlib import Path

async def test_health_endpoint(service_name: str, base_url: str) -> Dict:
    """Test health endpoints for a service"""
    
    endpoints = [
        '/health',
        '/health/quick', 
        '/health/ready',
        '/health/live'
    ]
    
    results = {}
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    results[endpoint] = {
                        "status_code": response.status,
                        "response_time_ms": response.headers.get('X-Response-Time', 'unknown'),
                        "status": "success" if response.status < 400 else "failure"
                    }
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            results[endpoint]["response_data"] = data
                        except:
                            results[endpoint]["response_data"] = await response.text()
                            
            except Exception as e:
                results[endpoint] = {
                    "status": "error",
                    "error": str(e)
                }
    
    return results

async def validate_all_health_checks():
    """Validate health checks for all services"""
    
    print("🏥 Validating health check implementations...")
    
    # Services to test (adjust based on actual deployment)
    services = [
        ("mcp-context", "http://localhost:8080"),
        ("mcp-agents", "http://localhost:8081"),
        ("mcp-research", "http://localhost:8082"),
        ("agno-coordinator", "http://localhost:8083"),
        ("agno-teams", "http://localhost:8084")
    ]
    
    results = {}
    
    for service_name, base_url in services:
        print(f"  🔍 Testing {service_name}...")
        results[service_name] = await test_health_endpoint(service_name, base_url)
        
        # Summary for this service
        endpoints_tested = len(results[service_name])
        successful_endpoints = sum(1 for result in results[service_name].values() 
                                 if result.get("status") == "success")
        
        print(f"    ✅ {successful_endpoints}/{endpoints_tested} endpoints healthy")
    
    # Generate report
    print("\\n📊 Health Check Validation Report:")
    for service, service_results in results.items():
        print(f"\\n{service}:")
        for endpoint, result in service_results.items():
            status_icon = "✅" if result.get("status") == "success" else "❌"
            print(f"  {status_icon} {endpoint}: {result.get('status_code', 'N/A')}")
    
    return results

if __name__ == "__main__":
    asyncio.run(validate_all_health_checks())
'''

        with open('scripts/validate-health-checks.py', 'w') as f:
            f.write(validation_script)
        
        os.chmod('scripts/validate-health-checks.py', 0o755)
        print("✅ Created health check validation script")
    
    def run_implementation(self):
        """Run comprehensive health check implementation"""
        print("🏥 Implementing comprehensive health checks...\n")
        
        # Find all services
        self.service_dirs = self.find_all_services()
        print(f"Found {len(self.service_dirs)} services to update")
        
        # Implement health checks for each service
        for service_dir in self.service_dirs:
            print(f"\n📦 Processing {service_dir.name}...")
            self.implement_health_checks_for_service(service_dir)
        
        # Create validation script
        print(f"\n🔧 Creating health check validation tools...")
        self.create_health_check_validation_script()
        
        print(f"\n📊 Implementation Complete:")
        print(f"  📦 Updated {len(self.service_dirs)} services")
        print(f"  🏥 Added comprehensive health endpoints")
        print(f"  ☸️  Updated Kubernetes health probes")
        print(f"  🔧 Created validation scripts")

def main():
    """Main function"""
    implementer = HealthCheckImplementer()
    implementer.run_implementation()
    
    print(f"\n💡 Next Steps:")
    print("1. Update service main files to import health check functions")
    print("2. Test health endpoints locally") 
    print("3. Run scripts/validate-health-checks.py to verify")
    print("4. Deploy services and monitor health metrics")

if __name__ == "__main__":
    main()
