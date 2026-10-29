"""Find every site the key can read and suggest profile entries for the ones not set up yet.

Reading is all it does on Google's side. The only write is `--write`, which appends
the suggested [[sites]] blocks to a local profile file.
"""

from __future__ import annotations

from urllib.parse import urlparse

from dottide import google
from dottide.config import Profile, config_paths, load_profiles


def host(address: str) -> str:
    """The bare domain behind a Search Console property or a site URL."""
    if address.startswith("sc-domain:"):
        address = address.removeprefix("sc-domain:")
    elif "://" in address:
        address = urlparse(address).hostname or ""
    return address.strip("/").lower().removeprefix("www.")


# Second-level labels under a country code, like the "co" in example.co.uk.
SECOND_LEVEL = {"co", "com", "org", "net", "ac", "gov", "edu"}


def brand_guess(domain: str) -> list[str]:
    """The site's own name as brand_terms would want it, from the label before the suffix."""
    labels = host(domain).split(".")[:-1]
    if len(labels) > 1 and labels[-1] in SECOND_LEVEL:
        labels.pop()
    if not labels:
        return []
    name = labels[-1]
    return [name, name.replace("-", " ")] if "-" in name else [name]


def plan(gsc_properties: list[str], streams: list[dict], configured: list[dict]) -> list[dict]:
    """Suggested sites, one per domain, skipping anything a profile already covers.

    A domain property wins over a URL-prefix property for the same domain, because it
    covers every subdomain and protocol.
    """
    taken = {host(s["name"]) for s in configured}
    taken |= {host(s["search_console"]) for s in configured if s.get("search_console")}
    taken_ga4 = {s["ga4_property"] for s in configured if s.get("ga4_property")}

    by_host: dict[str, dict] = {}
    for prop in gsc_properties:
        entry = by_host.setdefault(host(prop), {"name": host(prop)})
        current = entry.get("search_console", "")
        if not current or (prop.startswith("sc-domain:") and not current.startswith("sc-domain:")):
            entry["search_console"] = prop
    for stream in streams:
        key = host(stream["url"]) if stream["url"] else ""
        if not key or stream["property"] in taken_ga4:
            continue
        entry = by_host.setdefault(key, {"name": key})
        entry.setdefault("ga4_property", stream["property"])
        entry.setdefault("measurement_id", stream["measurement_id"])
    return [by_host[k] for k in sorted(by_host) if k not in taken]


def to_toml(sites: list[dict]) -> str:
    blocks = []
    for site in sites:
        lines = ["[[sites]]", f'name = "{site["name"]}"']
        if site.get("search_console"):
            lines.append(f'search_console = "{site["search_console"]}"')
        if site.get("ga4_property"):
            note = f"   # {site['measurement_id']}" if site.get("measurement_id") else ""
            lines.append(f'ga4_property = "{site["ga4_property"]}"{note}')
        if brand := brand_guess(site["name"]):
            terms = ", ".join(f'"{t}"' for t in brand)
            lines.append(
                f"# brand_terms = [{terms}]   # suggested from the domain; check it, then uncomment"
            )
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def discover(profile_name: str | None = None) -> dict:
    """Read what the key can see and compare it with every profile."""
    profiles = load_profiles()
    keyed = [p for p in profiles if p.keychain or p.key_file]
    if profile_name:
        keyed = [p for p in keyed if p.name == profile_name]
    if not keyed:
        raise ValueError("no profile with a [key]; add one first (see docs/configuration.md)")

    configured = [
        {"name": s.name, "search_console": s.search_console, "ga4_property": s.ga4_property}
        for p in profiles
        for s in p.sites
    ]
    # Several profiles often share one key; read each key once.
    seen: dict[str, Profile] = {}
    for p in keyed:
        seen.setdefault(p.key_source, p)

    gsc, streams, errors = [], [], []
    for profile in seen.values():
        gsc += google.gsc_properties(profile)
        try:
            streams += google.ga4_web_streams(profile)
        except Exception as exc:  # noqa: BLE001 - GA4 is optional; Search Console still counts
            errors.append(f"GA4 ({profile.key_source}): {exc}")

    new = plan(sorted(set(gsc)), streams, configured)
    result = {
        "keys": list(seen),
        "search_console_properties": sorted(set(gsc)),
        "ga4_web_streams": streams,
        "already_configured": [s["name"] for s in configured],
        "new_sites": new,
        "toml": to_toml(new),
    }
    if errors:
        result["errors"] = errors
    return result


def write(profile_name: str | None, toml: str) -> str:
    """Append suggested blocks to a profile file and return its path."""
    paths = config_paths()
    if profile_name:
        paths = [p for p in paths if p.stem == profile_name]
    if len(paths) != 1:
        names = ", ".join(p.stem for p in config_paths()) or "none"
        raise ValueError(f"pick one profile with --profile to write to. Profiles: {names}")
    path = paths[0]
    text = path.read_text().rstrip()
    # New sites go before [stores] when it exists, so the file keeps its usual order.
    marker = "\n[stores]"
    if marker in text:
        head, tail = text.split(marker, 1)
        text = f"{head.rstrip()}\n\n{toml}\n{marker}{tail}"
    else:
        text = f"{text}\n\n{toml}"
    path.write_text(text + "\n")
    return str(path)
