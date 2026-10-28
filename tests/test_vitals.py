from dottide import vitals


def test_rating_uses_googles_thresholds():
    assert vitals.rate("lcp_ms", 2500) == "good"
    assert vitals.rate("lcp_ms", 3000) == "needs improvement"
    assert vitals.rate("inp_ms", 600) == "poor"
    assert vitals.rate("cls", 0.12) == "needs improvement"


def test_field_reads_percentiles_and_scales_cls():
    experience = {
        "metrics": {
            "LARGEST_CONTENTFUL_PAINT_MS": {"percentile": 2100, "category": "FAST"},
            "INTERACTION_TO_NEXT_PAINT": {"percentile": 150, "category": "FAST"},
            "CUMULATIVE_LAYOUT_SHIFT_SCORE": {"percentile": 30, "category": "SLOW"},
        }
    }
    got = vitals.field(experience)
    assert got["cls"] == {"p75": 0.3, "rating": "poor"}
    assert got["lcp_ms"]["rating"] == "good"
    assert got["passes"] is False


def test_field_is_none_without_data():
    assert vitals.field({}) is None
    assert vitals.field(None) is None


def test_lab_and_home_page():
    result = {
        "categories": {"performance": {"score": 0.87}},
        "audits": {"largest-contentful-paint": {"displayValue": "2.4 s"}},
    }
    got = vitals.lab(result)
    assert got["performance_score"] == 87
    assert got["lcp"] == "2.4 s"
    assert got["tbt"] is None
    assert vitals.home_page("sc-domain:a.test", "a.test") == "https://a.test/"
    assert vitals.home_page("https://b.test/", "b.test") == "https://b.test/"
