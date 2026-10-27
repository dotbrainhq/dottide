"""Weekly snapshot: last full week against the week before, one JSON file per profile.

One file per profile keeps each side's numbers apart, the same way the keys are.
A failing site records its error and the snapshot carries on, so one revoked
permission never costs the whole week's numbers.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from dottide import report
from dottide.config import load_profiles

SCHEMA = 1


def _safe(fn, *args, **kwargs) -> dict:
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 - the error is the data point
        return {"error": str(exc)}


def build(profile_name: str) -> dict:
    profile = next(p for p in load_profiles() if p.name == profile_name)
    last = date.today() - timedelta(days=report.GSC_LAG_DAYS)
    first = last - timedelta(days=6)
    week = {"start": str(first), "end": str(last), "days": 7, "compare": True}
    sites = []
    for site in profile.sites:
        entry: dict = {"site": site.name}
        if site.search_console:
            entry["queries"] = _safe(report.search_queries, site.name, "query", **week, limit=10)
            entry["pages"] = _safe(report.search_queries, site.name, "page", **week, limit=10)
        if site.ga4_property:
            entry["traffic"] = _safe(report.traffic, site.name, **week, limit=10)
        sites.append(entry)
    return {
        "schema": SCHEMA,
        "profile": profile.name,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "week": {"start": str(first), "end": str(last)},
        "sites": sites,
        "stores": _safe(report.store_stats, profile.name),
    }


def run(out: str | None) -> list[Path]:
    written = []
    year, week, _ = date.today().isocalendar()
    for profile in load_profiles():
        data = build(profile.name)
        if out is None:
            print(json.dumps(data, indent=2))
            continue
        folder = Path(out).expanduser()
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{profile.name}-{year}-W{week:02d}.json"
        path.write_text(json.dumps(data, indent=2) + "\n")
        written.append(path)
        print(path)
    return written
