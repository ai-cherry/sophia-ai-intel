# Circular Dependency Resolution Strategy

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
