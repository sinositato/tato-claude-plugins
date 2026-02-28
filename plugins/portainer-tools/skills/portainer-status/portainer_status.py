#!/usr/bin/env python3
"""Show container health status across Portainer-managed Docker hosts.

Requires: requests
Environment: PORTAINER_TOKEN is required. PORTAINER_URL defaults to http://192.168.10.12:9000.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from portainer_common import ENDPOINTS, get_session


def format_ports(ports):
    entries = []
    for p in ports:
        pub = p.get("PublicPort")
        priv = p.get("PrivatePort")
        ptype = p.get("Type", "tcp")
        if pub:
            suffix = "" if ptype == "tcp" else f"/{ptype}"
            if pub == priv:
                entries.append(f"{pub}{suffix}")
            else:
                entries.append(f"{pub}→{priv}{suffix}")
    seen = set()
    unique = []
    for e in entries:
        if e not in seen:
            seen.add(e)
            unique.append(e)
    unique.sort(key=lambda x: int(x.split("→")[0].split("/")[0]))
    return ", ".join(unique) if unique else "—"


def main():
    parser = argparse.ArgumentParser(prog="portainer-status", description="Show container status across Docker hosts")
    parser.add_argument("host", nargs="?", default="all", choices=["all", "docker01", "docker02", "soho-nas"])
    parser.add_argument("--ports", action="store_true", help="Include port mappings in output")
    args = parser.parse_args()

    url, session = get_session()

    if args.host == "all":
        targets = ENDPOINTS
    else:
        targets = {args.host: ENDPOINTS[args.host]}

    total_running = 0
    total_stopped = 0
    total_other = 0

    try:
        for host, eid in targets.items():
            resp = session.get(f"{url}/api/endpoints/{eid}/docker/containers/json?all=1")
            if resp.status_code != 200:
                print(f"=== {host} === (error: HTTP {resp.status_code})")
                continue

            containers = resp.json()
            print(f"=== {host} ===")
            if not containers:
                print("  (no containers)")
            else:
                rows = []
                for c in sorted(containers, key=lambda x: x["Names"][0]):
                    name = c["Names"][0].lstrip("/")
                    state = c["State"]
                    status = c["Status"]
                    port_str = format_ports(c.get("Ports", []))
                    rows.append((name, state, status, port_str))
                    if state == "running":
                        total_running += 1
                    elif state in ("exited", "created"):
                        total_stopped += 1
                    else:
                        total_other += 1

                max_name = max(len(r[0]) for r in rows)
                max_state = max(len(r[1]) for r in rows)
                if args.ports:
                    max_status = max(len(r[2]) for r in rows)
                    for name, state, status, port_str in rows:
                        print(f"  {name:<{max_name}}  {state:<{max_state}}  {status:<{max_status}}  {port_str}")
                else:
                    for name, state, status, _ in rows:
                        print(f"  {name:<{max_name}}  {state:<{max_state}}  {status}")
            print()

        print(f"Summary: {total_running} running, {total_stopped} stopped, {total_other} other")
    except requests.RequestException as e:
        print(f"Connection error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
