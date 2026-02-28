#!/usr/bin/env python3
"""Manage Docker volumes across Portainer-managed hosts.

Requires: requests
Environment: PORTAINER_TOKEN is required. PORTAINER_URL defaults to http://192.168.10.12:9000.
"""

import argparse
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from portainer_common import ENDPOINTS, get_session


def find_volume(session, url, name, endpoint_ids):
    matches = []
    host_by_id = {v: k for k, v in ENDPOINTS.items()}
    for eid in endpoint_ids:
        resp = session.get(f"{url}/api/endpoints/{eid}/docker/volumes")
        if resp.status_code != 200:
            continue
        for v in resp.json().get("Volumes", []) or []:
            vname = v["Name"]
            if name == vname or name in vname:
                matches.append((eid, vname, host_by_id.get(eid, f"endpoint-{eid}")))
    return matches


def cmd_list(args, session, url):
    if args.host == "all":
        targets = ENDPOINTS
    else:
        targets = {args.host: ENDPOINTS[args.host]}

    total = 0
    for host, eid in targets.items():
        resp = session.get(f"{url}/api/endpoints/{eid}/docker/volumes")
        if resp.status_code != 200:
            print(f"=== {host} === (error: HTTP {resp.status_code})")
            continue

        volumes = resp.json().get("Volumes", []) or []
        print(f"=== {host} ===")
        if not volumes:
            print("  (no volumes)")
        else:
            rows = []
            for v in sorted(volumes, key=lambda x: x["Name"]):
                name = v["Name"]
                driver = v.get("Driver", "—")
                mountpoint = v.get("Mountpoint", "—")
                rows.append((name, driver, mountpoint))
                total += 1

            max_name = max(len(r[0]) for r in rows)
            max_driver = max(len(r[1]) for r in rows)
            print(f"  {'NAME':<{max_name}}  {'DRIVER':<{max_driver}}  MOUNTPOINT")
            for name, driver, mountpoint in rows:
                print(f"  {name:<{max_name}}  {driver:<{max_driver}}  {mountpoint}")
        print()

    print(f"Summary: {total} volumes across {len(targets)} host(s)")


def cmd_inspect(args, session, url):
    if not args.name:
        print("Error: Volume name is required for inspect.", file=sys.stderr)
        sys.exit(1)

    if args.host and args.host != "all":
        endpoint_ids = [ENDPOINTS[args.host]]
    else:
        endpoint_ids = list(ENDPOINTS.values())

    matches = find_volume(session, url, args.name, endpoint_ids)

    if not matches:
        print(f"Error: Volume '{args.name}' not found.", file=sys.stderr)
        sys.exit(1)
    if len(matches) > 1:
        exact = [m for m in matches if m[1] == args.name]
        if len(exact) == 1:
            matches = exact
        else:
            print(f"Error: Multiple volumes match '{args.name}':", file=sys.stderr)
            for _, vname, host in matches:
                print(f"  {vname} on {host}", file=sys.stderr)
            print("Use --host to disambiguate.", file=sys.stderr)
            sys.exit(1)

    eid, vname, host = matches[0]
    resp = session.get(f"{url}/api/endpoints/{eid}/docker/volumes/{vname}")
    if resp.status_code != 200:
        print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
        sys.exit(1)

    vol = resp.json()
    print(f"=== Volume: {vol['Name']} ({host}) ===")
    print(f"Driver:     {vol.get('Driver', '—')}")
    print(f"Mountpoint: {vol.get('Mountpoint', '—')}")
    print(f"Scope:      {vol.get('Scope', '—')}")
    print(f"Created:    {vol.get('CreatedAt', '—')}")

    labels = vol.get("Labels") or {}
    if labels:
        print("\nLabels:")
        for k, v in sorted(labels.items()):
            print(f"  {k}={v}")

    options = vol.get("Options") or {}
    if options:
        print("\nOptions:")
        for k, v in sorted(options.items()):
            print(f"  {k}={v}")

    usage = vol.get("UsageData")
    if usage and usage.get("Size", -1) >= 0:
        size_mb = usage["Size"] / (1024 * 1024)
        ref_count = usage.get("RefCount", 0)
        print(f"\nSize:       {size_mb:.1f} MB")
        print(f"Ref count:  {ref_count}")


def cmd_create(args, session, url):
    if not args.name:
        print("Error: Volume name is required for create.", file=sys.stderr)
        sys.exit(1)
    if not args.host or args.host == "all":
        print("Error: --host is required for create.", file=sys.stderr)
        sys.exit(1)

    eid = ENDPOINTS[args.host]
    body = {"Name": args.name, "Driver": args.driver or "local"}
    if args.opt:
        driver_opts = {}
        for o in args.opt:
            if "=" not in o:
                print(f"Error: --opt must be key=value, got '{o}'", file=sys.stderr)
                sys.exit(1)
            k, v = o.split("=", 1)
            driver_opts[k] = v
        body["DriverOpts"] = driver_opts

    resp = session.post(f"{url}/api/endpoints/{eid}/docker/volumes/create", json=body)
    if resp.status_code == 201 or (resp.status_code == 200 and resp.json().get("Name")):
        print(f"Volume '{args.name}' created on {args.host}.")
    else:
        print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
        if resp.text:
            print(resp.text, file=sys.stderr)
        sys.exit(1)


def cmd_remove(args, session, url):
    if not args.name:
        print("Error: Volume name is required for remove.", file=sys.stderr)
        sys.exit(1)
    if not args.host or args.host == "all":
        print("Error: --host is required for remove (safety: no cross-host matching for destructive ops).", file=sys.stderr)
        sys.exit(1)

    eid = ENDPOINTS[args.host]
    matches = find_volume(session, url, args.name, [eid])

    if not matches:
        print(f"Error: Volume '{args.name}' not found on {args.host}.", file=sys.stderr)
        sys.exit(1)
    if len(matches) > 1:
        exact = [m for m in matches if m[1] == args.name]
        if len(exact) == 1:
            matches = exact
        else:
            print(f"Error: Multiple volumes match '{args.name}' on {args.host}:", file=sys.stderr)
            for _, vname, _ in matches:
                print(f"  {vname}", file=sys.stderr)
            sys.exit(1)

    _, vname, host = matches[0]
    resp = session.delete(f"{url}/api/endpoints/{eid}/docker/volumes/{vname}")
    if resp.status_code == 204:
        print(f"Volume '{vname}' removed from {host}.")
    else:
        print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
        if resp.text:
            print(resp.text, file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="portainer-volumes", description="Manage Docker volumes")
    parser.add_argument("action", choices=["list", "inspect", "create", "remove"])
    parser.add_argument("name", nargs="?", help="Volume name (required for inspect/create/remove)")
    parser.add_argument("--host", default="all", choices=["all", "docker01", "docker02", "soho-nas"])
    parser.add_argument("--driver", default="local", help="Volume driver (default: local)")
    parser.add_argument("--opt", action="append", help="Driver options as key=value (repeatable)")
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
