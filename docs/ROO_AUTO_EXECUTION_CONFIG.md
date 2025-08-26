# Configuring Roo/Cider for Automatic Command Execution

## Option 1: VSCode Settings (Recommended)

Add these settings to your VSCode configuration:

### User Settings (applies globally)
1. Open VSCode Settings (Cmd/Ctrl + ,)
2. Search for "Cider" or "Roo"
3. Look for settings related to "auto approval" or "command execution"

### Workspace Settings (project-specific)
Create or update `.vscode/settings.json`:

```json
{
  "cider.autoApproveCommands": true,
  "cider.autoApproveFileChanges": true,
  "cider.autoApproveBrowserActions": false,
  "cider.requireApproval": false
}
```

## Option 2: Cider Configuration File

Create `.cider/config.json` in your project root:

```json
{
  "autoApprove": {
    "commands": true,
    "fileOperations": true,
    "browserActions": false
  },
  "safety": {
    "requireApproval": false,
    "dangerousCommandsRequireApproval": true
  }
}
```

## Option 3: Environment Variables

Set these environment variables before starting VSCode:

```bash
export CIDER_AUTO_APPROVE=true
export CIDER_AUTO_APPROVE_COMMANDS=true
export CIDER_AUTO_APPROVE_FILES=true
```

## Option 4: Launch Configuration

Add to `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Roo Auto Mode",
      "type": "node",
      "request": "launch",
      "env": {
        "CIDER_AUTO_APPROVE": "true"
      }
    }
  ]
}
```

## Security Considerations

⚠️ **WARNING**: Auto-approval can be dangerous!

### Recommended Safe Configuration:
```json
{
  "cider.autoApproveCommands": true,
  "cider.autoApproveFileChanges": true,
  "cider.autoApproveBrowserActions": false,
  "cider.dangerousCommands": [
    "rm -rf",
    "format",
    "sudo"
  ],
  "cider.requireApprovalForDangerousCommands": true
}
```

### Best Practices:
1. **Never auto-approve in production repositories**
2. **Keep browser actions manual** (they can navigate to malicious sites)
3. **Maintain a dangerous commands list** that always requires approval
4. **Use project-specific settings** rather than global
5. **Review command history regularly**

## Quick Setup for This Project

For the sophia-ai-intel project, create `.vscode/settings.json`:

```json
{
  "cider.autoApproveCommands": true,
  "cider.autoApproveFileChanges": true,
  "cider.autoApproveBrowserActions": false,
  "cider.requireApprovalForDangerousCommands": true,
  "cider.dangerousCommands": [
    "rm -rf /",
    "sudo rm",
    "docker-compose secrets",
    "git push --force"
  ]
}
```

This will:
- ✅ Auto-approve normal commands
- ✅ Auto-approve file changes
- ❌ Keep browser actions manual
- ⚠️ Require approval for dangerous commands

## Command Line Flag

You can also start Roo with auto-approval:

```bash
# If using Roo CLI directly
roo --auto-approve

# Or with specific approvals
roo --auto-approve-commands --auto-approve-files
```

## Verifying Configuration

To check if auto-approval is working:
1. Ask Roo to run a simple command like `ls`
2. It should execute without the approval dialog
3. Check the Roo output panel for confirmation

## Reverting to Manual Approval

To go back to manual approval:
```json
{
  "cider.autoApproveCommands": false,
  "cider.autoApproveFileChanges": false
}
```

Or simply delete the settings file.