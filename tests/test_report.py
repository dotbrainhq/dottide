from datetime import date

import pytest

from dottide import report
from dottide.config import find_site, load_profile


def test_previous_period_has_same_length_and_ends_the_day_before():
    assert report.previous(date(2026, 10, 1), date(2026, 10, 28)) == (
        date(2026, 9, 3),
        date(2026, 9, 30),
    )


def test_period_defaults_end_three_days_ago():
    first, last = report.period(None, None, 7)
    assert (last - first).days == 6
    assert (date.today() - last).days == report.GSC_LAG_DAYS


def test_period_rejects_start_after_end():
    with pytest.raises(ValueError):
        report.period("2026-10-10", "2026-10-01", 7)


@pytest.mark.parametrize(
    ("source", "name"),
    [
        ("chatgpt.com", "ChatGPT"),
        ("www.perplexity.ai", "Perplexity"),
        ("claude.ai", "Claude"),
        ("gemini.google.com", "Gemini"),
        ("gemini", "Gemini"),
        ("google", None),
        ("notchatgpt.com", None),
    ],
)
def test_ai_assistant(source, name):
    assert report.ai_assistant(source) == name


def test_ai_assistant_trusts_ga4_medium_for_unknown_sources():
    assert report.ai_assistant("newbot.example", "ai-assistant") == "newbot.example"
    assert report.ai_assistant("newbot.example", "referral") is None


def test_traffic_summary_counts_every_ai_row():
    rows = [
        {"source": "google", "medium": "organic", "sessions": 80, "engaged_sessions": 46},
        {"source": "chatgpt.com", "medium": "ai-assistant", "sessions": 17, "engaged_sessions": 5},
        {"source": "gemini", "medium": "ai-assistant", "sessions": 1, "engaged_sessions": 1},
    ]
    got = report._traffic_summary(rows, limit=10)
    assert got["ai_sessions"] == 18
    assert [a["assistant"] for a in got["ai_referrals"]] == ["ChatGPT", "Gemini"]


def test_ai_landing_pages_group_by_assistant_like_ai_referrals():
    rows = [
        {"source": "chatgpt.com", "medium": "referral", "landing_page": "/a/", "sessions": 3},
        {"source": "chat.openai.com", "medium": "referral", "landing_page": "/b/", "sessions": 5},
        {"source": "chatgpt.com", "medium": "referral", "landing_page": "/b/", "sessions": 2},
        {"source": "chatgpt.com", "medium": "referral", "landing_page": "/c/", "sessions": 1},
        {"source": "gemini", "medium": "ai-assistant", "landing_page": "/a/", "sessions": 1},
        {"source": "google", "medium": "organic", "landing_page": "/a/", "sessions": 90},
    ]
    for r in rows:
        r["engaged_sessions"] = 1
    got = report.ai_landing_pages(rows, limit=2)
    assert set(got) == {"ChatGPT", "Gemini"}
    assert got["ChatGPT"] == [
        {"page": "/b/", "sessions": 7, "engaged_sessions": 2},
        {"page": "/a/", "sessions": 3, "engaged_sessions": 1},
    ]
    assert "chatgpt\\.com" in report.AI_SOURCE_PATTERN
    assert "gemini" in report.AI_SOURCE_PATTERN


def test_delta_handles_missing_previous_row():
    row = report._delta({"clicks": 5}, None, ("clicks",))
    assert row == {"clicks": 5, "previous_clicks": None, "change_clicks": None}


def test_profile_file(tmp_path):
    path = tmp_path / "side.toml"
    path.write_text(
        '[key]\nkeychain = "dottide-side"\n'
        '[[sites]]\nname = "a.test"\nsearch_console = "sc-domain:a.test"\nga4_property = 42\n'
        'brand_terms = ["Acme", "acme inc"]\n'
        '[stores]\nfirefox = ["x"]\n'
    )
    profile = load_profile(path)
    assert profile.name == "side"
    assert profile.key_source == "keychain:dottide-side"
    _, site = find_site([profile], "a.test")
    assert site.ga4_property == "42"
    assert site.brand_terms == ("acme", "acme inc")
    with pytest.raises(ValueError):
        find_site([profile], "b.test")


def test_init_profile_writes_template_once(tmp_path, monkeypatch):
    from dottide import config

    monkeypatch.setattr(config, "DEFAULT_DIR", tmp_path / "dottide")
    path = config.init_profile("main")
    assert path.read_text().startswith("# dotTide profile")
    assert oct(path.stat().st_mode)[-3:] == "600"
    assert config.load_profile(path).keychain == "dottide-main"
    with pytest.raises(FileExistsError):
        config.init_profile("main")
