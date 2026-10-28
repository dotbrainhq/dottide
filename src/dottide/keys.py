"""Service account keys, read from the system secret store or a file outside any repo.

On macOS the key lives in the keychain, through `/usr/bin/security`. Values are stored
base64-encoded: `security find-generic-password -w` prints values that contain newlines as hex,
and base64 also lets us pass the key on stdin instead of argv, so it never shows up in the
process list.

On Windows (Credential Manager) and Linux (Secret Service) the key goes through `keyring`.
Windows caps one credential at 2,560 bytes and a key is larger, so the value is split into
numbered chunks there and on Linux alike.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from pathlib import Path

SECURITY = "/usr/bin/security"
ACCOUNT = "dottide"
CHUNK = 1000


def _validate(info: dict, where: str) -> dict:
    if info.get("type") != "service_account" or "client_email" not in info:
        raise ValueError(f"{where} is not a Google service account key")
    return info


def _encode(info: dict) -> str:
    return base64.b64encode(json.dumps(info, separators=(",", ":")).encode()).decode()


def _missing(service: str) -> PermissionError:
    return PermissionError(
        f"no stored key named {service!r}; run: dottide import-key {service} <key.json>"
    )


def _keyring_read(service: str) -> str | None:
    import keyring

    count = keyring.get_password(service, "chunks")
    if count is None:
        return None
    return "".join(keyring.get_password(service, f"chunk-{i}") or "" for i in range(int(count)))


def _keyring_store(service: str, blob: str) -> None:
    import keyring

    parts = [blob[i : i + CHUNK] for i in range(0, len(blob), CHUNK)]
    for i, part in enumerate(parts):
        keyring.set_password(service, f"chunk-{i}", part)
    keyring.set_password(service, "chunks", str(len(parts)))


def _get_blob(service: str) -> str | None:
    if sys.platform != "darwin":
        return _keyring_read(service)
    out = subprocess.run(
        [SECURITY, "find-generic-password", "-s", service, "-a", ACCOUNT, "-w"],
        capture_output=True,
        text=True,
    )
    return out.stdout.strip() if out.returncode == 0 else None


def _put_blob(service: str, blob: str) -> None:
    if sys.platform != "darwin":
        _keyring_store(service, blob)
        return
    label = f"'dotTide {service}'"
    command = f"add-generic-password -U -s {service} -a {ACCOUNT} -l {label} -w {blob}\n"
    out = subprocess.run([SECURITY, "-i"], input=command, capture_output=True, text=True)
    if out.returncode != 0 or out.stderr.strip():
        raise RuntimeError(f"keychain write failed: {out.stderr.strip() or out.returncode}")


def read(service: str) -> dict:
    blob = _get_blob(service)
    if blob is None:
        raise _missing(service)
    return _validate(json.loads(base64.b64decode(blob)), f"stored key {service!r}")


def read_file(path: str) -> dict:
    file = Path(path).expanduser()
    if os.name == "posix" and file.stat().st_mode & 0o077:
        print(
            f"dottide: warning: {file} can be read by other users; run: chmod 600 {file}",
            file=sys.stderr,
        )
    return _validate(json.loads(file.read_text()), path)


def store(service: str, path: str) -> str:
    """Copy a key file into the secret store. Returns the service account email."""
    info = read_file(path)
    _put_blob(service, _encode(info))
    if read(service)["client_email"] != info["client_email"]:
        raise RuntimeError("secret store read-back did not match the key file")
    return info["client_email"]


def read_secret(service: str) -> str:
    """A plain secret, like an API key, stored with store_secret."""
    blob = _get_blob(service)
    if blob is None:
        raise PermissionError(
            f"no stored secret named {service!r}; run: dottide import-secret {service}"
        )
    return base64.b64decode(blob).decode()


def store_secret(service: str, value: str) -> None:
    value = value.strip()
    if not value:
        raise ValueError("the secret is empty")
    _put_blob(service, base64.b64encode(value.encode()).decode())
    if read_secret(service) != value:
        raise RuntimeError("secret store read-back did not match")
