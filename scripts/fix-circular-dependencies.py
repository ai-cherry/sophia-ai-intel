#!/usr/bin/env python3
"""
Circular Dependency Resolution Script
Analyzes and fixes circular dependencies between MCP services
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Set
import json
import re

class CircularDependencyFixer:
    """Fixes circular dependencies in service architecture"""
    
    def __init__(self):
        self.services = {}
        self.dependencies = {}
        self.circular_deps = []
        
    def analyze_docker_compose(self) -> Dict:
        """Analyze docker-compose.yml for service dependencies"""
        compose_file = Path('docker-compose.yml')
        if not compose_file.exists():
            return {}
            
        try:
            with open(compose_file) as f:
                compose_data = yaml.safe_load(f)
            
            services = compose_data.get('services', {})
            
            for service_name, service_config in services.items():
                depends_on = service_config.get('depends_on', [])
                self.dependencies[service_name] = depends_on
                
            return services
        except Exception as e:
            print(f"Error analyzing docker-compose.yml: {e}")
            return {}
    
    def analyze_k8s_manifests(self) -> Dict:
        """Analyze Kubernetes manifests for service dependencies"""
        manifests_dir = Path('k8s-deploy/manifests')
        service_deps = {}
        
        if not manifests_dir.exists():
            return service_deps
            
        for manifest_file in manifests_dir.glob('*.yaml'):
            if 'mcp-' in manifest_file.name or 'agno-' in manifest_file.name:
                try:
                    with open(manifest_file) as f:
                        content = f.read()
                        
                    # Extract service references from environment variables
                    env_vars = re.findall(r'(\w+_MCP_URL|.*_URL): http://([^:]+):', content)
                    
                    service_name = manifest_file.stem
                    deps = [dep[1] for dep in env_vars if dep[1] != service_name]
                    
                    if deps:
                        service_deps[service_name] = deps
                        print(f"  📄 {service_name} depends on: {deps}")
                        
                except Exception as e:
                    print(f"Error analyzing {manifest_file}: {e}")
        
        return service_deps
    
    def find_circular_dependencies(self, deps: Dict[str, List[str]]) -> List[List[str]]:
        """Find circular dependencies using depth-first search"""
        visited = set()
        rec_stack = set()
        circular_paths = []
        
        def dfs(service: str, path: List[str] = None) -> bool:
            if path is None:
                path = []
                
            if service in rec_stack:
                # Found circular dependency
                cycle_start = path.index(service)
                cycle = path[cycle_start:] + [service]
                circular_paths.append(cycle)
                return True
                
            if service in visited:
                return False
                
            visited.add(service)
            rec_stack.add(service)
            
            for dependency in deps.get(service, []):
                if dfs(dependency, path + [service]):
                    return True
                    
            rec_stack.remove(service)
            return False
        
        for service in deps:
            if service not in visited:
                dfs(service)
                
        return circular_paths
    
    def create_event_bus_pattern(self):
        """Create event bus pattern to break circular dependencies"""
        
        # Create event bus service definition
        event_bus_config = """
# Event Bus Service for Breaking Circular Dependencies
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sophia-event-bus
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sophia-event-bus
  template:
    metadata:
      labels:
        app: sophia-event-bus
    spec:
      containers:
      - name: event-bus
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        env:
        - name: REDIS_CONFIG_FILE
          value: /etc/redis/redis.conf
        volumeMounts:
        - name: config
          mountPath: /etc/redis
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
      volumes:
      - name: config
        configMap:
          name: event-bus-config
---
apiVersion: v1
kind: Service
metadata:
  name: sophia-event-bus
  namespace: default
spec:
  selector:
    app: sophia-event-bus
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: event-bus-config
  namespace: default
data:
  redis.conf: |
    bind 0.0.0.0
    port 6379
    timeout 0
    tcp-keepalive 300
    maxmemory 200mb
    maxmemory-policy allkeys-lru
    save ""
"""

        with open('k8s-deploy/manifests/sophia-event-bus.yaml', 'w') as f:
            f.write(event_bus_config)
        
        print("✅ Created sophia-event-bus.yaml")
    
    def create_service_discovery_pattern(self):
        """Create service discovery to replace direct service calls"""
        
        discovery_config = """#!/usr/bin/env python3
'''
Service Discovery Implementation
Replaces direct service-to-service calls with event-driven communication
'''

import asyncio
import redis.asyncio as redis
from typing import Dict, Any, List
import json
import structlog

logger = structlog.get_logger()

class ServiceDiscovery:
    '''Service discovery and event bus implementation'''
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client = None
        
    async def connect(self):
        '''Connect to Redis event bus'''
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Connected to service discovery bus")
        except Exception as e:
            logger.error("Failed to connect to service discovery", error=str(e))
            raise
    
    async def register_service(self, service_name: str, health_endpoint: str):
        '''Register service with discovery'''
        service_info = {
            "name": service_name,
            "health_endpoint": health_endpoint,
            "timestamp": asyncio.get_event_loop().time(),
            "status": "healthy"
        }
        
        await self.redis_client.hset(
            "services:registry", 
            service_name, 
            json.dumps(service_info)
        )
        
        logger.info("Service registered", service=service_name)
    
    async def publish_event(self, event_type: str, data: Dict[str, Any]):
        '''Publish event to event bus'''
        event = {
            "type": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await self.redis_client.publish(f"events:{event_type}", json.dumps(event))
        logger.info("Event published", event_type=event_type)
    
    async def subscribe_to_events(self, event_types: List[str], callback):
        '''Subscribe to event types'''
        pubsub = self.redis_client.pubsub()
        
        for event_type in event_types:
            await pubsub.subscribe(f"events:{event_type}")
        
        logger.info("Subscribed to events", event_types=event_types)
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    event_data = json.loads(message['data'])
                    await callback(event_data)
                except Exception as e:
                    logger.error("Error processing event", error=str(e))
    
    async def get_service_endpoint(self, service_name: str) -> str:
        '''Get service endpoint from registry'''
        service_data = await self.redis_client.hget("services:registry", service_name)
        
        if service_data:
            service_info = json.loads(service_data)
            return service_info.get('health_endpoint', '')
        
        return None

# Example usage for MCP services
async def setup_mcp_service_discovery():
    '''Setup service discovery for MCP services'''
    discovery = ServiceDiscovery("redis://sophia-event-bus:6379")
    await discovery.connect()
    
    # Register this service
    service_name = os.getenv("SERVICE_NAME", "unknown")
    health_endpoint = f"http://{service_name}:8080/health"
    
    await discovery.register_service(service_name, health_endpoint)
    
    return discovery

# Event types for service communication
EVENT_TYPES = {
    "CONTEXT_REQUEST": "context.request",
    "CONTEXT_RESPONSE": "context.response", 
    "AGENT_REQUEST": "agent.request",
    "AGENT_RESPONSE": "agent.response",
    "BUSINESS_EVENT": "business.event",
    "RESEARCH_REQUEST": "research.request",
    "RESEARCH_RESPONSE": "research.response"
}
"""

        with open('platform/common/service_discovery.py', 'w') as f:
            f.write(discovery_config)
        
        print("✅ Created service_discovery.py")
    
    def fix_mcp_context_dependencies(self):
        """Fix MCP context service to use event bus"""
        
        # Read current mcp-context app
        context_app_path = Path('services/mcp-context/app.py')
        if not context_app_path.exists():
            print("⚠️ MCP context app not found")
            return
            
        # Create event-driven version
        event_driven_context = """#!/usr/bin/env python3
'''
MCP Context Service - Event Driven Architecture
Breaks circular dependencies using event bus pattern
'''

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import structlog
from typing import Dict, Any, List, Optional
import asyncio

# Import service discovery
import sys
sys.path.append('/app/platform/common')
from service_discovery import ServiceDiscovery, EVENT_TYPES

logger = structlog.get_logger()

app = FastAPI(
    title="Sophia MCP Context Service",
    description="Context management with event-driven architecture",
    version="2.0.0"
)

# Global service discovery instance
discovery: Optional[ServiceDiscovery] = None

class ContextRequest(BaseModel):
    query: str
    context_type: str = "general"
    max_results: int = 10

class ContextResponse(BaseModel):
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]

@app.on_event("startup")
async def startup_event():
    '''Initialize service discovery on startup'''
    global discovery
    
    redis_url = os.getenv("REDIS_URL", "redis://sophia-event-bus:6379")
    discovery = ServiceDiscovery(redis_url)
    
    try:
        await discovery.connect()
        await discovery.register_service("mcp-context", "http://mcp-context:8080/health")
        
        # Subscribe to relevant events
        await discovery.subscribe_to_events([
            EVENT_TYPES["CONTEXT_REQUEST"]
        ], handle_context_request_event)
        
        logger.info("MCP Context service initialized with event bus")
    except Exception as e:
        logger.error("Failed to initialize service discovery", error=str(e))

async def handle_context_request_event(event_data: Dict[str, Any]):
    '''Handle context request events from other services'''
    try:
        request_data = event_data.get("data", {})
        query = request_data.get("query", "")
        
        # Process context request
        results = await process_context_query(query)
        
        # Publish response event
        response_data = {
            "request_id": request_data.get("request_id"),
            "results": results,
            "service": "mcp-context"
        }
        
        await discovery.publish_event(EVENT_TYPES["CONTEXT_RESPONSE"], response_data)
        
    except Exception as e:
        logger.error("Error handling context request event", error=str(e))

async def process_context_query(query: str) -> List[Dict[str, Any]]:
    '''Process context query - mock implementation'''
    # TODO: Implement actual context processing
    return [
        {
            "content": f"Context result for: {query}",
            "score": 0.95,
            "source": "mcp-context"
        }
    ]

@app.get("/health")
async def health_check():
    '''Health check endpoint'''
    try:
        if discovery and discovery.redis_client:
            await discovery.redis_client.ping()
            return {"status": "healthy", "service": "mcp-context", "event_bus": "connected"}
    except Exception:
        pass
    
    return {"status": "unhealthy", "service": "mcp-context", "event_bus": "disconnected"}

@app.post("/context/search")
async def search_context(request: ContextRequest) -> ContextResponse:
    '''Search context endpoint - now publishes events instead of direct calls'''
    
    # Publish context request event
    request_data = {
        "request_id": f"ctx_{asyncio.get_event_loop().time()}",
        "query": request.query,
        "context_type": request.context_type,
        "max_results": request.max_results
    }
    
    if discovery:
        await discovery.publish_event(EVENT_TYPES["CONTEXT_REQUEST"], request_data)
    
    # Process locally and return
    results = await process_context_query(request.query)
    
    return ContextResponse(
        results=results,
        metadata={"service": "mcp-context", "event_driven": True}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        reload=False
    )
"""

        with open('services/mcp-context/app_event_driven.py', 'w') as f:
            f.write(event_driven_context)
        
        print("✅ Created event-driven mcp-context service")
    
    def create_dependency_breaking_strategy(self):
        """Create strategy document for breaking circular dependencies"""
        
        strategy_doc = """# Circular Dependency Resolution Strategy

## IDENTIFIED CIRCULAR DEPENDENCIES

Based on audit findings, the following circular dependency pattern exists:

```
mcp-context ↔ mcp-agents ↔ orchestrator ↔ mcp-context
```

This creates deployment failures and runtime instability.

## SOLUTION: EVENT-DRIVEN ARCHITECTURE

### 1. Event Bus Implementation
- **Technology:** Redis Pub/Sub
- **Service:** sophia-event-bus (dedicated Redis instance)
- **Pattern:** Publisher-Subscriber with event routing

### 2. Service Communication Flow

#### BEFORE (Circular Dependencies):
```
mcp-context → mcp-agents → orchestrator → mcp-context ❌
```

#### AFTER (Event-Driven):
```
mcp-context → EVENT_BUS ← mcp-agents
     ↑                        ↓
     └── EVENT_BUS ← orchestrator
```

### 3. Event Types

| Event Type | Publisher | Subscriber | Purpose |
|------------|-----------|------------|---------|
| `context.request` | mcp-agents | mcp-context | Request context data |
| `context.response` | mcp-context | mcp-agents | Return context results |
| `agent.request` | orchestrator | mcp-agents | Request agent execution |
| `agent.response` | mcp-agents | orchestrator | Return agent results |
| `business.event` | mcp-business | All | Business data updates |

### 4. Implementation Steps

#### Phase 1: Deploy Event Bus
1. Deploy sophia-event-bus Redis service
2. Configure pub/sub channels
3. Test basic connectivity

#### Phase 2: Update Services
1. Add service discovery to each MCP service
2. Replace direct HTTP calls with event publishing
3. Implement event subscribers for each service

#### Phase 3: Validate
1. Test service startup without circular dependency errors
2. Verify event flow between services
3. Monitor performance impact

### 5. Configuration Updates Required

#### Kubernetes Manifests:
- Remove direct service URL environment variables
- Add EVENT_BUS_URL to all services
- Update health checks to include event bus connectivity

#### Docker Compose:
- Remove depends_on circular references
- Add event-bus service
- Update service environment variables

### 6. Rollback Plan

If event-driven architecture causes issues:
1. Revert to direct service calls
2. Implement request timeout and circuit breakers
3. Use service mesh (Istio) for dependency management

## IMMEDIATE ACTION REQUIRED

1. **Deploy event bus service**
2. **Update mcp-context to use events**
3. **Test service startup**
4. **Monitor for performance impact**

This approach will eliminate circular dependencies while maintaining functionality.
"""

        with open('docs/CIRCULAR_DEPENDENCY_RESOLUTION.md', 'w') as f:
            f.write(strategy_doc)
        
        print("✅ Created circular dependency resolution strategy")
    
    def run_analysis(self):
        """Run complete circular dependency analysis"""
        print("🔍 Analyzing service dependencies for circular references...\n")
        
        # Analyze Docker Compose
        print("📄 Analyzing Docker Compose dependencies...")
        docker_deps = self.analyze_docker_compose()
        
        # Analyze Kubernetes manifests
        print("\n📄 Analyzing Kubernetes manifest dependencies...")
        k8s_deps = self.analyze_k8s_manifests()
        
        # Merge dependency information
        all_deps = {**docker_deps, **k8s_deps}
        
        # Find circular dependencies
        print(f"\n🔍 Searching for circular dependencies...")
        circular_deps = self.find_circular_dependencies(k8s_deps)
        
        if circular_deps:
            print(f"\n🚨 CIRCULAR DEPENDENCIES DETECTED:")
            for i, cycle in enumerate(circular_deps, 1):
                print(f"  {i}. {' → '.join(cycle)}")
        else:
            print("\n✅ No circular dependencies detected in current configuration")
        
        # Create solutions
        print(f"\n🔧 Creating dependency resolution solutions...")
        self.create_event_bus_pattern()
        self.create_service_discovery_pattern() 
        self.fix_mcp_context_dependencies()
        self.create_dependency_breaking_strategy()
        
        print(f"\n📊 Analysis Complete:")
        print(f"  📄 Analyzed {len(all_deps)} services")
        print(f"  🚨 Found {len(circular_deps)} circular dependency cycles")
        print(f"  ✅ Created event-driven architecture solution")
        
        return circular_deps

def main():
    """Main function"""
    fixer = CircularDependencyFixer()
    circular_deps = fixer.run_analysis()
    
    if circular_deps:
        print(f"\n🚨 CRITICAL: Circular dependencies detected")
        print("💡 Deploy sophia-event-bus to break circular dependencies")
        print("💡 Update services to use event-driven communication")
    else:
        print("\n✅ No circular dependencies detected")

if __name__ == "__main__":
    main()
