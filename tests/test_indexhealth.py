from datetime import UTC, datetime

from dottide import indexhealth as ih

NOW = datetime(2026, 10, 28, tzinfo=UTC)


def test_sitemap_summary_and_stale_problem():
    raw = {
        "path": "https://a.test/old.xml",
        "lastDownloaded": "2026-04-01T06:44:33.294Z",
        "errors": "1",
        "warnings": "2",
        "contents": [{"type": "web", "submitted": "39"}],
    }
    s = ih.sitemap_summary(raw, NOW)
    assert (s["errors"], s["warnings"], s["urls_submitted"], s["days_since_read"]) == (
        1,
        2,
        39,
        209,
    )
    problems = ih.sitemap_problems(s)
    assert len(problems) == 2
    assert "1 errors, 2 warnings" in problems[0]
    assert "209 days ago" in problems[1]


def test_healthy_sitemap_has_no_problems():
    s = ih.sitemap_summary({"path": "x", "lastDownloaded": "2026-10-20T00:00:00Z"}, NOW)
    assert ih.sitemap_problems(s) == []


def test_page_problems_for_unindexed_and_canonical_mismatch():
    ok = ih.page_summary(
        "https://a.test/a", 5, {"verdict": "PASS", "coverageState": "Submitted and indexed"}
    )
    assert ih.page_problems(ok) == []
    bad = ih.page_summary(
        "https://a.test/b",
        2,
        {
            "verdict": "NEUTRAL",
            "coverageState": "Crawled - currently not indexed",
            "googleCanonical": "https://a.test/c",
            "userCanonical": "https://a.test/b",
        },
    )
    problems = ih.page_problems(bad)
    assert "Crawled - currently not indexed" in problems[0]
    assert "https://a.test/c" in problems[1]
