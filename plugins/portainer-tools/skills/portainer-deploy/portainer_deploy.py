#!/usr/bin/env python3
"""Deploy or update a Docker Compose stack via Portainer.

Requires: requests
Environment: PORTAINER_TOKEN is required. PORTAINER_URL defaults to http://192.168.10.12:9000.
"""

import argparse
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from portainer_common import ENDPOINTS, get_session


def main():
    parser = argparse.ArgumentParser(prog="portainer-deploy", description="Deploy/update a Portainer stack")
    parser.add_argument("target", help="host/service (e.g. docker01/grafana)")
    parser.add_argument("--file", help="Path to compose file (default: docker/<host>/<service>/<service>.yml)")
    parser.add_argument("--stack-name", help="Override stack name (default: service name)")
    args = parser.parse_args()

    parts = args.target.split("/", 1)
    if len(parts) != 2:
        print("Error: Target must be <host>/<service> (e.g. docker01/grafana)", file=sys.stderr)
        sys.exit(1)

    host, service = parts
    if host not in ENDPOINTS:
        print(f"Error: Unknown host '{host}'. Use: {', '.join(ENDPOINTS.keys())}", file=sys.stderr)
        sys.exit(1)

    if args.file:
        compose_path = Path(args.file).resolve()
    else:
        compose_path = Path.cwd() / "docker" / host / service / f"{service}.yml"
    if not compose_path.exists():
        print(f"Error: Compose file not found at {compose_path}", file=sys.stderr)
        sys.exit(1)

    stack_name = args.stack_name or service
    endpoint_id = ENDPOINTS[host]
    compose_content = compose_path.read_text()

    url, session = get_session()

    try:
        # Check if stack already exists
        resp = session.get(f"{url}/api/stacks")
        if resp.status_code != 200:
            print(f"Error: Failed to list stacks (HTTP {resp.status_code})", file=sys.stderr)
            sys.exit(1)

        existing_id = None
        for stack in resp.json():
            if stack.get("Name") == stack_name:
                existing_id = stack["Id"]
                break

        if existing_id is None:
            resp = session.post(
                f"{url}/api/stacks/create/standalone/string",
                params={"endpointId": endpoint_id},
                json={"name": stack_name, "stackFileContent": compose_content},
            )
        else:
            resp = session.put(
                f"{url}/api/stacks/{existing_id}",
                params={"endpointId": endpoint_id},
                json={"stackFileContent": compose_content, "pullImage": True, "prune": False},
            )

        if resp.status_code in (200, 201) and resp.json().get("Id"):
            action = "updated" if existing_id else "created"
            print(f"Stack '{stack_name}' {action} successfully on {host}.")
        else:
            print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
            if resp.text:
                print(resp.text, file=sys.stderr)
            sys.exit(1)
    except requests.RequestException as e:
        print(f"Connection error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
