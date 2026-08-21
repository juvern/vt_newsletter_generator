#!/usr/bin/env python3
"""
Send a finished newsletter to Kit as a draft broadcast.

This is the only network / side-effecting script in the skill. It should
only ever be run after the user has explicitly confirmed the drafted
subject, preview text, and HTML content — same as the "Send to Kit" button
in app.py.

Input JSON (via --file or stdin):
{
  "subject": "...",
  "content": "<html>...",
  "preview_text": "..."
}

Reads kit_api_key from .streamlit/secrets.toml (same file the Streamlit
app uses), so no separate credential setup is needed.

Prints the Kit API response and exits non-zero on failure.
"""
import json
import sys
import tomllib
from pathlib import Path

import requests

SECRETS_PATH = Path(__file__).resolve().parents[4] / ".streamlit" / "secrets.toml"
KIT_BROADCASTS_URL = "https://api.convertkit.com/v4/broadcasts"


def load_kit_api_key() -> str:
    if not SECRETS_PATH.exists():
        raise SystemExit(f"Secrets file not found: {SECRETS_PATH}")
    with open(SECRETS_PATH, "rb") as f:
        secrets = tomllib.load(f)
    api_key = secrets.get("kit_api_key")
    if not api_key:
        raise SystemExit("kit_api_key not found in .streamlit/secrets.toml")
    return api_key


def send(payload: dict) -> dict:
    api_key = load_kit_api_key()
    response = requests.post(
        KIT_BROADCASTS_URL,
        headers={
            "Content-Type": "application/json",
            "X-Kit-Api-Key": api_key,
        },
        json=payload,
        timeout=15,
    )
    result = {"status_code": response.status_code}
    try:
        result["body"] = response.json()
    except ValueError:
        result["body"] = response.text
    return result


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] != "-":
        payload = json.loads(Path(sys.argv[1]).read_text())
    else:
        payload = json.loads(sys.stdin.read())

    missing = [k for k in ("subject", "content", "preview_text") if not payload.get(k)]
    if missing:
        raise SystemExit(f"Missing required field(s): {', '.join(missing)}")

    result = send(payload)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")

    if result["status_code"] not in (200, 201):
        sys.exit(1)


if __name__ == "__main__":
    main()
