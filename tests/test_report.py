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
        ("google", None),
        ("notchatgpt.com", None),
    ],
)
def test_ai_assistant(source, name):
    assert report.ai_assistant(source) == name


def test_delta_handles_missing_previous_row():
    row = report._delta({"clicks": 5}, None, ("clicks",))
    assert row == {"clicks": 5, "previous_clicks": None, "change_clicks": None}


def test_profile_file(tmp_path):
    path = tmp_path / "side.toml"
    path.write_text(
        '[key]\nkeychain = "dottide-side"\n'
        '[[sites]]\nname = "a.test"\nsearch_console = "sc-domain:a.test"\nga4_property = 42\n'
        '[stores]\nfirefox = ["x"]\n'
    )
    profile = load_profile(path)
    assert profile.name == "side"
    assert profile.key_source == "keychain:dottide-side"
    _, site = find_site([profile], "a.test")
    assert site.ga4_property == "42"
    with pytest.raises(ValueError):
        find_site([profile], "b.test")
