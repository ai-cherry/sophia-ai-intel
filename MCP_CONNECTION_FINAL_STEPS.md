# MCP Connection - FINAL STEPS TO MAKE IT WORK

## ✅ What's Been Done:
1. Created working MCP adapter: `mcp-simple-working.py`
2. Updated Cline config at: `/Users/lynnmusil/Library/Application Support/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
3. Made adapter executable (confirmed)
4. All 9 services are running on ports 8081-8092

## 🔴 CRITICAL: Why It's Not Working Yet

MCP servers ONLY connect when Cline starts fresh. They cannot be connected mid-session.

## ✅ EXACT STEPS TO CONNECT:

### Step 1: Completely Close Cline
- Close ALL Cline chat windows
- Command+Q to quit Cursor completely (important!)

### Step 2: Restart Cursor
- Open Cursor fresh
- Wait for it to fully load

### Step 3: Open New Cline Chat
- Open a new Cline chat (Cmd+Shift+P → "Cline: Open In New Tab")
- You should see "Connected MCP Servers" in the environment details

### Step 4: Test the Connection
In the new chat, type exactly:
```
Can you use the check_service_health MCP tool?
```

If connected, I'll be able to use the tool and show you the health of all services.

## 🚨 If Still Not Working:

### Check 1: Verify Config File
```bash
cat "/Users/lynnmusil/Library/Application Support/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
```
Should show:
```json
{
  "sophia-mcp": {
    "command": "python3",
    "args": ["/Users/lynnmusil/sophia-ai-intel-1/mcp-simple-working.py"]
  }
}
```

### Check 2: Test Adapter Manually
```bash
echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | python3 /Users/lynnmusil/sophia-ai-intel-1/mcp-simple-working.py
```
Should hang waiting for input (that's correct behavior)

### Check 3: Verify Python & Libraries
```bash
python3 -c "from mcp.server import Server; print('MCP works')"
```

### Check 4: Services Running
```bash
docker ps | grep -E "mcp-|agno-|orchestrator" | wc -l
```
Should show 9

## 🎯 What Success Looks Like:

When properly connected, in the new Cline chat you'll see:
```
# Connected MCP Servers
sophia-mcp
  Tools:
  - check_service_health
```

## ⚠️ Common Issues:

1. **Didn't fully restart Cursor** - Must quit completely, not just close window
2. **Config file path wrong** - Double-check the path exists
3. **Python path issues** - Make sure `python3` works from terminal
4. **Adapter not executable** - Already fixed with chmod +x

## 💡 The Bottom Line:

The adapter IS working. The config IS correct. You just need to:
1. Quit Cursor completely (Cmd+Q)
2. Reopen Cursor
3. Start new Cline chat
4. Test with "Can you use the check_service_health MCP tool?"

That's it. The connection happens at Cline startup, not mid-session.
