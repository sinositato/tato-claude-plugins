#!/usr/bin/env python3
"""View container logs from a Portainer-managed Docker host.

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


def strip_docker_headers(raw):
    output = []
    i = 0
    while i + 8 <= len(raw):
        size = int.from_bytes(raw[i + 4 : i + 8], "big")
        if i + 8 + size > len(raw):
            output.append(raw[i + 8 :].decode("utf-8", errors="replace"))
            break
        output.append(raw[i + 8 : i + 8 + size].decode("utf-8", errors="replace"))
        i += 8 + size
    return "".join(output)


def main():
    parser = argparse.ArgumentParser(prog="portainer-logs", description="View container logs")
    parser.add_argument("container")
    parser.add_argument("--host", choices=["docker01", "docker02", "soho-nas"])
    parser.add_argument("--tail", type=int, default=100)
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
            sys.exit(1)

        if len(matches) > 1:
            print(f"Error: Multiple containers match '{args.container}':", file=sys.stderr)
            for eid, cname, host in matches:
                print(f"  {cname} on {host}", file=sys.stderr)
            print("Use --host to disambiguate.", file=sys.stderr)
            sys.exit(1)

        eid, cname, host = matches[0]
        resp = session.get(
            f"{url}/api/endpoints/{eid}/docker/containers/{cname}/logs",
            params={"stdout": 1, "stderr": 1, "timestamps": 1, "tail": args.tail},
        )

        if resp.status_code == 404:
            print(f"Error: Container '{cname}' not found on {host}.", file=sys.stderr)
            sys.exit(1)
        elif resp.status_code != 200:
            print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
            sys.exit(1)

        if not resp.content:
            print(f"=== Logs: {cname} ({host}) — empty ===")
        else:
            cleaned = strip_docker_headers(resp.content)
            print(f"=== Logs: {cname} ({host}) — last {args.tail} lines ===")
            print(cleaned, end="")
    except requests.RequestException as e:
        print(f"Connection error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
