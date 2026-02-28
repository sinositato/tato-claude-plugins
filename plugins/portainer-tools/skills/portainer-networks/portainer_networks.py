#!/usr/bin/env python3
"""Manage Docker networks across Portainer-managed hosts.

Requires: requests
Environment: PORTAINER_TOKEN is required. PORTAINER_URL defaults to http://192.168.10.12:9000.
"""

import argparse
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from portainer_common import ENDPOINTS, get_session

DEFAULT_NETWORKS = {"bridge", "host", "none"}


def find_network(session, url, name, endpoint_ids):
    matches = []
    host_by_id = {v: k for k, v in ENDPOINTS.items()}
    for eid in endpoint_ids:
        resp = session.get(f"{url}/api/endpoints/{eid}/docker/networks")
        if resp.status_code != 200:
            continue
        for n in resp.json():
            nname = n["Name"]
            if name == nname or name in nname:
                matches.append((eid, n["Id"], nname, host_by_id.get(eid, f"endpoint-{eid}")))
    return matches


def cmd_list(args, session, url):
    if args.host == "all":
        targets = ENDPOINTS
    else:
        targets = {args.host: ENDPOINTS[args.host]}

    total_default = 0
    total_user = 0

    for host, eid in targets.items():
        resp = session.get(f"{url}/api/endpoints/{eid}/docker/networks")
        if resp.status_code != 200:
            print(f"=== {host} === (error: HTTP {resp.status_code})")
            continue

        networks = resp.json()
        print(f"=== {host} ===")
        if not networks:
            print("  (no networks)")
        else:
            rows = []
            for n in sorted(networks, key=lambda x: x["Name"]):
                name = n["Name"]
                driver = n.get("Driver", "—")
                scope = n.get("Scope", "—")
                containers = len(n.get("Containers", {}) or {})
                is_default = name in DEFAULT_NETWORKS
                tag = "  [default]" if is_default else ""
                rows.append((name, driver, scope, containers, tag))
                if is_default:
                    total_default += 1
                else:
                    total_user += 1

            max_name = max(len(r[0]) for r in rows)
            max_driver = max(len(r[1]) for r in rows)
            max_scope = max(len(r[2]) for r in rows)
            print(f"  {'NAME':<{max_name}}  {'DRIVER':<{max_driver}}  {'SCOPE':<{max_scope}}  CONTAINERS")
            for name, driver, scope, containers, tag in rows:
                print(f"  {name:<{max_name}}  {driver:<{max_driver}}  {scope:<{max_scope}}  {containers}{tag}")
        print()

    total = total_default + total_user
    print(f"Summary: {total} networks across {len(targets)} host(s) ({total_default} default, {total_user} user-created)")


def cmd_inspect(args, session, url):
    if not args.name:
        print("Error: Network name is required for inspect.", file=sys.stderr)
        sys.exit(1)

    if args.host:
        endpoint_ids = [ENDPOINTS[args.host]]
    else:
        endpoint_ids = list(ENDPOINTS.values())

    matches = find_network(session, url, args.name, endpoint_ids)

    if not matches:
        print(f"Error: Network '{args.name}' not found.", file=sys.stderr)
        sys.exit(1)
    if len(matches) > 1:
        exact = [m for m in matches if m[2] == args.name]
        if len(exact) == 1:
            matches = exact
        else:
            print(f"Error: Multiple networks match '{args.name}':", file=sys.stderr)
            for _, _, nname, host in matches:
                print(f"  {nname} on {host}", file=sys.stderr)
            print("Use --host to disambiguate.", file=sys.stderr)
            sys.exit(1)

    eid, nid, nname, host = matches[0]
    resp = session.get(f"{url}/api/endpoints/{eid}/docker/networks/{nid}")
    if resp.status_code != 200:
        print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
        sys.exit(1)

    net = resp.json()
    print(f"=== Network: {net['Name']} ({host}) ===")
    print(f"Driver:   {net.get('Driver', '—')}")
    print(f"Scope:    {net.get('Scope', '—')}")

    ipam_configs = (net.get("IPAM") or {}).get("Config") or []
    if ipam_configs:
        cfg = ipam_configs[0]
        print(f"Subnet:   {cfg.get('Subnet', '—')}")
        print(f"Gateway:  {cfg.get('Gateway', '—')}")

    containers = net.get("Containers") or {}
    if containers:
        print()
        print("Connected containers:")
        max_cname = max(len(c.get("Name", "")) for c in containers.values())
        for cid, c in sorted(containers.items(), key=lambda x: x[1].get("Name", "")):
            cname = c.get("Name", cid[:12])
            ipv4 = c.get("IPv4Address", "—")
            print(f"  {cname:<{max_cname}}  {ipv4}")
    else:
        print("\nNo connected containers.")


def cmd_create(args, session, url):
    if not args.name:
        print("Error: Network name is required for create.", file=sys.stderr)
        sys.exit(1)
    if not args.host:
        print("Error: --host is required for create.", file=sys.stderr)
        sys.exit(1)

    eid = ENDPOINTS[args.host]
    body = {"Name": args.name, "Driver": args.driver or "bridge", "CheckDuplicate": True}
    if args.subnet or args.gateway:
        ipam_config = {}
        if args.subnet:
            ipam_config["Subnet"] = args.subnet
        if args.gateway:
            ipam_config["Gateway"] = args.gateway
        body["IPAM"] = {"Config": [ipam_config]}

    resp = session.post(f"{url}/api/endpoints/{eid}/docker/networks/create", json=body)
    if resp.status_code == 201 or (resp.status_code == 200 and resp.json().get("Id")):
        print(f"Network '{args.name}' created on {args.host}.")
    else:
        print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
        if resp.text:
            print(resp.text, file=sys.stderr)
        sys.exit(1)


def cmd_remove(args, session, url):
    if not args.name:
        print("Error: Network name is required for remove.", file=sys.stderr)
        sys.exit(1)
    if not args.host:
        print("Error: --host is required for remove (safety: no cross-host matching for destructive ops).", file=sys.stderr)
        sys.exit(1)
    if args.name in DEFAULT_NETWORKS:
        print(f"Error: Cannot remove default network '{args.name}'.", file=sys.stderr)
        sys.exit(1)

    eid = ENDPOINTS[args.host]
    matches = find_network(session, url, args.name, [eid])

    if not matches:
        print(f"Error: Network '{args.name}' not found on {args.host}.", file=sys.stderr)
        sys.exit(1)
    if len(matches) > 1:
        exact = [m for m in matches if m[2] == args.name]
        if len(exact) == 1:
            matches = exact
        else:
            print(f"Error: Multiple networks match '{args.name}' on {args.host}:", file=sys.stderr)
            for _, _, nname, _ in matches:
                print(f"  {nname}", file=sys.stderr)
            sys.exit(1)

    _, nid, nname, host = matches[0]
    resp = session.delete(f"{url}/api/endpoints/{eid}/docker/networks/{nid}")
    if resp.status_code == 204:
        print(f"Network '{nname}' removed from {host}.")
    else:
        print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
        if resp.text:
            print(resp.text, file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="portainer-networks", description="Manage Docker networks")
    parser.add_argument("action", choices=["list", "inspect", "create", "remove"])
    parser.add_argument("name", nargs="?", help="Network name (required for inspect/create/remove)")
    parser.add_argument("--host", default="all", choices=["all", "docker01", "docker02", "soho-nas"])
    parser.add_argument("--driver", default="bridge", help="Network driver (default: bridge)")
    parser.add_argument("--subnet", help="Subnet CIDR (e.g. 172.20.0.0/16)")
    parser.add_argument("--gateway", help="Gateway IP (e.g. 172.20.0.1)")
    args = parser.parse_args()

    url, session = get_session()

    handlers = {"list": cmd_list, "inspect": cmd_inspect, "create": cmd_create, "remove": cmd_remove}

    try:
        handlers[args.action](args, session, url)
    except requests.RequestException as e:
        print(f"Connection error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
