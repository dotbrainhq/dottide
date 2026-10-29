from dottide import opportunities as op


def row(clicks, impressions, position):
    ctr = round(clicks / impressions * 100, 2) if impressions else 0
    return {"clicks": clicks, "impressions": impressions, "ctr": ctr, "position": position}


def test_striking_distance_keeps_positions_8_to_20_by_impressions():
    rows = {"a": row(1, 50, 9.0), "b": row(0, 80, 15.2), "c": row(5, 90, 3.0), "d": row(0, 2, 12.0)}
    got = op.striking_distance(rows, min_impressions=5, limit=10)
    assert [r["query"] for r in got] == ["b", "a"]


def test_losing_includes_rows_that_vanished():
    before = {"/a": row(10, 100, 4.0), "/b": row(3, 40, 6.0), "/c": row(1, 10, 9.0)}
    now = {"/a": row(4, 90, 5.0), "/c": row(2, 12, 8.0)}
    got = op.losing(now, before, "page", limit=10)
    assert [(r["page"], r["change_clicks"]) for r in got] == [("/a", -6), ("/b", -3)]
    assert got[1]["position"] is None


def test_low_ctr_compares_with_the_sites_own_band_median():
    rows = {
        "good1": row(10, 100, 2.0),
        "good2": row(12, 100, 2.4),
        "good3": row(9, 100, 1.6),
        "weak": row(1, 200, 2.0),
        "tiny": row(0, 3, 2.0),
    }
    got = op.low_ctr(rows, min_impressions=5, limit=10)
    assert [r["query"] for r in got] == ["weak"]
    assert got[0]["band"] == "1-3"
    assert got[0]["band_median_ctr"] == 9.5


def test_low_ctr_needs_enough_rows_in_a_band():
    rows = {"a": row(10, 100, 5.0), "b": row(0, 100, 5.0)}
    assert op.low_ctr(rows, min_impressions=5, limit=10) == []


def test_low_ctr_leaves_brand_queries_out_of_medians_and_list():
    rows = {
        "acme": row(60, 100, 1.2),
        "acme login": row(70, 100, 1.4),
        "Acme pricing": row(80, 100, 2.0),
        "good1": row(10, 100, 2.0),
        "good2": row(12, 100, 2.4),
        "good3": row(9, 100, 1.6),
        "fair": row(11, 200, 2.0),
    }
    # Brand rows lift the 1-3 median from 9.5 to 12, so "fair" at 5.5% looks low.
    assert [r["query"] for r in op.low_ctr(rows, 5, 10)] == ["fair"]
    assert op.low_ctr(rows, 5, 10, brand_terms=("acme",)) == []
    assert op.branded(rows, ("ACME",)) == 3


def test_low_ctr_note_gives_band_counts_when_no_band_is_full():
    rows = {
        "a": row(1, 50, 2.0),
        "b": row(0, 50, 5.0),
        "c": row(0, 50, 6.4),
        "tiny": row(0, 2, 2.0),
        "acme": row(9, 50, 1.0),
        "far": row(0, 50, 30.0),
    }
    counts = op.band_counts(rows, min_impressions=5, brand_terms=("acme",))
    assert counts == {"1-3": 1, "4-7": 2, "8-10": 0}
    note = op.low_ctr_note(counts, min_impressions=5)
    assert "no position band has 3 queries" in note
    assert "1-3: 1, 4-7: 2, 8-10: 0" in note


def test_low_ctr_note_is_none_when_a_band_has_enough():
    assert op.low_ctr_note({"1-3": 3, "4-7": 0, "8-10": 0}, min_impressions=5) is None
