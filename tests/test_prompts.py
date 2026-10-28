from dottide import prompts


def test_weekly_review_covers_every_site_or_one():
    assert "every site dotTide can read" in prompts.weekly_review()
    assert "the site a.test" in prompts.weekly_review("a.test")


def test_prompts_name_the_tools_they_need():
    assert "`opportunities`" in prompts.what_to_work_on("a.test")
    assert "`index_health`" in prompts.index_check("a.test")
    for text in (prompts.weekly_review(), prompts.what_to_work_on("a.test")):
        assert "Quote the numbers" in text


def test_weekly_review_includes_bing_only_where_set_up():
    text = prompts.weekly_review()
    assert "`bing_queries`" in text
    assert "Skip this step for sites without Bing" in text
