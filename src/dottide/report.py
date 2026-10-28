"""The four reports, shared by the MCP server, the CLI, and the weekly snapshot."""

from __future__ import annotations

from datetime import date, timedelta

from dottide import google, stores
from dottide.config import Profile, find_site, load_profiles

# Search Console data settles about three days after the fact.
GSC_LAG_DAYS = 3

AI_SOURCES = {
    "chatgpt.com": "ChatGPT",
    "chat.openai.com": "ChatGPT",
    "perplexity.ai": "Perplexity",
    "copilot.microsoft.com": "Copilot",
    "copilot.com": "Copilot",
    "gemini.google.com": "Gemini",
    "bard.google.com": "Gemini",
    "claude.ai": "Claude",
    "chat.mistral.ai": "Mistral",
    "chat.deepseek.com": "DeepSeek",
    "grok.com": "Grok",
    "meta.ai": "Meta AI",
    "you.com": "You.com",
    "phind.com": "Phind",
}


def ai_assistant(source: str) -> str | None:
    host = source.lower().strip().removeprefix("www.")
    for domain, name in AI_SOURCES.items():
        if host == domain or host.endswith("." + domain):
            return name
    return None


def period(start: str | None, end: str | None, days: int) -> tuple[date, date]:
    last = date.fromisoformat(end) if end else date.today() - timedelta(days=GSC_LAG_DAYS)
    first = date.fromisoformat(start) if start else last - timedelta(days=days - 1)
    if first > last:
        raise ValueError(f"start {first} is after end {last}")
    return first, last


def previous(first: date, last: date) -> tuple[date, date]:
    length = (last - first).days + 1
    prev_last = first - timedelta(days=1)
    return prev_last - timedelta(days=length - 1), prev_last


def _delta(now: dict, before: dict | None, fields: tuple[str, ...]) -> dict:
    out = dict(now)
    for f in fields:
        old = (before or {}).get(f)
        out[f"previous_{f}"] = old
        out[f"change_{f}"] = None if old is None else round(now[f] - old, 2)
    return out


def sites() -> dict:
    """Every configured site, the key that covers it, and whether access works when you ask."""
    report = []
    for profile in load_profiles():
        entry: dict = {"profile": profile.name, "key": profile.key_source, "sites": []}
        try:
            entry["service_account"] = google.client_email(profile)
            visible = google.gsc_properties(profile)
            entry["search_console_visible"] = visible
        except Exception as exc:  # noqa: BLE001 - report every failure, never stop the list
            entry["key_error"] = str(exc)
            visible = None
        for site in profile.sites:
            status: dict = {"site": site.name}
            if site.search_console:
                if visible is None:
                    status["search_console"] = "no key access"
                elif site.search_console in visible:
                    status["search_console"] = "ok"
                else:
                    near = [v for v in visible if site.name in v]
                    status["search_console"] = "not shared with this key" + (
                        f"; visible instead: {', '.join(near)}" if near else ""
                    )
            if site.ga4_property:
                status["ga4"] = _ga4_check(profile, site.ga4_property)
            else:
                status["ga4"] = "not used"
            if profile.bing_keychain:
                status["bing"] = _bing_check(profile, site)
            entry["sites"].append(status)
        report.append(entry)
    return {"profiles": report}


def _bing_check(profile: Profile, site) -> str:
    from dottide import bing

    try:
        listed = bing.user_sites(bing.api_key(profile))
    except Exception as exc:  # noqa: BLE001
        return str(exc)
    return "ok" if bing.site_url(site) in listed else "not in Bing Webmaster Tools"


def _ga4_check(profile: Profile, prop: str) -> str:
    day = (date.today() - timedelta(days=1)).isoformat()
    try:
        google.ga4_sources(profile, prop, day, day)
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return str(exc)


def search_queries(
    site: str,
    by: str = "query",
    start: str | None = None,
    end: str | None = None,
    days: int = 28,
    compare: bool = False,
    limit: int = 25,
) -> dict:
    if by not in ("query", "page"):
        raise ValueError("by must be 'query' or 'page'")
    profile, s = find_site(load_profiles(), site)
    if not s.search_console:
        raise ValueError(f"{site} has no search_console property in its profile")
    first, last = period(start, end, days)
    fields = ("clicks", "impressions", "ctr", "position")
    rows = google.gsc_query(profile, s.search_console, str(first), str(last), by, limit)
    totals = google.gsc_query(profile, s.search_console, str(first), str(last), None).get(
        "total", dict.fromkeys(fields, 0)
    )
    result: dict = {
        "site": site,
        "property": s.search_console,
        "start": str(first),
        "end": str(last),
        "by": by,
    }
    if compare:
        p_first, p_last = previous(first, last)
        p_args = (profile, s.search_console, str(p_first), str(p_last))
        before = google.gsc_query(*p_args, by, 5000)
        p_totals = google.gsc_query(*p_args, None).get("total")
        result["previous_start"], result["previous_end"] = str(p_first), str(p_last)
        result["totals"] = _delta(totals, p_totals, fields)
        result["rows"] = [{by: k, **_delta(v, before.get(k), fields)} for k, v in rows.items()]
    else:
        result["totals"] = totals
        result["rows"] = [{by: k, **v} for k, v in rows.items()]
    return result


def _traffic_summary(rows: list[dict], limit: int) -> dict:
    ai: dict[str, dict] = {}
    for row in rows:
        if name := ai_assistant(row["source"]):
            bucket = ai.setdefault(name, {"assistant": name, "sessions": 0, "engaged_sessions": 0})
            bucket["sessions"] += row["sessions"]
            bucket["engaged_sessions"] += row["engaged_sessions"]
    return {
        "sessions": sum(r["sessions"] for r in rows),
        "ai_sessions": sum(a["sessions"] for a in ai.values()),
        "ai_referrals": sorted(ai.values(), key=lambda a: -a["sessions"]),
        "sources": rows[:limit],
    }


def traffic(
    site: str,
    start: str | None = None,
    end: str | None = None,
    days: int = 28,
    compare: bool = False,
    limit: int = 25,
) -> dict:
    profile, s = find_site(load_profiles(), site)
    if not s.ga4_property:
        raise ValueError(f"{site} has no GA4 property; traffic only covers sites with GA4")
    first, last = period(start, end, days)
    rows = google.ga4_sources(profile, s.ga4_property, str(first), str(last))
    result = {"site": site, "property": s.ga4_property, "start": str(first), "end": str(last)}
    result |= _traffic_summary(rows, limit)
    if compare:
        p_first, p_last = previous(first, last)
        p_rows = google.ga4_sources(profile, s.ga4_property, str(p_first), str(p_last))
        before = _traffic_summary(p_rows, limit)
        result["previous"] = {
            "start": str(p_first),
            "end": str(p_last),
            "sessions": before["sessions"],
            "ai_sessions": before["ai_sessions"],
            "ai_referrals": before["ai_referrals"],
        }
    return result


def store_stats(profile: str | None = None) -> dict:
    merged: dict[str, list] = {}
    for p in load_profiles():
        if profile and p.name != profile:
            continue
        for store, items in p.stores.items():
            merged.setdefault(store, [])
            merged[store] += [i for i in items if i not in merged[store]]
    return stores.collect(merged)
