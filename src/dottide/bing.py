"""Bing Webmaster Tools numbers. Bing feeds Copilot and other assistants, so its search data
is worth a look next to Google's. Needs a Bing Webmaster Tools API key, stored with
`dottide import-secret`. Bing updates these numbers about once a week."""

from __future__ import annotations

from datetime import UTC, date, datetime

import httpx

from dottide import keys
from dottide.config import Profile, Site, find_site, load_profiles
from dottide.report import period

API = "https://ssl.bing.com/webmaster/api.svc/json"


def _call(api_key: str, method: str, **params) -> list[dict]:
    response = httpx.get(f"{API}/{method}", params={"apikey": api_key, **params}, timeout=30)
    if response.status_code >= 400:
        try:
            message = response.json().get("Message") or response.text[:200]
        except ValueError:
            message = response.text[:200]
        raise RuntimeError(f"Bing API {response.status_code}: {message}")
    return response.json().get("d") or []


def bing_date(value: str) -> date:
    """Bing dates look like /Date(1316156400000-0700)/: milliseconds since 1970, in UTC."""
    millis = value.removeprefix("/Date(").split(")")[0]
    for sign in "+-":
        millis = millis.split(sign)[0] if sign in millis[1:] else millis
    return datetime.fromtimestamp(int(millis) / 1000, UTC).date()


def site_url(site: Site) -> str:
    if site.bing:
        return site.bing
    prop = site.search_console or site.name
    if prop.startswith("http"):
        return prop
    return f"https://{prop.removeprefix('sc-domain:')}/"


def api_key(profile: Profile) -> str:
    if not profile.bing_keychain:
        raise ValueError(
            f"profile {profile.name!r} has no [bing] keychain; add one and run "
            "dottide import-secret <name> (see docs/configuration.md)"
        )
    return keys.read_secret(profile.bing_keychain)


def user_sites(key: str) -> list[str]:
    return [s["Url"] for s in _call(key, "GetUserSites") if s.get("IsVerified", True)]


def summarize(rows: list[dict], first: date, last: date, limit: int) -> list[dict]:
    """Add up Bing's weekly query rows inside the range, most clicks first."""
    by_query: dict[str, dict] = {}
    for row in rows:
        if not first <= bing_date(row["Date"]) <= last:
            continue
        q = by_query.setdefault(row["Query"], {"clicks": 0, "impressions": 0, "weighted": 0.0})
        q["clicks"] += row.get("Clicks", 0)
        q["impressions"] += row.get("Impressions", 0)
        q["weighted"] += row.get("AvgImpressionPosition", 0) * row.get("Impressions", 0)
    out = [
        {
            "query": name,
            "clicks": q["clicks"],
            "impressions": q["impressions"],
            "position": round(q["weighted"] / q["impressions"], 1) if q["impressions"] else None,
        }
        for name, q in by_query.items()
    ]
    return sorted(out, key=lambda r: (-r["clicks"], -r["impressions"]))[:limit]


def totals(rows: list[dict], first: date, last: date) -> dict:
    inside = [r for r in rows if first <= bing_date(r["Date"]) <= last]
    return {
        "clicks": sum(r.get("Clicks", 0) for r in inside),
        "impressions": sum(r.get("Impressions", 0) for r in inside),
    }


def bing_queries(
    site: str, start: str | None = None, end: str | None = None, days: int = 28, limit: int = 25
) -> dict:
    profile, s = find_site(load_profiles(), site)
    key, url = api_key(profile), site_url(s)
    first, last = period(start, end, days)
    return {
        "site": site,
        "bing_site": url,
        "start": str(first),
        "end": str(last),
        "totals": totals(_call(key, "GetRankAndTrafficStats", siteUrl=url), first, last),
        "rows": summarize(_call(key, "GetQueryStats", siteUrl=url), first, last, limit),
    }
