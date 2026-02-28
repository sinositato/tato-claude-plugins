---
name: portainer-logs
description: View container logs from a Portainer-managed Docker host. Use when asked to "view logs", "show logs", "tail logs", "check logs", or "read console output" for a specific container.
argument-hint: "<container-name> [on <host>] [--tail <n>]"
user-invocable: true
allowed-tools: [Bash]
---

## User Input

```text
$ARGUMENTS
```

Fetch and display logs for a named container on a Docker host via the Portainer API.

## Steps

1. Parse `$ARGUMENTS`:
   - Extract container name
   - Extract host if specified after `on` (e.g. `on docker01`)
   - Extract `--tail <n>` if present (default: 100)

2. Run:

```bash
python3 $SKILL_DIR/portainer_logs.py <container> [--host <host>] [--tail <n>]
```

   Example: `python3 $SKILL_DIR/portainer_logs.py n8n --host docker02 --tail 200`

3. Display the output in a code block.

4. If the script reports multiple matches, ask the user to specify the host.

5. If auth fails, tell the user:
   > Set `PORTAINER_TOKEN=ptr_...` before invoking. Generate one in Portainer: User Settings > Access Tokens.
