---
name: portainer-ports
description: Show port allocations across all Portainer-managed Docker hosts. Use when asked to check ports, port usage, what ports are in use, available ports, or port conflicts.
argument-hint: "[docker01|docker02|soho-nas|all]"
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
python3 $SKILL_DIR/portainer_ports.py $ARGUMENTS
```

3. Present the output as a formatted markdown table with columns: **Host Port**, **Container Port**, **Protocol**, **Container**, **State**. Group by host with a header for each.

4. If auth fails, tell the user:
   > Set `PORTAINER_TOKEN=ptr_...` before invoking. Generate one in Portainer: User Settings > Access Tokens.
