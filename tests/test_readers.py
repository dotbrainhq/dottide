"""Every reader against saved sample responses. All names and numbers are made up."""

import json
from pathlib import Path

import httpx
import pytest

from dottide import google, indexhealth, stores, vitals
from dottide.config import Profile, Site

FIXTURES = Path(__file__).parent / "fixtures"
PROFILE = Profile(name="main", keychain="unused")


def fixture(name):
    return json.loads((FIXTURES / name).read_text())


class FakeHTTP:
    """Answers requests by the first route whose text appears in the URL."""

    def __init__(self, monkeypatch, routes):
        self.routes = routes
        self.calls = []
        monkeypatch.setattr(httpx, "request", self.request)
        monkeypatch.setattr(httpx, "get", self.get)
        monkeypatch.setattr(google, "_token", lambda profile: "token")

    def answer(self, method, url, params=None, json=None):
        self.calls.append((method, url, params, json))
        for part, (status, body, headers) in self.routes.items():
            if part in url:
                payload = fixture(body) if isinstance(body, str) else body
                return httpx.Response(status, json=payload, headers=headers or {})
        raise AssertionError(f"no route for {url}")

    def request(self, method, url, headers=None, timeout=None, params=None, json=None):
        return self.answer(method, url, params, json)

    def get(self, url, timeout=None, follow_redirects=None, params=None, headers=None):
        return self.answer("GET", url, params)


def test_gsc_properties_skip_unverified(monkeypatch):
    FakeHTTP(monkeypatch, {"/sites": (200, "gsc_sites.json", None)})
    assert google.gsc_properties(PROFILE) == ["sc-domain:a.test", "https://b.test/"]


def test_gsc_query_rows_and_totals(monkeypatch):
    http = FakeHTTP(monkeypatch, {"searchAnalytics": (200, "gsc_query_rows.json", None)})
    rows = google.gsc_query(PROFILE, "sc-domain:a.test", "2026-10-01", "2026-10-28", "query", 25)
    assert rows["first query"] == {"clicks": 12, "impressions": 400, "ctr": 3.0, "position": 4.3}
    assert http.calls[0][3]["dimensions"] == ["query"]
    assert "sc-domain%3Aa.test" in http.calls[0][1]

    FakeHTTP(monkeypatch, {"searchAnalytics": (200, "gsc_query_total.json", None)})
    total = google.gsc_query(PROFILE, "sc-domain:a.test", "2026-10-01", "2026-10-28", None)
    assert total == {"total": {"clicks": 40, "impressions": 2000, "ctr": 2.0, "position": 11.0}}


def test_google_errors_carry_googles_message(monkeypatch):
    FakeHTTP(monkeypatch, {"/sites": (403, "google_error_403.json", None)})
    with pytest.raises(RuntimeError, match="403: User does not have sufficient permission"):
        google.gsc_properties(PROFILE)


def test_ga4_sources_parse_numbers(monkeypatch):
    FakeHTTP(monkeypatch, {":runReport": (200, "ga4_report.json", None)})
    rows = google.ga4_sources(PROFILE, "111", "2026-10-01", "2026-10-28")
    assert rows[0] == {
        "source": "google",
        "medium": "organic",
        "sessions": 120,
        "engaged_sessions": 60,
        "users": 100,
    }


def test_ga4_web_streams_follow_pages(monkeypatch):
    FakeHTTP(
        monkeypatch,
        {
            "accountSummaries#next": (200, "ga4_summaries_page2.json", None),
            "accountSummaries": (200, "ga4_summaries_page1.json", None),
            "properties/111/dataStreams": (200, "ga4_streams_111.json", None),
            "properties/222/dataStreams": (200, "ga4_streams_222.json", None),
        },
    )
    # Route the second page by its token.
    original = httpx.request

    def paged(method, url, headers=None, timeout=None, params=None, json=None):
        if params and params.get("pageToken") == "next":
            url = url + "#next"
        return original(method, url, headers=headers, timeout=timeout, params=params, json=json)

    monkeypatch.setattr(httpx, "request", paged)
    streams = google.ga4_web_streams(PROFILE)
    assert [(s["property"], s["measurement_id"], s["url"]) for s in streams] == [
        ("111", "G-AAAA1111", "https://a.test"),
        ("222", "G-BBBB2222", "https://www.b.test/"),
    ]


def test_wordpress_org_keeps_seven_days_and_unescapes(monkeypatch):
    FakeHTTP(
        monkeypatch,
        {
            "plugins/info": (200, "wporg_info.json", None),
            "downloads.php": (200, "wporg_downloads.json", None),
        },
    )
    got = stores.wordpress_org("sample-plugin")
    assert got["name"] == "Sample – Plugin"
    assert len(got["downloads_by_day"]) == 7
    assert got["downloads_last_7_days"] == 35
    assert got["active_installs"] == 300


def test_wordpress_org_unknown_plugin(monkeypatch):
    FakeHTTP(monkeypatch, {"plugins/info": (200, {"error": "Plugin not found."}, None)})
    assert stores.wordpress_org("nope") == {"slug": "nope", "error": "Plugin not found."}


def test_firefox_addon_and_missing(monkeypatch):
    FakeHTTP(monkeypatch, {"/addon/sample-addon/": (200, "amo_addon.json", None)})
    got = stores.firefox("sample-addon")
    assert (got["average_daily_users"], got["rating"], got["num_ratings"], got["version"]) == (
        42,
        4.5,
        2,
        "1.0.0",
    )
    FakeHTTP(monkeypatch, {"/addon/": (404, {"detail": "Not found."}, None)})
    assert stores.firefox("gone") == {"slug": "gone", "error": "AMO 404"}


def test_github_skips_forks_and_sorts(monkeypatch):
    FakeHTTP(monkeypatch, {"/users/sample/repos": (200, "github_repos.json", None)})
    got = stores.github("sample")
    assert got["total_stars"] == 43
    assert [r["repo"] for r in got["repos"]] == ["big", "small"]


def test_github_rate_limit_says_when_it_resets(monkeypatch):
    headers = {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1793098629"}
    FakeHTTP(monkeypatch, {"/repos": (403, {"message": "rate limit"}, headers)})
    assert "resets 2026-" in stores.github("sample")["error"]


def test_core_web_vitals_end_to_end(monkeypatch):
    FakeHTTP(monkeypatch, {"pagespeedonline": (200, "pagespeed.json", None)})
    site = Site(name="a.test", profile="main", search_console="sc-domain:a.test")
    monkeypatch.setattr(vitals, "find_site", lambda profiles, name: (PROFILE, site))
    monkeypatch.setattr(vitals, "load_profiles", lambda: [PROFILE])
    got = vitals.core_web_vitals("a.test")
    assert got["page"] == "https://a.test/"
    assert got["page_field"]["inp_ms"] == {"p75": 250, "rating": "needs improvement"}
    assert got["page_field"]["cls"]["p75"] == 0.05
    assert got["site_field"] is None
    assert got["lab"]["performance_score"] == 91


def test_index_health_end_to_end(monkeypatch):
    FakeHTTP(
        monkeypatch,
        {
            "/sitemaps": (200, "sitemaps.json", None),
            "searchAnalytics": (
                200,
                {
                    "rows": [
                        {
                            "keys": ["https://a.test/x"],
                            "clicks": 3,
                            "impressions": 90,
                            "ctr": 0.03,
                            "position": 6,
                        }
                    ]
                },
                None,
            ),
            "urlInspection": (200, "inspection.json", None),
        },
    )
    site = Site(name="a.test", profile="main", search_console="sc-domain:a.test")
    monkeypatch.setattr(indexhealth, "find_site", lambda profiles, name: (PROFILE, site))
    monkeypatch.setattr(indexhealth, "load_profiles", lambda: [PROFILE])
    got = indexhealth.index_health("a.test", pages=5)
    assert got["sitemaps"][0]["urls_submitted"] == 12
    assert got["problems"] == ["https://a.test/x: Discovered - currently not indexed"]
