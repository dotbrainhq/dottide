"""Pages and queries worth working on, worked out from Search Console rows.

Three kinds of opportunity, each item carrying its own numbers so an agent can quote them:
queries in striking distance, pages and queries losing clicks, and queries whose click-through
rate is low for their position. Low click-through is judged against the site's own other
queries at a similar position, not an outside benchmark.
"""

from __future__ import annotations

from collections import defaultdict
from statistics import median

from dottide import google
from dottide.config import find_site, load_profiles
from dottide.report import period, previous

ROWS = 5000
BANDS = ((1, 3), (4, 7), (8, 10))
MIN_BAND_ROWS = 3


def striking_distance(rows: dict[str, dict], min_impressions: int, limit: int) -> list[dict]:
    """Queries at positions 8 to 20: the bottom of page one and the top of page two."""
    items = [
        {"query": q, **r}
        for q, r in rows.items()
        if 8 <= r["position"] <= 20 and r["impressions"] >= min_impressions
    ]
    return sorted(items, key=lambda r: -r["impressions"])[:limit]


def losing(now: dict[str, dict], before: dict[str, dict], key: str, limit: int) -> list[dict]:
    """Rows with fewer clicks than in the previous period, biggest drop first."""
    items = []
    for name, old in before.items():
        new = now.get(name, {"clicks": 0, "impressions": 0, "position": None})
        if new["clicks"] < old["clicks"]:
            items.append(
                {
                    key: name,
                    "clicks": new["clicks"],
                    "previous_clicks": old["clicks"],
                    "change_clicks": new["clicks"] - old["clicks"],
                    "impressions": new["impressions"],
                    "previous_impressions": old["impressions"],
                    "position": new["position"],
                    "previous_position": old["position"],
                }
            )
    return sorted(items, key=lambda r: r["change_clicks"])[:limit]


def _band(position: float) -> tuple[int, int] | None:
    for low, high in BANDS:
        if low <= round(position) <= high:
            return low, high
    return None


def _is_brand(query: str, terms: tuple[str, ...]) -> bool:
    q = query.lower()
    return any(t.lower() in q for t in terms)


def branded(rows: dict[str, dict], terms: tuple[str, ...]) -> int:
    return sum(_is_brand(q, terms) for q in rows)


def low_ctr(
    rows: dict[str, dict], min_impressions: int, limit: int, brand_terms: tuple[str, ...] = ()
) -> list[dict]:
    """Queries on page one whose click-through is under half the site's median for that band.

    Brand queries click far more at the top, so they would lift the medians; they are left out.
    """
    rows = {q: r for q, r in rows.items() if not _is_brand(q, brand_terms)}
    by_band: dict[tuple[int, int], list[float]] = {}
    for r in rows.values():
        band = _band(r["position"])
        if band and r["impressions"] >= min_impressions:
            by_band.setdefault(band, []).append(r["ctr"])
    medians = {b: median(c) for b, c in by_band.items() if len(c) >= MIN_BAND_ROWS}
    items = []
    for q, r in rows.items():
        band = _band(r["position"])
        if band in medians and r["impressions"] >= min_impressions and r["ctr"] < medians[band] / 2:
            items.append(
                {
                    "query": q,
                    **r,
                    "band": f"{band[0]}-{band[1]}",
                    "band_median_ctr": round(medians[band], 2),
                }
            )
    return sorted(items, key=lambda r: -r["impressions"])[:limit]


def opportunities(
    site: str,
    start: str | None = None,
    end: str | None = None,
    days: int = 28,
    min_impressions: int = 5,
    limit: int = 10,
    country: str | None = None,
    device: str | None = None,
    search_type: str = "web",
) -> dict:
    filters = google.search_filter(country, device, search_type)
    google.require_queries(filters)
    profile, s = find_site(load_profiles(), site)
    if not s.search_console:
        raise ValueError(f"{site} has no search_console property in its profile")
    first, last = period(start, end, days)
    p_first, p_last = previous(first, last)
    prop = s.search_console

    def rows(dimension: str, a, b) -> dict[str, dict]:
        return google.gsc_query(profile, prop, str(a), str(b), dimension, ROWS, filters)

    queries, pages = rows("query", first, last), rows("page", first, last)
    old_queries, old_pages = rows("query", p_first, p_last), rows("page", p_first, p_last)

    result = {
        "site": site,
        "start": str(first),
        "end": str(last),
        "previous_start": str(p_first),
        "previous_end": str(p_last),
        "filters": filters,
        "min_impressions": min_impressions,
        "striking_distance": striking_distance(queries, min_impressions, limit),
        "losing_pages": losing(pages, old_pages, "page", limit),
        "losing_queries": losing(queries, old_queries, "query", limit),
        "low_ctr": low_ctr(queries, min_impressions, limit, s.brand_terms),
    }
    if s.brand_terms:
        result["brand_terms"] = list(s.brand_terms)
        result["brand_queries_left_out"] = branded(queries, s.brand_terms)
    if sum(r["impressions"] >= min_impressions for r in queries.values()) < 2 * MIN_BAND_ROWS:
        result["note"] = (
            f"Few queries reach {min_impressions} impressions in this range, so the lists are "
            "short. Try a longer range or a lower min_impressions."
        )
    return result


def competing(pairs: list[tuple[str, str, dict]], min_impressions: int, limit: int) -> list[dict]:
    """Queries where two or more pages each get at least `min_impressions`, biggest first."""
    by_query: dict[str, list[dict]] = defaultdict(list)
    for query, page, numbers in pairs:
        if numbers["impressions"] >= min_impressions:
            by_query[query].append({"page": page, **numbers})
    items = []
    for query, pages in by_query.items():
        if len(pages) < 2:
            continue
        pages.sort(key=lambda p: (-p["clicks"], -p["impressions"]))
        clicks = sum(p["clicks"] for p in pages)
        items.append(
            {
                "query": query,
                "impressions": sum(p["impressions"] for p in pages),
                "clicks": clicks,
                "top_page": pages[0]["page"] if clicks else None,
                "top_page_click_share": round(pages[0]["clicks"] / clicks * 100, 1)
                if clicks
                else None,
                "pages": pages,
            }
        )
    items.sort(key=lambda i: -i["impressions"])
    return items[:limit]


def competing_pages(
    site: str,
    start: str | None = None,
    end: str | None = None,
    days: int = 28,
    min_impressions: int = 5,
    limit: int = 10,
    country: str | None = None,
    device: str | None = None,
    search_type: str = "web",
) -> dict:
    filters = google.search_filter(country, device, search_type)
    google.require_queries(filters)
    profile, s = find_site(load_profiles(), site)
    if not s.search_console:
        raise ValueError(f"{site} has no search_console property in its profile")
    first, last = period(start, end, days)
    pairs = google.gsc_pairs(profile, s.search_console, str(first), str(last), filters)
    result: dict = {
        "site": site,
        "start": str(first),
        "end": str(last),
        "filters": filters,
        "min_impressions": min_impressions,
        "queries": competing(pairs, min_impressions, limit),
    }
    if not result["queries"]:
        result["note"] = (
            f"No query has two or more pages with {min_impressions}+ impressions each in this "
            "range. Try a longer range or a lower min_impressions."
        )
    return result
