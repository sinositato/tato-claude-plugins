#!/usr/bin/env python3
"""Show port allocations across Portainer-managed Docker hosts.

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
    parser = argparse.ArgumentParser(prog="portainer-ports", description="Show port allocations per Docker host")
    parser.add_argument("host", nargs="?", default="all", choices=["all", "docker01", "docker02", "soho-nas"])
    args = parser.parse_args()

    url, session = get_session()

    if args.host == "all":
        targets = ENDPOINTS
    else:
        targets = {args.host: ENDPOINTS[args.host]}

    try:
        for host, eid in targets.items():
            resp = session.get(f"{url}/api/endpoints/{eid}/docker/containers/json?all=1")
            if resp.status_code != 200:
                print(f"=== {host} === (error: HTTP {resp.status_code})")
                continue

            containers = resp.json()
            print(f"=== {host} ===")

            port_rows = []
            seen = set()
            for c in containers:
                name = c["Names"][0].lstrip("/")
                state = c["State"]
                net_mode = c.get("HostConfig", {}).get("NetworkMode", "")
                for p in c.get("Ports", []):
                    pub = p.get("PublicPort")
                    priv = p.get("PrivatePort")
                    ptype = p.get("Type", "tcp")
                    key = (pub, priv, ptype, name)
                    if pub and key not in seen:
                        seen.add(key)
                        port_rows.append((pub, priv, ptype, name, state))
                if net_mode == "host":
                    key = (None, None, "host", name)
                    if key not in seen:
                        seen.add(key)
                        port_rows.append((None, None, "host", name, state))

            if not port_rows:
                print("  (no published ports)")
            else:
                port_rows.sort(key=lambda r: (r[0] or 99999,))
                max_name = max(len(r[3]) for r in port_rows)
                for pub, priv, ptype, name, state in port_rows:
                    if pub is None:
                        print(f"  {'host':<7}  {'—':>5}  {'—':<4}  {name:<{max_name}}  {state}")
                    else:
                        print(f"  {pub:<7}  {priv:>5}  {ptype:<4}  {name:<{max_name}}  {state}")
            print()
    except requests.RequestException as e:
        print(f"Connection error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
