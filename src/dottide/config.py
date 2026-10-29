"""Profiles: one TOML file per side, each with its own Google key and its own sites.

Keeping one file per side means a personal profile and a business profile never share a key,
and an agent can be pointed at a single file when it should only see one side.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path

from dottide import keys

DEFAULT_DIR = Path("~/.config/dottide")


@dataclass(frozen=True)
class Site:
    name: str
    profile: str
    search_console: str | None = None
    ga4_property: str | None = None
    bing: str | None = None
    brand_terms: tuple[str, ...] = ()


@dataclass
class Profile:
    name: str
    keychain: str | None = None
    key_file: str | None = None
    bing_keychain: str | None = None
    sites: list[Site] = field(default_factory=list)
    stores: dict = field(default_factory=dict)

    @property
    def key_source(self) -> str:
        if self.keychain:
            return f"keychain:{self.keychain}"
        if self.key_file:
            return f"file:{self.key_file}"
        return "none"

    def key_info(self) -> dict:
        if self.keychain:
            return keys.read(self.keychain)
        if self.key_file:
            return keys.read_file(self.key_file)
        raise PermissionError(f"profile {self.name!r} has no [key] set")


def config_paths() -> list[Path]:
    """DOTTIDE_CONFIG may name one file or a folder of .toml files."""
    target = Path(os.environ.get("DOTTIDE_CONFIG", DEFAULT_DIR)).expanduser()
    if target.is_file():
        return [target]
    if target.is_dir():
        return sorted(p for p in target.glob("*.toml") if not p.name.startswith("_"))
    return []


def load_profile(path: Path) -> Profile:
    data = tomllib.loads(path.read_text())
    key = data.get("key", {})
    profile = Profile(
        name=path.stem,
        keychain=key.get("keychain"),
        key_file=key.get("file"),
        bing_keychain=data.get("bing", {}).get("keychain"),
        stores=data.get("stores", {}),
    )
    for entry in data.get("sites", []):
        ga4 = entry.get("ga4_property")
        profile.sites.append(
            Site(
                name=entry["name"],
                profile=profile.name,
                search_console=entry.get("search_console"),
                ga4_property=str(ga4) if ga4 else None,
                bing=entry.get("bing"),
                brand_terms=tuple(t.lower() for t in entry.get("brand_terms", [])),
            )
        )
    return profile


def load_profiles() -> list[Profile]:
    return [load_profile(p) for p in config_paths()]


def find_site(profiles: list[Profile], name: str) -> tuple[Profile, Site]:
    for profile in profiles:
        for site in profile.sites:
            if site.name == name:
                return profile, site
    known = ", ".join(s.name for p in profiles for s in p.sites) or "none configured"
    raise ValueError(f"unknown site {name!r}. Configured sites: {known}")


def init_profile(name: str = "main") -> Path:
    """Write a starter profile from the bundled template. Never overwrites a file."""
    folder = DEFAULT_DIR.expanduser()
    path = folder / f"{name}.toml"
    if path.exists():
        raise FileExistsError(f"{path} already exists; edit it, or pick another --profile name")
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_text(files("dottide").joinpath("profile_template.toml").read_text())
    path.chmod(0o600)
    return path
