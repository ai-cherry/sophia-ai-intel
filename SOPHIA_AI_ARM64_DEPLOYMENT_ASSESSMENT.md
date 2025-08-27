# SOPHIA AI ARM64 DEPLOYMENT ASSESSMENT & WORKING PLAN

## Executive Summary
System Status: **DEPLOYMENT BLOCKED - ARM64 INCOMPATIBILITY**  
Primary Blocker: Qdrant vector database has a hard incompatibility with ARM64 architecture  
Secondary Blocker: Unknown ARM64 compatibility status for 28 other microservices  
Recommendation: **Replace Qdrant before proceeding with any deployments**

---

## 1. ARCHITECTURE & ENVIRONMENT ASSESSMENT

### 1.1 ARM64 Compatibility Status

#### Confirmed Incompatible Services
| Service | Issue | Evidence | Impact |
|---------|-------|----------|--------|
| **Qdrant** | jemalloc page size incompatibility | `jemalloc: Unsupported system page size` crash | **CRITICAL - Blocks all vector operations** |

#### Unverified Services (Need Testing)
Based on directory structure analysis, the following 29 services need ARM64 compatibility verification:

**Core Infrastructure Services:**
1. `mcp-context` - Context management service
2. `mcp-research` - Research orchestration
3. `mcp-agents` - Agent management
4. `mcp-business` - Business logic service
5. `mcp-github` - GitHub integration
6. `mcp-hubspot` - HubSpot CRM integration
7. `mcp-salesforce` - Salesforce integration
8. `mcp-gong` - Gong call analytics
9. `mcp-slack` - Slack messaging integration
10. `mcp-apollo` - Apollo GraphQL service
11. `mcp-lambda` - Lambda Labs integration

**Agno Services:**
12. `agno-coordinator` - TypeScript/Node.js orchestrator
13. `agno-teams` - Team management service
14. `agno-wrappers` - Service wrappers

**Supporting Services:**
15. `orchestrator` - Main orchestration service
16. `sonic-ai` - Audio processing service
17. `enrichment-mcp` - Data enrichment
18. `analytics-mcp` - Analytics processing
19. `crm-mcp` - CRM integration
20. `comms-mcp` - Communications hub
21. `projects-mcp` - Project management
22. `support-mcp` - Support ticket handling

**Data/ML Services:**
23. `context-api` - Context API service
24. `vector-indexer` - Vector indexing service
25. `mem0` - Memory service
26. `portkey-llm` - LLM routing service
27. `swarm` - Agent swarm orchestration

**Frontend Services:**
28. `sophia-dashboard` - Next.js dashboard
29. `agentic` - Agentic framework service

### 1.2 Container Image Compatibility Analysis

**Python Services (FastAPI-based):**
- Base Image: Likely `python:3.11-slim` or similar
- ARM64 Status: ✅ **Usually Compatible** (Python has good ARM64 support)
- Risk Level: LOW

**Node.js/TypeScript Services:**
- Base Image: Likely `node:18-alpine` or similar
- ARM64 Status: ✅ **Usually Compatible** (Node.js has excellent ARM64 support)
- Risk Level: LOW

**Database/Infrastructure:**
- Redis: ✅ **Compatible** (Official ARM64 images available)
- PostgreSQL/Neon: ✅ **Compatible** (ARM64 supported)
- Qdrant: ❌ **INCOMPATIBLE** (jemalloc page size issue)
- Risk Level: CRITICAL for Qdrant

### 1.3 Resource Distribution Requirements

**Estimated Resource Allocation:**
```yaml
Total Cluster Resources Available:
- CPU: ~28 cores (assuming 8-core nodes × 3-4 nodes)
- Memory: ~112 GB (assuming 32GB per node)
- Storage: ~1-2 TB NVMe

Per-Service Recommendations:
- Small Services (APIs): 0.1-0.5 CPU, 256-512Mi Memory
- Medium Services (Processing): 0.5-1.0 CPU, 512Mi-1Gi Memory  
- Large Services (ML/Vector): 1.0-2.0 CPU, 1-4Gi Memory
- Databases: 2.0-4.0 CPU, 4-8Gi Memory
```

---

## 2. CURRENT BLOCKERS (PRIORITIZED)

### Priority 1: CRITICAL - Must Fix First
1. **Qdrant ARM64 Incompatibility**
   - **Impact:** Blocks ALL vector search functionality
   - **Solution Options:**
     
   **Option A: Replace with Weaviate** ⭐ RECOMMENDED
   ```yaml
   Pros:
   - Native ARM64 support
   - Drop-in replacement for vector search
   - Similar API to Qdrant
   - Production-ready
   Cons:
   - Requires code changes in vector-indexer service
   - Different query syntax
   ```
   
   **Option B: Replace with ChromaDB**
   ```yaml
   Pros:
   - Python-native, works on ARM64
   - Simple integration
   - Lightweight
   Cons:
   - Less performant than Qdrant
   - Fewer advanced features
   ```
   
   **Option C: Use Pinecone (Cloud)**
   ```yaml
   Pros:
   - No infrastructure management
   - Highly scalable
   - Great performance
   Cons:
   - External dependency
   - Additional cost
   - Network latency
   ```

2. **GitHub Container Registry Credentials**
   - **Format Required:**
   ```bash
   GITHUB_USERNAME="your-github-username"
   GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"  # Personal Access Token with packages:read
   GITHUB_EMAIL="your-email@example.com"
   ```
   - **Creation Steps:**
   1. Go to GitHub Settings → Developer Settings → Personal Access Tokens
   2. Generate token with `read:packages` permission
   3. Update `k8s-deploy/scripts/create-image-pull-secret.sh`

### Priority 2: HIGH - Fix Before Full Deployment
3. **Secret Validation**
   - All secrets currently use placeholder values
   - Need real API keys for: OpenAI, HubSpot, Salesforce, Gong, GitHub
   - PostgreSQL/Neon connection strings need real endpoints

4. **ARM64 Image Building**
   - Need to rebuild all custom images for ARM64 architecture
   - Use multi-arch builds: `docker buildx build --platform linux/arm64`

### Priority 3: MEDIUM - Can Deploy Without
5. **Monitoring Stack ARM64 Compatibility**
   - Prometheus: ✅ Compatible
   - Grafana: ✅ Compatible  
   - Alertmanager: ✅ Compatible

---

## 3. DEPLOYMENT STRATEGY

### Phase 0: Pre-flight Checks (MUST DO FIRST)
```bash
# 1. Verify SSH tunnel is active
ssh -i lambda_kube_ssh_key.pem -L 8443:192.222.51.223:6443 ubuntu@192.222.51.223

# 2. Verify kubectl access
export KUBECONFIG=./kubeconfig_lambda.yaml
kubectl get nodes

# 3. Check cluster resources
kubectl top nodes
```

### Phase 1: Replace Qdrant with ARM64-Compatible Alternative
```bash
# 1. Remove existing Qdrant deployment
kubectl delete deployment qdrant -n sophia-ai
kubectl delete service qdrant -n sophia-ai
kubectl delete pvc qdrant-storage -n sophia-ai

# 2. Deploy Weaviate (recommended)
cat > weaviate-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: weaviate
  namespace: sophia-ai
spec:
  replicas: 1
  selector:
    matchLabels:
      app: weaviate
  template:
    metadata:
      labels:
        app: weaviate
    spec:
      containers:
      - name: weaviate
        image: semitechnologies/weaviate:1.24.1
        ports:
        - containerPort: 8080
        env:
        - name: PERSISTENCE_DATA_PATH
          value: "/var/lib/weaviate"
        - name: AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED
          value: "true"
        - name: DEFAULT_VECTORIZER_MODULE
          value: "none"
        volumeMounts:
        - name: weaviate-data
          mountPath: /var/lib/weaviate
      volumes:
      - name: weaviate-data
        persistentVolumeClaim:
          claimName: weaviate-storage
---
apiVersion: v1
kind: Service
metadata:
  name: weaviate
  namespace: sophia-ai
spec:
  ports:
  - port: 8080
    targetPort: 8080
  selector:
    app: weaviate
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: weaviate-storage
  namespace: sophia-ai
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
EOF

kubectl apply -f weaviate-deployment.yaml
```

### Phase 2: Deploy Core Infrastructure
```bash
# Deploy in this exact order:

# 1. Redis Event Bus (Required by all services)
kubectl apply -f k8s-deploy/manifests/redis.yaml

# 2. ConfigMaps (Configuration for all services)
kubectl apply -f k8s-deploy/manifests/configmap.yaml

# 3. Apply all secrets (with real values)
python3 k8s-deploy/scripts/apply_secrets.py

# 4. Verify infrastructure
kubectl get pods -n sophia-ai | grep -E "redis|weaviate"
```

### Phase 3: Deploy Services by Dependency Order

**Group 1: Independent Services (Can deploy in parallel)**
```bash
# These have no dependencies on other custom services
kubectl apply -f k8s-deploy/manifests/mcp-github.yaml
kubectl apply -f k8s-deploy/manifests/mcp-hubspot.yaml
kubectl apply -f k8s-deploy/manifests/mcp-salesforce.yaml
kubectl apply -f k8s-deploy/manifests/mcp-gong.yaml
kubectl apply -f k8s-deploy/manifests/mcp-slack.yaml
```

**Group 2: Core Services (Deploy sequentially)**
```bash
# Order matters here
kubectl apply -f k8s-deploy/manifests/mcp-context.yaml    # Needs vector DB
kubectl apply -f k8s-deploy/manifests/mcp-research.yaml   # Needs context
kubectl apply -f k8s-deploy/manifests/mcp-agents.yaml     # Needs research
kubectl apply -f k8s-deploy/manifests/mcp-business.yaml   # Needs agents
```

**Group 3: Orchestration Layer**
```bash
kubectl apply -f k8s-deploy/manifests/agno-coordinator.yaml
kubectl apply -f k8s-deploy/manifests/orchestrator.yaml
kubectl apply -f k8s-deploy/manifests/agno-teams.yaml
```

**Group 4: Frontend & Supporting Services**
```bash
kubectl apply -f k8s-deploy/manifests/sophia-dashboard.yaml
kubectl apply -f k8s-deploy/manifests/monitoring-stack.yaml
```

### Phase 4: Verification & Rollback Points

**Rollback Strategy:**
```bash
# Save current state before each phase
kubectl get all -n sophia-ai -o yaml > backup-phase-X.yaml

# If issues occur, rollback:
kubectl delete -f <failed-manifest>
kubectl apply -f backup-phase-X.yaml
```

---

## 4. VALIDATION PLAN

### 4.1 Service Health Verification

**Health Check Script:**
```bash
#!/bin/bash
# save as verify-health.sh

NAMESPACE="sophia-ai"
SERVICES=(
    "mcp-context:8000"
    "mcp-research:8001"
    "mcp-agents:8002"
    "mcp-business:8003"
    "mcp-github:8004"
    "mcp-hubspot:8005"
    "mcp-salesforce:8006"
    "mcp-gong:8007"
    "mcp-slack:8008"
    "redis:6379"
    "weaviate:8080"
)

for SERVICE in "${SERVICES[@]}"; do
    NAME="${SERVICE%%:*}"
    PORT="${SERVICE##*:}"
    
    # Port-forward and check health
    kubectl port-forward -n $NAMESPACE svc/$NAME $PORT:$PORT &
    PF_PID=$!
    sleep 2
    
    # Check health endpoint
    if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        echo "✅ $NAME is healthy"
    else
        echo "❌ $NAME health check failed"
    fi
    
    kill $PF_PID 2>/dev/null
done
```

### 4.2 Test Endpoints

**Critical Functionality Tests:**
```python
# save as test-critical.py
import requests
import json

tests = [
    {
        "name": "Vector Search (Weaviate)",
        "url": "http://localhost:8080/v1/objects",
        "method": "GET",
        "expected_status": 200
    },
    {
        "name": "Context Service",
        "url": "http://localhost:8000/health",
        "method": "GET",
        "expected_status": 200
    },
    {
        "name": "Research Service",
        "url": "http://localhost:8001/health",
        "method": "GET",
        "expected_status": 200
    }
]

for test in tests:
    try:
        response = requests.request(test["method"], test["url"])
        if response.status_code == test["expected_status"]:
            print(f"✅ {test['name']}: PASS")
        else:
            print(f"❌ {test['name']}: FAIL (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ {test['name']}: ERROR ({str(e)})")
```

### 4.3 Log Indicators

**Success Indicators:**
```bash
# Look for these in pod logs
kubectl logs -n sophia-ai <pod-name> | grep -E "Ready|Started|Listening|Connected"

SUCCESS_PATTERNS=(
    "INFO:     Application startup complete"
    "INFO:     Uvicorn running on"
    "Connected to Redis"
    "Connected to database"
    "Health check passed"
)
```

**Failure Indicators:**
```bash
# These indicate problems
FAILURE_PATTERNS=(
    "Connection refused"
    "Authentication failed"
    "jemalloc"  # Qdrant ARM64 issue
    "Cannot allocate memory"
    "Permission denied"
    "Module not found"
    "ImportError"
)
```

---

## 5. IMMEDIATE ACTION PLAN

### Today's Priority Actions:

1. **STOP all Qdrant troubleshooting** ✅ Already acknowledged
2. **Choose Qdrant replacement** (Recommend Weaviate)
3. **Get real GitHub registry credentials**
4. **Deploy Weaviate on ARM64**
5. **Update vector-indexer service code for new vector DB**
6. **Begin sequential service deployment**

### Success Criteria:
- [ ] Weaviate running successfully on ARM64
- [ ] At least 5 core services deployed and healthy
- [ ] Health endpoints responding
- [ ] No CrashLoopBackOff pods
- [ ] Frontend accessible

### Time Estimate:
- Qdrant replacement: 2-3 hours
- Service deployment: 4-6 hours
- Testing & validation: 2-3 hours
- **Total: 8-12 hours for basic operational system**

---

## 6. RISK MITIGATION

### High-Risk Areas:
1. **Vector DB Migration**: Code changes required in multiple services
2. **Secret Management**: Wrong secrets = instant failures
3. **Service Dependencies**: Wrong order = cascade failures

### Mitigation Strategies:
1. **Test locally first**: Use docker-compose with ARM64 images
2. **Deploy incrementally**: One service at a time with validation
3. **Monitor actively**: Watch logs during each deployment
4. **Maintain SSH tunnel**: Keep connection stable throughout

---

## CONCLUSION

The primary blocker is Qdrant's ARM64 incompatibility. **No further deployment should proceed until this is resolved.** Once Weaviate (or alternative) is deployed and verified, the remaining services can be deployed systematically.

The good news: Most Python and Node.js services should work on ARM64 without issues. The deployment can proceed once the vector database blocker is cleared.

**Next Immediate Step:** Deploy Weaviate and verify it works on ARM64 Lambda Labs cluster.
