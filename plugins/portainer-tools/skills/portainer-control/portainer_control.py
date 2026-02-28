#!/usr/bin/env python3
"""Start, stop, or restart a Docker container via Portainer.

Requires: requests
Environment: PORTAINER_TOKEN is required. PORTAINER_URL defaults to http://192.168.10.12:9000.
"""

import argparse
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from portainer_common import ENDPOINTS, get_session


def find_container(session, url, name, endpoint_ids):
    matches = []
    host_by_id = {v: k for k, v in ENDPOINTS.items()}
    for eid in endpoint_ids:
        resp = session.get(f"{url}/api/endpoints/{eid}/docker/containers/json?all=1")
        if resp.status_code != 200:
            continue
        for c in resp.json():
            cname = c["Names"][0].lstrip("/")
            if name == cname or name in cname:
                matches.append((eid, cname, host_by_id.get(eid, f"endpoint-{eid}")))
    return matches


def main():
    parser = argparse.ArgumentParser(prog="portainer-control", description="Start/stop/restart a container")
    parser.add_argument("action", choices=["start", "stop", "restart"])
    parser.add_argument("container")
    parser.add_argument("--host", choices=["docker01", "docker02", "soho-nas"])
    args = parser.parse_args()

    url, session = get_session()

    if args.host:
        endpoint_ids = [ENDPOINTS[args.host]]
    else:
        endpoint_ids = list(ENDPOINTS.values())

    try:
        matches = find_container(session, url, args.container, endpoint_ids)

        if not matches:
            print(f"Error: Container '{args.container}' not found.", file=sys.stderr)
            print("Run: /portainer-status to check container names", file=sys.stderr)
            sys.exit(1)

        if len(matches) > 1:
            print(f"Error: Multiple containers match '{args.container}':", file=sys.stderr)
            for eid, cname, host in matches:
                print(f"  {cname} on {host}", file=sys.stderr)
            print("Use --host to disambiguate.", file=sys.stderr)
            sys.exit(1)

        eid, cname, host = matches[0]
        resp = session.post(
            f"{url}/api/endpoints/{eid}/docker/containers/{cname}/{args.action}",
            headers={"Content-Type": "application/json"},
        )

        if resp.status_code == 204:
            print(f"{cname} {args.action} completed successfully on {host}.")
        elif resp.status_code == 304:
            print(f"{cname} is already in the requested state on {host}.")
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
