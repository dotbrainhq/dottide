"""Filters, one page's queries, and competing pages. All names and numbers are made up."""

import pytest

from dottide import google, prompts, report
from dottide import opportunities as op
from dottide.config import Site

from .test_readers import PROFILE, FakeHTTP

SITE = Site(name="a.test", profile="main", search_console="sc-domain:a.test")


def numbers(clicks, impressions, position=5.0):
    return {"clicks": clicks, "impressions": impressions, "ctr": 0, "position": position}


def test_search_filter_checks_and_lowercases():
    assert google.search_filter("USA", "Mobile") == {
        "search_type": "web",
        "country": "usa",
        "device": "mobile",
    }
    assert google.search_filter() == {"search_type": "web"}
    for bad in ({"country": "us"}, {"device": "watch"}, {"search_type": "shopping"}):
        with pytest.raises(ValueError):
            google.search_filter(**bad)


def test_discover_and_google_news_have_no_query_rows():
    google.require_queries({"search_type": "image"})
    for kind in google.PAGES_ONLY:
        with pytest.raises(ValueError, match="pages only"):
            google.require_queries({"search_type": kind})


def test_gsc_query_sends_type_and_filters(monkeypatch):
    http = FakeHTTP(monkeypatch, {"searchAnalytics": (200, {"rows": []}, None)})
    filters = {**google.search_filter("bgd", "desktop", "image"), "page": "https://a.test/x/"}
    google.gsc_query(PROFILE, "sc-domain:a.test", "2026-10-01", "2026-10-28", "query", 5, filters)
    body = http.calls[0][3]
    assert body["type"] == "image"
    assert body["dimensionFilterGroups"] == [
        {
            "filters": [
                {"dimension": "country", "operator": "equals", "expression": "bgd"},
                {"dimension": "device", "operator": "equals", "expression": "desktop"},
                {"dimension": "page", "operator": "equals", "expression": "https://a.test/x/"},
            ]
        }
    ]


def test_web_search_sends_no_type_or_filters(monkeypatch):
    http = FakeHTTP(monkeypatch, {"searchAnalytics": (200, {"rows": []}, None)})
    google.gsc_query(PROFILE, "sc-domain:a.test", "2026-10-01", "2026-10-28", None, 1, {})
    assert "type" not in http.calls[0][3]
    assert "dimensionFilterGroups" not in http.calls[0][3]


def test_rows_without_position_keep_none(monkeypatch):
    discover = {
        "rows": [{"keys": ["https://a.test/"], "clicks": 3, "impressions": 90, "ctr": 0.03}]
    }
    FakeHTTP(monkeypatch, {"searchAnalytics": (200, discover, None)})
    rows = google.gsc_query(PROFILE, "sc-domain:a.test", "2026-10-01", "2026-10-28", "page")
    assert rows["https://a.test/"]["position"] is None


def test_gsc_pairs_pages_until_a_short_page(monkeypatch):
    def page_of(n, start):
        return [
            {"keys": [f"q{start + i}", "https://a.test/"], "clicks": 0, "impressions": 1, "ctr": 0}
            for i in range(n)
        ]

    pages = iter([{"rows": page_of(25_000, 0)}, {"rows": page_of(3, 25_000)}])
    http = FakeHTTP(monkeypatch, {})
    monkeypatch.setattr(
        http, "answer", lambda *a, **k: __import__("httpx").Response(200, json=next(pages))
    )
    pairs = google.gsc_pairs(PROFILE, "sc-domain:a.test", "2026-10-01", "2026-10-28")
    assert len(pairs) == 25_003
    assert pairs[-1][0] == "q25002"


def test_hidden_share_is_what_query_rows_leave_out():
    totals = numbers(1, 109)
    rows = {"a": numbers(0, 30), "b": numbers(0, 14)}
    assert report._hidden(totals, rows) == {
        "clicks": 1,
        "clicks_share": 100.0,
        "impressions": 65,
        "impressions_share": 59.6,
    }
    assert report._hidden(numbers(0, 0), {})["impressions_share"] == 0


def test_page_queries_reads_one_page(monkeypatch):
    calls = []

    def fake_query(profile, prop, start, end, dimension, limit=25, filters=None):
        calls.append((dimension, limit, filters))
        if dimension == "query":
            return {"first": numbers(2, 40, 3.0), "second": numbers(1, 20, 8.0)}
        return {"total": numbers(5, 100, 6.0)}

    monkeypatch.setattr(report, "find_site", lambda profiles, site: (PROFILE, SITE))
    monkeypatch.setattr(report, "load_profiles", lambda: [])
    monkeypatch.setattr(google, "gsc_query", fake_query)
    got = report.page_queries("a.test", "https://a.test/x/", days=28, limit=1, device="mobile")
    assert [r["query"] for r in got["rows"]] == ["first"]
    assert got["hidden"]["clicks"] == 2
    assert got["hidden"]["impressions"] == 40
    assert got["filters"] == {"search_type": "web", "device": "mobile"}
    assert calls[0] == (
        "query",
        25_000,
        {"search_type": "web", "device": "mobile", "page": "https://a.test/x/"},
    )


def test_page_queries_wants_a_full_url():
    with pytest.raises(ValueError, match="full URL"):
        report.page_queries("a.test", "/x/")


def test_competing_lists_queries_with_two_pages_over_the_minimum():
    pairs = [
        ("shared", "https://a.test/one/", numbers(6, 120, 4.0)),
        ("shared", "https://a.test/two/", numbers(2, 80, 9.0)),
        ("shared", "https://a.test/tiny/", numbers(0, 2, 30.0)),
        ("bigger", "https://a.test/one/", numbers(0, 200, 12.0)),
        ("bigger", "https://a.test/three/", numbers(0, 150, 15.0)),
        ("alone", "https://a.test/one/", numbers(9, 500, 2.0)),
    ]
    got = op.competing(pairs, min_impressions=5, limit=10)
    assert [q["query"] for q in got] == ["bigger", "shared"]
    shared = got[1]
    assert [p["page"] for p in shared["pages"]] == ["https://a.test/one/", "https://a.test/two/"]
    assert shared["top_page_click_share"] == 75.0
    assert got[0]["top_page"] is None


def test_what_to_work_on_checks_competing_pages():
    assert "`competing_pages`" in prompts.what_to_work_on("a.test")
