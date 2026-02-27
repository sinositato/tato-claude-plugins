---
name: portainer-ports
description: Show port allocations across all Portainer-managed Docker hosts. Use when asked to check ports, port usage, what ports are in use, available ports, or port conflicts.
argument-hint: "[host-name|all]"
user-invocable: true
allowed-tools: [Bash]
---

## User Input

```text
$ARGUMENTS
```

Show port allocations across Docker hosts using the Portainer API.

## Steps

1. Parse `$ARGUMENTS` to determine which host(s) to query:
   - A specific host name → pass as argument
   - empty or `all` → omit argument (defaults to all)

2. Run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/portainer.py ports $ARGUMENTS
```

3. Present the output as a formatted markdown table with columns: **Host Port**, **Container Port**, **Protocol**, **Container**, **State**. Group by host with a header for each.

4. If `PORTAINER_PASS` is not set (script exits with error), tell the user:
   > Set `PORTAINER_PASS=yourpassword` before invoking, or add it to your shell environment.
