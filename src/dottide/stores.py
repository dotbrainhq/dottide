"""Public store numbers that need no login: WordPress.org, Firefox Add-ons, GitHub."""

from __future__ import annotations

import html
import os
from datetime import UTC, datetime

import httpx

TIMEOUT = 20


def _get(url: str, **kwargs) -> httpx.Response:
    return httpx.get(url, timeout=TIMEOUT, follow_redirects=True, **kwargs)


def wordpress_org(slug: str) -> dict:
    info = _get(
        "https://api.wordpress.org/plugins/info/1.2/",
        params={"action": "plugin_information", "request[slug]": slug},
    ).json()
    if "error" in info:
        return {"slug": slug, "error": info["error"]}
    daily = _get(
        "https://api.wordpress.org/stats/plugin/1.0/downloads.php",
        params={"slug": slug, "limit": 8},
    ).json()
    # The endpoint returns full days only; keep the newest seven.
    week = dict(sorted(daily.items())[-7:])
    return {
        "slug": slug,
        "name": html.unescape(info.get("name") or ""),
        "version": info.get("version"),
        "active_installs": info.get("active_installs"),
        "rating": info.get("rating"),
        "num_ratings": info.get("num_ratings"),
        "support_threads": info.get("support_threads"),
        "support_threads_resolved": info.get("support_threads_resolved"),
        "last_updated": info.get("last_updated"),
        "downloads_last_7_days": sum(int(v) for v in week.values()),
        "downloads_by_day": {day: int(v) for day, v in week.items()},
    }


def firefox(slug: str) -> dict:
    response = _get(f"https://addons.mozilla.org/api/v5/addons/addon/{slug}/")
    if response.status_code != 200:
        return {"slug": slug, "error": f"AMO {response.status_code}"}
    data = response.json()
    return {
        "slug": slug,
        "version": (data.get("current_version") or {}).get("version"),
        "average_daily_users": data.get("average_daily_users"),
        "weekly_downloads": data.get("weekly_downloads"),
        "rating": data.get("ratings", {}).get("average"),
        "num_ratings": data.get("ratings", {}).get("count"),
    }


def github(owner: str) -> dict:
    """Stars and forks for an owner's public repos. Anonymous unless DOTTIDE_GITHUB_TOKEN is set."""
    headers = {"Accept": "application/vnd.github+json"}
    if token := os.environ.get("DOTTIDE_GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    response = _get(
        f"https://api.github.com/users/{owner}/repos",
        params={"type": "owner", "per_page": 100},
        headers=headers,
    )
    if response.status_code == 403 and response.headers.get("x-ratelimit-remaining") == "0":
        reset = datetime.fromtimestamp(int(response.headers["x-ratelimit-reset"]), UTC)
        return {"owner": owner, "error": f"GitHub rate limit, resets {reset:%Y-%m-%d %H:%M} UTC"}
    if response.status_code != 200:
        return {"owner": owner, "error": f"GitHub {response.status_code}"}
    repos = [
        {"repo": r["name"], "stars": r["stargazers_count"], "forks": r["forks_count"]}
        for r in response.json()
        if not r.get("fork") and not r.get("private")
    ]
    return {
        "owner": owner,
        "total_stars": sum(r["stars"] for r in repos),
        "repos": sorted(repos, key=lambda r: -r["stars"]),
    }


def collect(stores: dict) -> dict:
    """stores is the merged [stores] table: lists of slugs or owners per store."""
    return {
        "wordpress_org": [wordpress_org(s) for s in stores.get("wordpress_org", [])],
        "firefox": [firefox(s) for s in stores.get("firefox", [])],
        "github": [github(o) for o in stores.get("github_owners", [])],
    }
