---
name: portainer-networks
description: Manage Docker networks across all Portainer-managed hosts. Use when asked to list networks, inspect a network, create a network, remove a network, check network configuration, or troubleshoot container connectivity.
argument-hint: "list [host] | inspect <name> [--host host] | create <name> --host host [--driver bridge] [--subnet CIDR] [--gateway IP] | remove <name> --host host"
user-invocable: true
allowed-tools: [Bash]
---

## User Input

```text
$ARGUMENTS
```

Manage Docker networks across hosts using the Portainer API.

## Steps

1. Parse `$ARGUMENTS` to determine the action and parameters:

   - **list** — `list [host-name|all]`
     - Default: all hosts
   - **inspect** — `inspect <network-name> [--host HOST]`
     - Shows driver, subnet, gateway, connected containers
   - **create** — `create <network-name> --host HOST [--driver bridge] [--subnet CIDR] [--gateway IP]`
     - `--host` is required
   - **remove** — `remove <network-name> --host HOST`
     - `--host` is required; refuses to delete default networks (bridge, host, none)

2. Build and run the command:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/portainer.py networks <action> [name] [--host HOST] [--driver DRIVER] [--subnet CIDR] [--gateway IP]
```

3. Present the output:
   - **list**: Format as a markdown table with columns **Name**, **Driver**, **Scope**, **Containers**, grouped by host. Include `[default]` tag for built-in networks.
   - **inspect**: Show network details (driver, scope, subnet, gateway) and a table of connected containers with their IPs.
   - **create/remove**: Show the success or error message.

4. If auth fails, tell the user:
   > Set `PORTAINER_TOKEN=ptr_...` before invoking. Generate one in Portainer: User Settings > Access Tokens.
