#!/usr/bin/env python3
"""CLI for managing homelab containers via the Portainer API.

Requires: requests (pip install requests)
Environment: PORTAINER_TOKEN (API access token) is required. PORTAINER_URL defaults to http://192.168.10.12:9000.
"""

import argparse
import os
import sys
from pathlib import Path

import requests

DEFAULT_URL = "http://192.168.10.12:9000"
ENDPOINTS = {"docker01": 7, "docker02": 8, "soho-nas": 9}
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def get_env():
    url = os.environ.get("PORTAINER_URL", DEFAULT_URL)
    token = os.environ.get("PORTAINER_TOKEN")
    if not token:
        print("Error: PORTAINER_TOKEN environment variable is required.", file=sys.stderr)
        print("Generate one in Portainer: User Settings > Access Tokens", file=sys.stderr)
        print("Run: export PORTAINER_TOKEN=ptr_...", file=sys.stderr)
        sys.exit(1)
    return url, token


def find_container(session, url, name, endpoint_ids):
    """Search endpoints for containers matching `name`. Returns [(endpoint_id, exact_name, host_name)]."""
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
    """Strip 8-byte Docker stream multiplexing headers from log output."""
    output = []
    i = 0
    while i + 8 <= len(raw):
        size = int.from_bytes(raw[i + 4 : i + 8], "big")
        if i + 8 + size > len(raw):
            # Incomplete frame — grab what's left
            output.append(raw[i + 8 :].decode("utf-8", errors="replace"))
            break
        output.append(raw[i + 8 : i + 8 + size].decode("utf-8", errors="replace"))
        i += 8 + size
    return "".join(output)


def format_ports(ports):
    """Format Docker API port entries into readable strings like '3100→3000'."""
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
    # Deduplicate and sort by public port
    seen = set()
    unique = []
    for e in entries:
        if e not in seen:
            seen.add(e)
            unique.append(e)
    unique.sort(key=lambda x: int(x.split("→")[0].split("/")[0]))
    return ", ".join(unique) if unique else "—"


# --- Subcommands ---


def cmd_status(args, session, url):
    if args.host == "all":
        targets = ENDPOINTS
    else:
        targets = {args.host: ENDPOINTS[args.host]}

    total_running = 0
    total_stopped = 0
    total_other = 0

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

            # Align columns
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
    return 0


def cmd_ports(args, session, url):
    if args.host == "all":
        targets = ENDPOINTS
    else:
        targets = {args.host: ENDPOINTS[args.host]}

    for host, eid in targets.items():
        resp = session.get(f"{url}/api/endpoints/{eid}/docker/containers/json?all=1")
        if resp.status_code != 200:
            print(f"=== {host} === (error: HTTP {resp.status_code})")
            continue

        containers = resp.json()
        print(f"=== {host} ===")

        # Collect all port mappings, deduplicated
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
            # Sort by host port (host-mode entries go last)
            port_rows.sort(key=lambda r: (r[0] or 99999,))
            max_name = max(len(r[3]) for r in port_rows)
            for pub, priv, ptype, name, state in port_rows:
                if pub is None:
                    print(f"  {'host':<7}  {'—':>5}  {'—':<4}  {name:<{max_name}}  {state}")
                else:
                    print(f"  {pub:<7}  {priv:>5}  {ptype:<4}  {name:<{max_name}}  {state}")
        print()

    return 0


def cmd_control(args, session, url):
    if args.host:
        endpoint_ids = [ENDPOINTS[args.host]]
    else:
        endpoint_ids = list(ENDPOINTS.values())

    matches = find_container(session, url, args.container, endpoint_ids)

    if not matches:
        print(f"Error: Container '{args.container}' not found.", file=sys.stderr)
        print("Run: /portainer-status to check container names", file=sys.stderr)
        return 1

    if len(matches) > 1:
        print(f"Error: Multiple containers match '{args.container}':", file=sys.stderr)
        for eid, cname, host in matches:
            print(f"  {cname} on {host}", file=sys.stderr)
        print("Use --host to disambiguate.", file=sys.stderr)
        return 1

    eid, cname, host = matches[0]
    resp = session.post(
        f"{url}/api/endpoints/{eid}/docker/containers/{cname}/{args.action}",
        headers={"Content-Type": "application/json"},
    )

    if resp.status_code == 204:
        print(f"{cname} {args.action} completed successfully on {host}.")
        return 0
    elif resp.status_code == 304:
        print(f"{cname} is already in the requested state on {host}.")
        return 0
    else:
        print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
        if resp.text:
            print(resp.text, file=sys.stderr)
        return 1


def cmd_logs(args, session, url):
    if args.host:
        endpoint_ids = [ENDPOINTS[args.host]]
    else:
        endpoint_ids = list(ENDPOINTS.values())

    matches = find_container(session, url, args.container, endpoint_ids)

    if not matches:
        print(f"Error: Container '{args.container}' not found.", file=sys.stderr)
        return 1

    if len(matches) > 1:
        print(f"Error: Multiple containers match '{args.container}':", file=sys.stderr)
        for eid, cname, host in matches:
            print(f"  {cname} on {host}", file=sys.stderr)
        print("Use --host to disambiguate.", file=sys.stderr)
        return 1

    eid, cname, host = matches[0]
    resp = session.get(
        f"{url}/api/endpoints/{eid}/docker/containers/{cname}/logs",
        params={"stdout": 1, "stderr": 1, "timestamps": 1, "tail": args.tail},
    )

    if resp.status_code == 404:
        print(f"Error: Container '{cname}' not found on {host}.", file=sys.stderr)
        return 1
    elif resp.status_code != 200:
        print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
        return 1

    if not resp.content:
        print(f"=== Logs: {cname} ({host}) — empty ===")
        return 0

    cleaned = strip_docker_headers(resp.content)
    print(f"=== Logs: {cname} ({host}) — last {args.tail} lines ===")
    print(cleaned, end="")
    return 0


def cmd_deploy(args, session, url):
    parts = args.target.split("/", 1)
    if len(parts) != 2:
        print("Error: Target must be <host>/<service> (e.g. docker01/grafana)", file=sys.stderr)
        return 1

    host, service = parts
    if host not in ENDPOINTS:
        print(f"Error: Unknown host '{host}'. Use: {', '.join(ENDPOINTS.keys())}", file=sys.stderr)
        return 1

    compose_path = REPO_ROOT / "docker" / host / service / f"{service}.yml"
    if not compose_path.exists():
        print(f"Error: Compose file not found at {compose_path}", file=sys.stderr)
        return 1

    stack_name = args.stack_name or service
    endpoint_id = ENDPOINTS[host]
    compose_content = compose_path.read_text()

    # Check if stack already exists
    resp = session.get(f"{url}/api/stacks")
    if resp.status_code != 200:
        print(f"Error: Failed to list stacks (HTTP {resp.status_code})", file=sys.stderr)
        return 1

    existing_id = None
    for stack in resp.json():
        if stack.get("Name") == stack_name:
            existing_id = stack["Id"]
            break

    if existing_id is None:
        # Create new stack
        resp = session.post(
            f"{url}/api/stacks/create/standalone/string",
            params={"endpointId": endpoint_id},
            json={"name": stack_name, "stackFileContent": compose_content},
        )
    else:
        # Update existing stack
        resp = session.put(
            f"{url}/api/stacks/{existing_id}",
            params={"endpointId": endpoint_id},
            json={"stackFileContent": compose_content, "pullImage": True, "prune": False},
        )

    if resp.status_code in (200, 201) and resp.json().get("Id"):
        action = "updated" if existing_id else "created"
        print(f"Stack '{stack_name}' {action} successfully on {host}.")
        return 0
    else:
        print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
        if resp.text:
            print(resp.text, file=sys.stderr)
        return 1


DEFAULT_NETWORKS = {"bridge", "host", "none"}


def find_volume(session, url, name, endpoint_ids):
    """Search endpoints for volumes matching `name`. Returns [(endpoint_id, volume_name, host_name)]."""
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


def cmd_volumes(args, session, url):
    action = args.action

    if action == "list":
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
        return 0

    elif action == "inspect":
        if not args.name:
            print("Error: Volume name is required for inspect.", file=sys.stderr)
            return 1

        if args.host and args.host != "all":
            endpoint_ids = [ENDPOINTS[args.host]]
        else:
            endpoint_ids = list(ENDPOINTS.values())

        matches = find_volume(session, url, args.name, endpoint_ids)

        if not matches:
            print(f"Error: Volume '{args.name}' not found.", file=sys.stderr)
            return 1
        if len(matches) > 1:
            exact = [m for m in matches if m[1] == args.name]
            if len(exact) == 1:
                matches = exact
            else:
                print(f"Error: Multiple volumes match '{args.name}':", file=sys.stderr)
                for _, vname, host in matches:
                    print(f"  {vname} on {host}", file=sys.stderr)
                print("Use --host to disambiguate.", file=sys.stderr)
                return 1

        eid, vname, host = matches[0]
        resp = session.get(f"{url}/api/endpoints/{eid}/docker/volumes/{vname}")
        if resp.status_code != 200:
            print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
            return 1

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

        return 0

    elif action == "create":
        if not args.name:
            print("Error: Volume name is required for create.", file=sys.stderr)
            return 1
        if not args.host or args.host == "all":
            print("Error: --host is required for create.", file=sys.stderr)
            return 1

        eid = ENDPOINTS[args.host]
        body = {"Name": args.name, "Driver": args.driver or "local"}
        if args.opt:
            driver_opts = {}
            for o in args.opt:
                if "=" not in o:
                    print(f"Error: --opt must be key=value, got '{o}'", file=sys.stderr)
                    return 1
                k, v = o.split("=", 1)
                driver_opts[k] = v
            body["DriverOpts"] = driver_opts

        resp = session.post(f"{url}/api/endpoints/{eid}/docker/volumes/create", json=body)
        if resp.status_code == 201 or (resp.status_code == 200 and resp.json().get("Name")):
            print(f"Volume '{args.name}' created on {args.host}.")
            return 0
        else:
            print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
            if resp.text:
                print(resp.text, file=sys.stderr)
            return 1

    elif action == "remove":
        if not args.name:
            print("Error: Volume name is required for remove.", file=sys.stderr)
            return 1
        if not args.host or args.host == "all":
            print("Error: --host is required for remove (safety: no cross-host matching for destructive ops).", file=sys.stderr)
            return 1

        eid = ENDPOINTS[args.host]
        matches = find_volume(session, url, args.name, [eid])

        if not matches:
            print(f"Error: Volume '{args.name}' not found on {args.host}.", file=sys.stderr)
            return 1
        if len(matches) > 1:
            exact = [m for m in matches if m[1] == args.name]
            if len(exact) == 1:
                matches = exact
            else:
                print(f"Error: Multiple volumes match '{args.name}' on {args.host}:", file=sys.stderr)
                for _, vname, _ in matches:
                    print(f"  {vname}", file=sys.stderr)
                return 1

        _, vname, host = matches[0]
        resp = session.delete(f"{url}/api/endpoints/{eid}/docker/volumes/{vname}")
        if resp.status_code == 204:
            print(f"Volume '{vname}' removed from {host}.")
            return 0
        else:
            print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
            if resp.text:
                print(resp.text, file=sys.stderr)
            return 1

    else:
        print(f"Error: Unknown volumes action '{action}'.", file=sys.stderr)
        return 1


def find_network(session, url, name, endpoint_ids):
    """Search endpoints for networks matching `name`. Returns [(endpoint_id, network_id, network_name, host_name)]."""
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


def cmd_networks(args, session, url):
    action = args.action

    if action == "list":
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
        return 0

    elif action == "inspect":
        if not args.name:
            print("Error: Network name is required for inspect.", file=sys.stderr)
            return 1

        if args.host:
            endpoint_ids = [ENDPOINTS[args.host]]
        else:
            endpoint_ids = list(ENDPOINTS.values())

        matches = find_network(session, url, args.name, endpoint_ids)

        if not matches:
            print(f"Error: Network '{args.name}' not found.", file=sys.stderr)
            return 1
        if len(matches) > 1:
            # Prefer exact match
            exact = [m for m in matches if m[2] == args.name]
            if len(exact) == 1:
                matches = exact
            else:
                print(f"Error: Multiple networks match '{args.name}':", file=sys.stderr)
                for _, _, nname, host in matches:
                    print(f"  {nname} on {host}", file=sys.stderr)
                print("Use --host to disambiguate.", file=sys.stderr)
                return 1

        eid, nid, nname, host = matches[0]
        resp = session.get(f"{url}/api/endpoints/{eid}/docker/networks/{nid}")
        if resp.status_code != 200:
            print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
            return 1

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
        return 0

    elif action == "create":
        if not args.name:
            print("Error: Network name is required for create.", file=sys.stderr)
            return 1
        if not args.host:
            print("Error: --host is required for create.", file=sys.stderr)
            return 1

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
            return 0
        else:
            print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
            if resp.text:
                print(resp.text, file=sys.stderr)
            return 1

    elif action == "remove":
        if not args.name:
            print("Error: Network name is required for remove.", file=sys.stderr)
            return 1
        if not args.host:
            print("Error: --host is required for remove (safety: no cross-host matching for destructive ops).", file=sys.stderr)
            return 1
        if args.name in DEFAULT_NETWORKS:
            print(f"Error: Cannot remove default network '{args.name}'.", file=sys.stderr)
            return 1

        eid = ENDPOINTS[args.host]
        matches = find_network(session, url, args.name, [eid])

        if not matches:
            print(f"Error: Network '{args.name}' not found on {args.host}.", file=sys.stderr)
            return 1
        if len(matches) > 1:
            exact = [m for m in matches if m[2] == args.name]
            if len(exact) == 1:
                matches = exact
            else:
                print(f"Error: Multiple networks match '{args.name}' on {args.host}:", file=sys.stderr)
                for _, _, nname, _ in matches:
                    print(f"  {nname}", file=sys.stderr)
                return 1

        _, nid, nname, host = matches[0]
        resp = session.delete(f"{url}/api/endpoints/{eid}/docker/networks/{nid}")
        if resp.status_code == 204:
            print(f"Network '{nname}' removed from {host}.")
            return 0
        else:
            print(f"Error: HTTP {resp.status_code}", file=sys.stderr)
            if resp.text:
                print(resp.text, file=sys.stderr)
            return 1

    else:
        print(f"Error: Unknown networks action '{action}'.", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(prog="portainer", description="Manage homelab containers via Portainer API")
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="Show container status")
    p_status.add_argument("host", nargs="?", default="all", choices=["all", "docker01", "docker02", "soho-nas"])
    p_status.add_argument("--ports", action="store_true", help="Include port mappings in output")

    p_ports = sub.add_parser("ports", help="Show port allocations per host")
    p_ports.add_argument("host", nargs="?", default="all", choices=["all", "docker01", "docker02", "soho-nas"])

    p_control = sub.add_parser("control", help="Start/stop/restart a container")
    p_control.add_argument("action", choices=["start", "stop", "restart"])
    p_control.add_argument("container")
    p_control.add_argument("--host", choices=["docker01", "docker02", "soho-nas"])

    p_logs = sub.add_parser("logs", help="View container logs")
    p_logs.add_argument("container")
    p_logs.add_argument("--host", choices=["docker01", "docker02", "soho-nas"])
    p_logs.add_argument("--tail", type=int, default=100)

    p_deploy = sub.add_parser("deploy", help="Deploy/update a Portainer stack")
    p_deploy.add_argument("target", help="host/service (e.g. docker01/grafana)")
    p_deploy.add_argument("--stack-name", help="Override stack name (default: service name)")

    p_volumes = sub.add_parser("volumes", help="Manage Docker volumes")
    p_volumes.add_argument("action", choices=["list", "inspect", "create", "remove"])
    p_volumes.add_argument("name", nargs="?", help="Volume name (required for inspect/create/remove)")
    p_volumes.add_argument("--host", default="all", choices=["all", "docker01", "docker02", "soho-nas"])
    p_volumes.add_argument("--driver", default="local", help="Volume driver (default: local)")
    p_volumes.add_argument("--opt", action="append", help="Driver options as key=value (repeatable)")

    p_networks = sub.add_parser("networks", help="Manage Docker networks")
    p_networks.add_argument("action", choices=["list", "inspect", "create", "remove"])
    p_networks.add_argument("name", nargs="?", help="Network name (required for inspect/create/remove)")
    p_networks.add_argument("--host", default="all", choices=["all", "docker01", "docker02", "soho-nas"])
    p_networks.add_argument("--driver", default="bridge", help="Network driver (default: bridge)")
    p_networks.add_argument("--subnet", help="Subnet CIDR (e.g. 172.20.0.0/16)")
    p_networks.add_argument("--gateway", help="Gateway IP (e.g. 172.20.0.1)")

    args = parser.parse_args()
    url, token = get_env()

    session = requests.Session()
    session.headers["X-API-Key"] = token

    handlers = {"status": cmd_status, "ports": cmd_ports, "control": cmd_control, "logs": cmd_logs, "deploy": cmd_deploy, "volumes": cmd_volumes, "networks": cmd_networks}

    try:
        code = handlers[args.command](args, session, url)
    except requests.RequestException as e:
        print(f"Connection error: {e}", file=sys.stderr)
        code = 1

    sys.exit(code)


if __name__ == "__main__":
    main()
