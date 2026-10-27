"""Service account keys, read from the macOS keychain or a file outside any repo.

Keychain values are stored base64-encoded: `security find-generic-password -w` prints values
that contain newlines as hex, and base64 also lets us pass the key on stdin instead of argv,
so it never shows up in the process list.
"""

from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path

SECURITY = "/usr/bin/security"
ACCOUNT = "dottide"


def _validate(info: dict, where: str) -> dict:
    if info.get("type") != "service_account" or "client_email" not in info:
        raise ValueError(f"{where} is not a Google service account key")
    return info


def read(service: str) -> dict:
    out = subprocess.run(
        [SECURITY, "find-generic-password", "-s", service, "-a", ACCOUNT, "-w"],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        raise PermissionError(
            f"no keychain item {service!r}; run: dottide import-key {service} <key.json>"
        )
    return _validate(json.loads(base64.b64decode(out.stdout.strip())), f"keychain item {service!r}")


def read_file(path: str) -> dict:
    return _validate(json.loads(Path(path).expanduser().read_text()), path)


def store(service: str, path: str) -> str:
    """Copy a key file into the keychain. Returns the service account email."""
    info = read_file(path)
    blob = base64.b64encode(json.dumps(info, separators=(",", ":")).encode()).decode()
    label = f"'dotTide {service}'"
    command = f"add-generic-password -U -s {service} -a {ACCOUNT} -l {label} -w {blob}\n"
    out = subprocess.run([SECURITY, "-i"], input=command, capture_output=True, text=True)
    if out.returncode != 0 or out.stderr.strip():
        raise RuntimeError(f"keychain write failed: {out.stderr.strip() or out.returncode}")
    if read(service)["client_email"] != info["client_email"]:
        raise RuntimeError("keychain read-back did not match the key file")
    return info["client_email"]
