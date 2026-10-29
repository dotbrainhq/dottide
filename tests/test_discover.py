from dottide import discover
from dottide.config import load_profiles


def test_host_handles_every_property_shape():
    assert discover.host("sc-domain:Example.com") == "example.com"
    assert discover.host("https://www.example.com/") == "example.com"
    assert discover.host("http://blog.example.com/path") == "blog.example.com"


def test_domain_property_wins_over_url_prefix():
    new = discover.plan(["https://a.test/", "sc-domain:a.test"], [], [])
    assert new == [{"name": "a.test", "search_console": "sc-domain:a.test"}]


def test_ga4_stream_joins_its_search_console_site():
    streams = [
        {"property": "42", "name": "A", "measurement_id": "G-X", "url": "https://www.a.test"}
    ]
    new = discover.plan(["sc-domain:a.test"], streams, [])
    assert new[0]["ga4_property"] == "42"
    assert new[0]["measurement_id"] == "G-X"


def test_configured_sites_are_skipped_by_name_property_or_ga4():
    configured = [
        {"name": "a.test", "search_console": None, "ga4_property": None},
        {"name": "other", "search_console": "https://b.test/", "ga4_property": "7"},
    ]
    streams = [{"property": "7", "name": "C", "measurement_id": "G-C", "url": "https://c.test"}]
    new = discover.plan(
        ["sc-domain:a.test", "https://b.test/", "sc-domain:d.test"], streams, configured
    )
    assert [s["name"] for s in new] == ["d.test"]


def test_toml_output():
    toml = discover.to_toml(
        [
            {
                "name": "a.test",
                "search_console": "sc-domain:a.test",
                "ga4_property": "42",
                "measurement_id": "G-X",
            }
        ]
    )
    assert toml == (
        '[[sites]]\nname = "a.test"\n'
        'search_console = "sc-domain:a.test"\nga4_property = "42"   # G-X\n'
        '# brand_terms = ["a"]   # suggested from the domain; check it, then uncomment'
    )


def test_brand_guess_takes_the_name_from_the_domain():
    assert discover.brand_guess("themology.com") == ["themology"]
    assert discover.brand_guess("blog.example.co.uk") == ["example"]
    assert discover.brand_guess("my-site.com") == ["my-site", "my site"]
    assert discover.brand_guess("localhost") == []


def test_write_keeps_the_brand_suggestion_commented(tmp_path, monkeypatch):
    path = tmp_path / "main.toml"
    path.write_text('[key]\nkeychain = "k"\n')
    monkeypatch.setenv("DOTTIDE_CONFIG", str(path))
    discover.write(None, discover.to_toml([{"name": "themology.com"}]))
    assert '# brand_terms = ["themology"]' in path.read_text()
    site = load_profiles()[0].sites[0]
    assert site.brand_terms == ()


def test_write_puts_sites_before_stores(tmp_path, monkeypatch):
    path = tmp_path / "main.toml"
    path.write_text('[key]\nkeychain = "k"\n\n[stores]\nfirefox = ["x"]\n')
    monkeypatch.setenv("DOTTIDE_CONFIG", str(path))
    discover.write(None, '[[sites]]\nname = "a.test"')
    text = path.read_text()
    assert text.index("[[sites]]") < text.index("[stores]")
    assert 'firefox = ["x"]' in text
