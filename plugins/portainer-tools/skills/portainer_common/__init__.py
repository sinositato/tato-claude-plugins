"""Shared configuration and helpers for all Portainer skills."""

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load config: skill-local .env first, then user-level ~/.config/portainer/.env.
# Already-set env vars (from ~/.profile or system) take highest priority since
# load_dotenv does not overwrite existing values.
load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv(Path.home() / ".config" / "portainer" / ".env")

DEFAULT_URL = "http://192.168.10.12:9000"
ENDPOINTS = {"docker01": 7, "docker02": 8, "soho-nas": 9}


def get_session():
    """Return (url, authenticated_session). Exits on missing token."""
    url = os.environ.get("PORTAINER_URL", DEFAULT_URL)
    token = os.environ.get("PORTAINER_TOKEN")
    if not token:
        print("Error: PORTAINER_TOKEN not set.", file=sys.stderr)
        print("Configure it in one of these locations:", file=sys.stderr)
        print("  1. ~/.config/portainer/.env  (recommended for users)", file=sys.stderr)
        print("  2. skills/portainer_common/.env  (project-level)", file=sys.stderr)
        print("  3. export PORTAINER_TOKEN=ptr_...  (in ~/.profile)", file=sys.stderr)
        sys.exit(1)
    session = requests.Session()
    session.headers["X-API-Key"] = token
    return url, session
