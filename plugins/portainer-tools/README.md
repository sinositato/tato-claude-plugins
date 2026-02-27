# Portainer Tools

Manage Docker containers across Portainer-managed hosts from Claude Code — check status, view logs, control containers, and deploy stacks.

## Skills

| Skill | Command | Description |
|-------|---------|-------------|
| Status | `/portainer-status [host]` | Show container health across all hosts |
| Control | `/portainer-control restart grafana` | Start, stop, or restart a container |
| Logs | `/portainer-logs n8n --tail 50` | View container stdout/stderr logs |
| Deploy | `/portainer-deploy docker01/grafana` | Deploy or update a Portainer stack |

## Setup

### Required

```bash
export PORTAINER_PASS=yourpassword
```

### Optional

```bash
export PORTAINER_URL=http://192.168.10.12:9000   # default
export PORTAINER_USER=tato                         # default
export COMPOSE_ROOT=/path/to/repo                  # for deploy; default: cwd
```

### Custom Endpoints

By default, the plugin is configured for three hosts:

| Host | Endpoint ID |
|------|-------------|
| docker01 | 7 |
| docker02 | 8 |
| soho-nas | 9 |

Override with a JSON map:

```bash
export PORTAINER_ENDPOINTS='{"myhost1": 1, "myhost2": 2}'
```

## Dependencies

- Python 3
- `requests` (`pip install requests`)

## Usage Examples

```bash
# Check all hosts
/portainer-status

# Check a specific host
/portainer-status docker02

# View last 20 lines of grafana logs
/portainer-logs grafana --tail 20

# Restart a container
/portainer-control restart n8n on docker02

# Deploy a stack from a compose file
/portainer-deploy docker01/prometheus
```
