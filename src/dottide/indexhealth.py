"""Index health: the state of each sitemap, and whether a site's top pages are in Google's index.

Everything here reads. It never submits a sitemap or requests indexing.
"""

from __future__ import annotations

from datetime import UTC, datetime

from dottide import google
from dottide.config import find_site, load_profiles
from dottide.report import period

STALE_DAYS = 30
MAX_PAGES = 50


def sitemap_summary(raw: dict, now: datetime) -> dict:
    downloaded = raw.get("lastDownloaded")
    age = None
    if downloaded:
        age = (now - datetime.fromisoformat(downloaded.replace("Z", "+00:00"))).days
    return {
        "path": raw.get("path"),
        "last_read": downloaded,
        "days_since_read": age,
        "pending": raw.get("isPending", False),
        "is_index": raw.get("isSitemapsIndex", False),
        "errors": int(raw.get("errors", 0)),
        "warnings": int(raw.get("warnings", 0)),
        "urls_submitted": sum(int(c.get("submitted", 0)) for c in raw.get("contents") or []),
    }


def sitemap_problems(sitemap: dict) -> list[str]:
    path, problems = sitemap["path"], []
    if sitemap["errors"] or sitemap["warnings"]:
        problems.append(f"{path}: {sitemap['errors']} errors, {sitemap['warnings']} warnings")
    if sitemap["days_since_read"] is not None and sitemap["days_since_read"] > STALE_DAYS:
        problems.append(
            f"{path}: last read by Google {sitemap['days_since_read']} days ago; remove it "
            "from Search Console if the site no longer serves it"
        )
    return problems


def page_summary(url: str, clicks: float, status: dict) -> dict:
    google_canonical, user_canonical = status.get("googleCanonical"), status.get("userCanonical")
    return {
        "page": url,
        "clicks": clicks,
        "verdict": status.get("verdict"),
        "coverage": status.get("coverageState"),
        "indexing": status.get("indexingState"),
        "robots_txt": status.get("robotsTxtState"),
        "fetch": status.get("pageFetchState"),
        "last_crawl": status.get("lastCrawlTime"),
        "google_canonical": google_canonical,
        "canonical_mismatch": bool(
            google_canonical and user_canonical and google_canonical != user_canonical
        ),
    }


def page_problems(page: dict) -> list[str]:
    problems = []
    if page["verdict"] and page["verdict"] != "PASS":
        problems.append(f"{page['page']}: {page['coverage'] or page['verdict']}")
    if page["canonical_mismatch"]:
        problems.append(f"{page['page']}: Google picked {page['google_canonical']} as canonical")
    return problems


def index_health(site: str, pages: int = 10, days: int = 28) -> dict:
    profile, s = find_site(load_profiles(), site)
    if not s.search_console:
        raise ValueError(f"{site} has no search_console property in its profile")
    prop, now = s.search_console, datetime.now(UTC)

    sitemaps = [sitemap_summary(x, now) for x in google.gsc_sitemaps(profile, prop)]
    first, last = period(None, None, days)
    top = google.gsc_query(profile, prop, str(first), str(last), "page", min(pages, MAX_PAGES))
    checked = []
    for url, numbers in top.items():
        try:
            checked.append(
                page_summary(url, numbers["clicks"], google.gsc_inspect(profile, prop, url))
            )
        except RuntimeError as exc:
            checked.append({"page": url, "clicks": numbers["clicks"], "error": str(exc)})

    problems = [p for m in sitemaps for p in sitemap_problems(m)]
    problems += [p for c in checked if "error" not in c for p in page_problems(c)]
    if not sitemaps:
        problems.append("No sitemap is submitted in Search Console for this property")
    return {
        "site": site,
        "property": prop,
        "sitemaps": sitemaps,
        "top_pages_checked": checked,
        "problems": problems,
    }
