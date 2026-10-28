"""Pages and queries worth working on, worked out from Search Console rows.

Three kinds of opportunity, each item carrying its own numbers so an agent can quote them:
queries in striking distance, pages and queries losing clicks, and queries whose click-through
rate is low for their position. Low click-through is judged against the site's own other
queries at a similar position, not an outside benchmark.
"""

from __future__ import annotations

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


def low_ctr(rows: dict[str, dict], min_impressions: int, limit: int) -> list[dict]:
    """Queries on page one whose click-through is under half the site's median for that band."""
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
) -> dict:
    profile, s = find_site(load_profiles(), site)
    if not s.search_console:
        raise ValueError(f"{site} has no search_console property in its profile")
    first, last = period(start, end, days)
    p_first, p_last = previous(first, last)
    prop = s.search_console

    def rows(dimension: str, a, b) -> dict[str, dict]:
        return google.gsc_query(profile, prop, str(a), str(b), dimension, ROWS)

    queries, pages = rows("query", first, last), rows("page", first, last)
    old_queries, old_pages = rows("query", p_first, p_last), rows("page", p_first, p_last)

    result = {
        "site": site,
        "start": str(first),
        "end": str(last),
        "previous_start": str(p_first),
        "previous_end": str(p_last),
        "min_impressions": min_impressions,
        "striking_distance": striking_distance(queries, min_impressions, limit),
        "losing_pages": losing(pages, old_pages, "page", limit),
        "losing_queries": losing(queries, old_queries, "query", limit),
        "low_ctr": low_ctr(queries, min_impressions, limit),
    }
    if sum(r["impressions"] >= min_impressions for r in queries.values()) < 2 * MIN_BAND_ROWS:
        result["note"] = (
            f"Few queries reach {min_impressions} impressions in this range, so the lists are "
            "short. Try a longer range or a lower min_impressions."
        )
    return result
