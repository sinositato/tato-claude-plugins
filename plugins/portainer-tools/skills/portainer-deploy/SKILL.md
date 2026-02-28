---
name: portainer-deploy
description: Deploy or update a Docker Compose stack on a homelab host via Portainer. Reads a compose file and pushes it as a Portainer stack. Use when asked to deploy, update, or push a stack.
argument-hint: "<host>/<service> [--file <path>] [--stack-name <name>]"
user-invocable: true
allowed-tools: [Bash, Read]
---

## User Input

```text
$ARGUMENTS
```

Deploy a stack to a homelab host by reading a compose file and pushing it to Portainer.

## Steps

1. Parse `$ARGUMENTS`:
   - Extract `<host>/<service>` (e.g. `docker01/grafana`)
   - Extract optional `--file <path>` (compose file path; defaults to `docker/<host>/<service>/<service>.yml`)
   - Extract optional `--stack-name <name>` override

2. Verify the compose file exists. If not, tell the user the file was not found.

3. Run:

```bash
python3 $SKILL_DIR/portainer_deploy.py <host>/<service> [--file <path>] [--stack-name <name>]
```

   Examples:
   - `python3 $SKILL_DIR/portainer_deploy.py docker01/grafana`
   - `python3 $SKILL_DIR/portainer_deploy.py docker02/test-stack --file ./tmp/test-stack.yml`

4. Report the result. Remind user to verify at http://portainer.app.soho.local

5. If auth fails, tell the user:
   > Set `PORTAINER_TOKEN=ptr_...` before invoking. Generate one in Portainer: User Settings > Access Tokens.
