# REPO AUDIT & ALIGNMENT PROMPT
**For Strategy/Architect AI Coder Swarm**

## MISSION
Examine entire Sophia AI repository. Create actionable plan to achieve:
- ONE chat interface (no multiple chat buttons/views)
- Zero mock data (everything real)
- Swarm-of-swarms pipeline working
- Left sidebar for deep views, but STILL one chat

## PHASE 1: INVENTORY (What Exists)

### Check These Files
```
services/planning/intelligent_planner.py
services/real_swarm_executor.py
apps/sophia-dashboard/src/app/page.tsx
apps/sophia-dashboard/src/app/api/chat/route.ts
apps/sophia-dashboard/src/components/*
libs/agents/swarm_manager.py
services/mcp-*/
```

### Output: repo_map.json
```json
{
  "services": [{"name":"", "path":"", "mock":true/false, "health_url":""}],
  "mcp_servers": [{"name":"", "implemented":true/false}],
  "mock_components": ["component_name"],
  "duplicate_code": [{"file1":"", "file2":"", "type":""}]
}
```

## PHASE 2: UNIFICATION PLAN

### Required Changes
1. **Chat API** - `/api/chat` returns:
```json
{
  "sections": {
    "summary": "",
    "actions": [],
    "research": [],
    "code": {},
    "github": {},
    "events": []
  }
}
```

2. **Dashboard** - ONE chat, sections render as cards
3. **WebSocket** - Auto-subscribe on swarm create
4. **Left Sidebar** - API Health, Agent Factory (but chat stays unified)

### Output: unification_plan.json
```json
{
  "api_changes": [],
  "ui_changes": [],
  "ws_subscriptions": [],
  "mock_replacements": []
}
```

## PHASE 3: IMPLEMENTATION

### Priority Order
1. Replace mock data in remaining 8 components
2. Unify chat to single interface
3. Wire WebSocket subscriptions
4. Add activity feed with real data

### Output: implementation_tasks.csv
```csv
task,file,priority,status
"Replace mock in SwarmCreator","SwarmCreator.tsx",1,"pending"
"Unify chat API","route.ts",1,"pending"
```

## PHASE 4: VALIDATION

### Tests Required
- Chat handles all intents through one box
- No mock data in prod build
- WebSocket events appear in activity feed
- API Health shows real service status

## DELIVERABLES (SHORT, NO ESSAYS)
- repo_map.json (inventory)
- unification_plan.json (changes)
- implementation_tasks.csv (action items)
- NO LONG .MD FILES
