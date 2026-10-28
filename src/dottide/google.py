"""Search Console and GA4 reads through a service account. Read-only scopes only."""

from __future__ import annotations

from urllib.parse import quote

import httpx
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from dottide.config import Profile

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/analytics.readonly",
    # PageSpeed Insights only needs an identity; quota comes from the key's Cloud project.
    "openid",
]
GSC = "https://searchconsole.googleapis.com/webmasters/v3"
GSC_INSPECT = "https://searchconsole.googleapis.com/v1"
PAGESPEED = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
GA4_DATA = "https://analyticsdata.googleapis.com/v1beta"
GA4_ADMIN = "https://analyticsadmin.googleapis.com/v1beta"

_credentials: dict[str, service_account.Credentials] = {}


def client_email(profile: Profile) -> str:
    return profile.key_info()["client_email"]


def _token(profile: Profile) -> str:
    creds = _credentials.get(profile.name)
    if creds is None:
        creds = service_account.Credentials.from_service_account_info(
            profile.key_info(), scopes=SCOPES
        )
        _credentials[profile.name] = creds
    if not creds.valid:
        creds.refresh(Request())
    return creds.token


def _call(profile: Profile, method: str, url: str, timeout: int = 30, **kwargs) -> dict:
    headers = {"Authorization": f"Bearer {_token(profile)}"}
    response = httpx.request(method, url, headers=headers, timeout=timeout, **kwargs)
    if response.status_code >= 400:
        try:
            message = response.json()["error"]["message"]
        except (ValueError, KeyError, TypeError):
            message = response.text[:200]
        raise RuntimeError(f"Google API {response.status_code}: {message}")
    return response.json()


def gsc_properties(profile: Profile) -> list[str]:
    entries = _call(profile, "GET", f"{GSC}/sites").get("siteEntry", [])
    return [e["siteUrl"] for e in entries if e.get("permissionLevel") != "siteUnverifiedUser"]


SEARCH_TYPES = ("web", "image", "video", "news", "discover", "googleNews")
DEVICES = ("desktop", "mobile", "tablet")
# The API refuses query rows for these two and reports no position.
PAGES_ONLY = ("discover", "googleNews")
MAX_PAIR_ROWS = 100_000


def search_filter(
    country: str | None = None, device: str | None = None, search_type: str = "web"
) -> dict:
    """Checked Search Console filters, in the form results echo them back."""
    if search_type not in SEARCH_TYPES:
        raise ValueError(f"search_type must be one of {', '.join(SEARCH_TYPES)}")
    found: dict = {"search_type": search_type}
    if country:
        if len(country) != 3 or not country.isalpha():
            raise ValueError("country takes a three-letter ISO 3166-1 code, like usa or bgd")
        found["country"] = country.lower()
    if device:
        if device.lower() not in DEVICES:
            raise ValueError(f"device must be one of {', '.join(DEVICES)}")
        found["device"] = device.lower()
    return found


def require_queries(filters: dict) -> None:
    if filters.get("search_type") in PAGES_ONLY:
        raise ValueError(
            f"{filters['search_type']} reports pages only: Search Console has no query rows "
            "for it. Use search_queries with by='page'."
        )


def _body(start: str, end: str, limit: int, filters: dict | None) -> dict:
    body: dict = {"startDate": start, "endDate": end, "rowLimit": limit}
    filters = filters or {}
    if filters.get("search_type", "web") != "web":
        body["type"] = filters["search_type"]
    clauses = [
        {"dimension": name, "operator": "equals", "expression": filters[name]}
        for name in ("country", "device", "page")
        if filters.get(name)
    ]
    if clauses:
        body["dimensionFilterGroups"] = [{"filters": clauses}]
    return body


def _numbers(row: dict) -> dict:
    position = row.get("position")
    return {
        "clicks": row["clicks"],
        "impressions": row["impressions"],
        "ctr": round(row.get("ctr", 0) * 100, 2),
        "position": round(position, 1) if position is not None else None,
    }


def gsc_query(
    profile: Profile,
    prop: str,
    start: str,
    end: str,
    dimension: str | None,
    limit: int = 25,
    filters: dict | None = None,
) -> dict[str, dict]:
    """Rows keyed by query or page. With no dimension, one row keyed "total". `filters` takes
    search_filter()'s result, plus "page" to read a single page."""
    body = _body(start, end, limit, filters)
    if dimension:
        body["dimensions"] = [dimension]
    url = f"{GSC}/sites/{quote(prop, safe='')}/searchAnalytics/query"
    rows = _call(profile, "POST", url, json=body).get("rows", [])
    return {(row["keys"][0] if dimension else "total"): _numbers(row) for row in rows}


def gsc_pairs(
    profile: Profile, prop: str, start: str, end: str, filters: dict | None = None
) -> list[tuple[str, str, dict]]:
    """Every query and page pair in the range, paged 25,000 rows at a time."""
    url = f"{GSC}/sites/{quote(prop, safe='')}/searchAnalytics/query"
    pairs: list[tuple[str, str, dict]] = []
    while len(pairs) < MAX_PAIR_ROWS:
        body = {**_body(start, end, 25_000, filters), "dimensions": ["query", "page"]}
        body["startRow"] = len(pairs)
        rows = _call(profile, "POST", url, json=body).get("rows", [])
        pairs += [(row["keys"][0], row["keys"][1], _numbers(row)) for row in rows]
        if len(rows) < 25_000:
            break
    return pairs


def ga4_sources(profile: Profile, prop: str, start: str, end: str) -> list[dict]:
    """Sessions by source and medium, biggest first."""
    body = {
        "dateRanges": [{"startDate": start, "endDate": end}],
        "dimensions": [{"name": "sessionSource"}, {"name": "sessionMedium"}],
        "metrics": [{"name": "sessions"}, {"name": "engagedSessions"}, {"name": "totalUsers"}],
        "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
        "limit": 1000,
    }
    data = _call(profile, "POST", f"{GA4_DATA}/properties/{prop}:runReport", json=body)
    rows = []
    for row in data.get("rows", []):
        source, medium = (d["value"] for d in row["dimensionValues"])
        sessions, engaged, users = (int(m["value"]) for m in row["metricValues"])
        rows.append(
            {
                "source": source,
                "medium": medium,
                "sessions": sessions,
                "engaged_sessions": engaged,
                "users": users,
            }
        )
    return rows


def ga4_web_streams(profile: Profile) -> list[dict]:
    """Every GA4 web stream the key can read, with the site address it tracks."""
    streams, page = [], None
    while True:
        params = {"pageSize": 200, **({"pageToken": page} if page else {})}
        data = _call(profile, "GET", f"{GA4_ADMIN}/accountSummaries", params=params)
        for account in data.get("accountSummaries", []):
            for prop in account.get("propertySummaries", []):
                pid = prop["property"].split("/")[1]
                url = f"{GA4_ADMIN}/properties/{pid}/dataStreams"
                for stream in _call(profile, "GET", url).get("dataStreams", []):
                    web = stream.get("webStreamData")
                    if web:
                        streams.append(
                            {
                                "property": pid,
                                "name": prop.get("displayName"),
                                "measurement_id": web.get("measurementId"),
                                "url": web.get("defaultUri", ""),
                            }
                        )
        page = data.get("nextPageToken")
        if not page:
            return streams


def gsc_sitemaps(profile: Profile, prop: str) -> list[dict]:
    url = f"{GSC}/sites/{quote(prop, safe='')}/sitemaps"
    return _call(profile, "GET", url).get("sitemap", [])


def gsc_inspect(profile: Profile, prop: str, page: str) -> dict:
    """Google's index status for one URL. Read-only; it never requests indexing."""
    body = {"inspectionUrl": page, "siteUrl": prop}
    data = _call(profile, "POST", f"{GSC_INSPECT}/urlInspection/index:inspect", json=body)
    return data.get("inspectionResult", {}).get("indexStatusResult", {})


def pagespeed(profile: Profile, url: str, strategy: str) -> dict:
    params = {"url": url, "strategy": strategy, "category": "performance"}
    return _call(profile, "GET", PAGESPEED, params=params, timeout=120)
