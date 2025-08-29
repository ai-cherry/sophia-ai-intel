# UNIFIED SOPHIA FIX - NO BS

## AUDIT RESULTS
- **Tech Debt Score: 170** (HIGH)
- **9 components** using mock data
- **10 services** not running
- **100+ duplicate env keys**

## PRIORITY FIXES

### 1. ONE CHAT API (Replace ALL mock endpoints)
```typescript
// /api/chat/route.ts - THE ONLY ENDPOINT
export async function POST(req) {
  const { message } = await req.json()
  
  // Route internally based on intent
  const intent = detectIntent(message)
  
  switch(intent) {
    case 'research':
      return await mcp_research.search(message)
    case 'deploy_agent':
      return await swarm_api.create(message)
    case 'code_review':
      return await mcp_github.analyze(message)
    case 'commit':
      return await github_api.createPR(message)
    default:
      return await sophia_brain.process(message)
  }
}
```

### 2. COMPONENTS TO DELETE/REPLACE
- `AgentManagement.tsx` → DELETE (use chat)
- `CommandPalette.tsx` → DELETE (use chat)  
- `SwarmManager.tsx` → REPLACE with real API
- `AgentMonitoring.tsx` → REPLACE with WebSocket

### 3. SERVICES TO FIX
```bash
# Dead services (not running)
- agno-coordinator (8080)
- orchestrator (8088)
- mcp-agents (8000)
- mcp-context (8081)
- mcp-github (8082)
```

### 4. LEFT SIDEBAR STRUCTURE
```
Chat (/)              # ONE chat box
API Health (/health)  # Real service status
Agents (/agents)      # Live swarm monitor
Code (/code)          # Real GitHub diffs
Metrics (/metrics)    # Real Prometheus
```

## IMPLEMENTATION

Day 1: Delete all mock components
Day 2: Wire unified /api/chat  
Day 3: Add WebSocket subscriptions
Day 4: Test everything works
Day 5: Ship it