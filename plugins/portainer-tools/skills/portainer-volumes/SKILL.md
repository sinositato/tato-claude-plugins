---
name: portainer-volumes
description: Manage Docker volumes across all Portainer-managed hosts. Use when asked to list volumes, inspect a volume, create a volume, remove a volume, check volume usage, or troubleshoot storage.
argument-hint: "list [host] | inspect <name> [--host host] | create <name> --host host [--driver local] [--opt key=value] | remove <name> --host host"
user-invocable: true
allowed-tools: [Bash]
---

## User Input

```text
$ARGUMENTS
```

Manage Docker volumes across hosts using the Portainer API.

## Steps

1. Parse `$ARGUMENTS` to determine the action and parameters:

   - **list** — `list [docker01|docker02|soho-nas|all]`
     - Default: all hosts
   - **inspect** — `inspect <volume-name> [--host HOST]`
     - Shows driver, mountpoint, scope, labels, options, size if available
   - **create** — `create <volume-name> --host HOST [--driver local] [--opt key=value]`
     - `--host` is required; `--opt` is repeatable for driver options
   - **remove** — `remove <volume-name> --host HOST`
     - `--host` is required

2. Build and run the command:

```bash
python3 $SKILL_DIR/portainer_volumes.py <action> [name] [--host HOST] [--driver DRIVER] [--opt key=value]
```

3. Present the output:
   - **list**: Format as a markdown table with columns **Name**, **Driver**, **Mountpoint**, grouped by host.
   - **inspect**: Show volume details (driver, mountpoint, scope, created date, labels, options, size/ref count if available).
   - **create/remove**: Show the success or error message.

4. If auth fails, tell the user:
   > Set `PORTAINER_TOKEN=ptr_...` before invoking. Generate one in Portainer: User Settings > Access Tokens.
