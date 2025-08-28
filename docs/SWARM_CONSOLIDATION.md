# Sophia AI Swarm Consolidation Plan

## Completed Actions

### 1. UI Cleanup
- ✅ Removed old `ChatInterface.tsx` (313 lines of monolithic code)
- ✅ Confirmed new dashboard (`page.tsx`) with sidebar navigation is active
- ✅ Added version markers to verify correct deployment

### 2. Stub/Mock Removal
- ✅ Deprecated `agentic/coding_swarms/main.py` (mock implementation)
- ✅ Deprecated `agentic/research_swarms/trend_swarm.py` (stub)

### 3. Canonical Implementations

#### Primary Swarm Architecture (USE THESE):
- **SwarmManager**: `libs/agents/swarm_manager.py` - Advanced multi-agent orchestration
- **Deep Research**: `agentic/swarms/research/deep_research_swarm.py` - Real research swarm
- **Coding Swarm**: `agentic/coding_swarms/dev_swarm.py` - Agno-based coding specialists

#### Three-Planner System:
1. **Cutting-Edge Planner** - Explores experimental solutions
2. **Conservative Planner** - Focuses on stability
3. **Synthesis Planner** - Mediates and synthesizes final plan

### 4. Service Consolidation Strategy

The duplicate services (`agents/swarm/app.py` and `mcp/agents-swarm/app.py`) should be consolidated into a single service that:

1. Delegates to `libs/agents/swarm_manager.py` for orchestration
2. Exposes unified endpoints:
   - `/swarms` - List active swarms
   - `/swarms/create` - Create new swarm
   - `/swarms/{id}/status` - Get swarm status
   - `/agents` - List available agents
   - `/tasks` - Submit tasks to swarms

### 5. Frontend Integration Points

The dashboard should integrate:
- **Agent Factory** - UI for creating/configuring agents
- **Swarm Monitor** - Real-time swarm status and task progress
- **Plan Viewer** - Shows cutting-edge, conservative, and synthesized plans
- **Repository Context** - File tree and code analysis

### 6. Next Steps

1. Create unified swarm service API
2. Wire dashboard to use SwarmManager
3. Implement plan visualization in UI
4. Add Agno memory/reasoning integration
5. Connect to GitHub for automated PRs

## Architecture Diagram

```
┌─────────────────┐
│   Dashboard     │
│  (page.tsx)     │
└────────┬────────┘
         │
┌────────▼────────┐
│  Swarm Service  │ (Unified API)
└────────┬────────┘
         │
┌────────▼────────┐
│  SwarmManager   │ (libs/agents/swarm_manager.py)
└────────┬────────┘
         │
    ┌────┴────┬──────────┬─────────┐
    │         │          │         │
┌───▼──┐ ┌───▼──┐ ┌─────▼──┐ ┌───▼──┐
│Cutting│ │Conserv│ │Synthesis│ │Code  │
│Edge   │ │ative  │ │Planner  │ │Kraken│
└──────┘ └──────┘ └────────┘ └──────┘
```

## Benefits of Consolidation

1. **Single Source of Truth** - No more confusion about which implementation to use
2. **Consistent API** - All swarm operations go through one service
3. **Better Maintenance** - Updates in one place affect entire system
4. **Clear Architecture** - Three-planner system is now canonical
5. **Enhanced UI** - Dashboard can show all swarm operations in one place