---
name: portainer-deploy
description: Deploy or update a Docker Compose stack on a Portainer-managed host. Reads a compose file and pushes it as a Portainer stack. Use when asked to deploy, update, or push a stack.
argument-hint: "<host>/<service> [--stack-name <name>]"
user-invocable: true
allowed-tools: [Bash, Read]
---

## User Input

```text
$ARGUMENTS
```

Deploy a stack to a Docker host by reading a compose file and pushing it to Portainer.

## Steps

1. Parse `$ARGUMENTS`:
   - Extract `<host>/<service>` (e.g. `docker01/grafana`)
   - Extract optional `--stack-name <name>` override

2. Verify the compose file exists at `docker/<host>/<service>/<service>.yml` relative to the current working directory. If not, tell the user the expected path.

3. Run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/portainer.py deploy <host>/<service> [--stack-name <name>]
```

   Example: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/portainer.py deploy docker01/grafana`

   Note: Set `COMPOSE_ROOT` env var if compose files are not in the current working directory.

4. Report the result.

5. If `PORTAINER_PASS` is not set, tell the user to `export PORTAINER_PASS=yourpassword` before invoking.
