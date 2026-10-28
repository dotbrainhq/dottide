from datetime import date

from dottide import bing
from dottide.config import Site

from .test_readers import FakeHTTP, fixture


def test_bing_date_reads_milliseconds():
    assert bing.bing_date("/Date(1761523200000-0700)/") == date(2025, 10, 27)
    assert bing.bing_date("/Date(1761523200000)/") == date(2025, 10, 27)


def test_summarize_adds_weeks_inside_the_range():
    rows = fixture("bing_query_stats.json")["d"]
    got = bing.summarize(rows, date(2025, 10, 1), date(2025, 10, 31), 10)
    assert got[0] == {"query": "alpha", "clicks": 5, "impressions": 100, "position": 5.2}
    assert [r["query"] for r in got] == ["alpha", "beta"]


def test_totals_inside_the_range():
    rows = fixture("bing_traffic.json")["d"]
    assert bing.totals(rows, date(2025, 10, 1), date(2025, 10, 31)) == {
        "clicks": 6,
        "impressions": 120,
    }


def test_site_url_from_search_console():
    assert bing.site_url(Site("a.test", "p", "sc-domain:a.test")) == "https://a.test/"
    assert bing.site_url(Site("b.test", "p", "https://b.test/")) == "https://b.test/"
    assert (
        bing.site_url(Site("c.test", "p", None, None, "https://www.c.test/"))
        == "https://www.c.test/"
    )


def test_user_sites_keeps_verified(monkeypatch):
    FakeHTTP(monkeypatch, {"GetUserSites": (200, "bing_sites.json", None)})
    assert bing.user_sites("key") == ["https://a.test/"]


def test_bing_errors_carry_the_message(monkeypatch):
    FakeHTTP(monkeypatch, {"GetUserSites": (400, {"Message": "Invalid API key"}, None)})
    try:
        bing.user_sites("bad")
    except RuntimeError as exc:
        assert "Invalid API key" in str(exc)
    else:
        raise AssertionError("expected an error")


def test_api_key_goes_in_the_query(monkeypatch):
    http = FakeHTTP(monkeypatch, {"GetUserSites": (200, "bing_sites.json", None)})
    bing.user_sites("key")
    assert http.calls[0][2]["apikey"] == "key"
