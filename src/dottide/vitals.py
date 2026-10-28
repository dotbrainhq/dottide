"""Core Web Vitals from PageSpeed Insights: real-user numbers from the Chrome UX Report when
Google has enough visits, and a lab run from Lighthouse every time."""

from __future__ import annotations

from dottide import google
from dottide.config import find_site, load_profiles

# Google's thresholds: (good up to, poor above).
THRESHOLDS = {
    "lcp_ms": (2500, 4000),
    "inp_ms": (200, 500),
    "cls": (0.1, 0.25),
}
FIELD_METRICS = {
    "LARGEST_CONTENTFUL_PAINT_MS": "lcp_ms",
    "INTERACTION_TO_NEXT_PAINT": "inp_ms",
    "CUMULATIVE_LAYOUT_SHIFT_SCORE": "cls",
}
LAB_AUDITS = {
    "largest-contentful-paint": "lcp",
    "cumulative-layout-shift": "cls",
    "total-blocking-time": "tbt",
    "first-contentful-paint": "fcp",
    "speed-index": "speed_index",
}


def rate(metric: str, value: float) -> str:
    good, poor = THRESHOLDS[metric]
    if value <= good:
        return "good"
    return "poor" if value > poor else "needs improvement"


def field(experience: dict | None) -> dict | None:
    """Real-user 75th-percentile values, or None when Google has too little data."""
    metrics = (experience or {}).get("metrics") or {}
    out = {}
    for source, name in FIELD_METRICS.items():
        if source in metrics:
            value = metrics[source]["percentile"]
            if name == "cls":
                value = value / 100
            out[name] = {"p75": value, "rating": rate(name, value)}
    if not out:
        return None
    out["passes"] = all(m["rating"] == "good" for m in out.values())
    return out


def lab(result: dict) -> dict:
    audits = result.get("audits", {})
    score = result.get("categories", {}).get("performance", {}).get("score")
    return {
        "performance_score": None if score is None else round(score * 100),
        **{name: audits.get(key, {}).get("displayValue") for key, name in LAB_AUDITS.items()},
    }


def home_page(search_console: str | None, name: str) -> str:
    if search_console and search_console.startswith("http"):
        return search_console
    domain = (search_console or name).removeprefix("sc-domain:")
    return f"https://{domain}/"


def core_web_vitals(site: str, page: str | None = None, strategy: str = "mobile") -> dict:
    if strategy not in ("mobile", "desktop"):
        raise ValueError("strategy must be 'mobile' or 'desktop'")
    profile, s = find_site(load_profiles(), site)
    url = page or home_page(s.search_console, s.name)
    data = google.pagespeed(profile, url, strategy)
    result = {
        "site": site,
        "page": url,
        "strategy": strategy,
        "page_field": field(data.get("loadingExperience")),
        "site_field": field(data.get("originLoadingExperience")),
        "lab": lab(data.get("lighthouseResult", {})),
    }
    if result["page_field"] is None and result["site_field"] is None:
        result["note"] = (
            "Google has too few real visits for field data, so only the lab run is shown. "
            "Lab numbers come from one simulated load and move between runs."
        )
    return result
