"""Ready-made prompts that MCP clients show as commands. Each one tells the agent which
dotTide tools to call and how to report, so the answer quotes real numbers."""

from __future__ import annotations

QUOTE = "Quote the numbers you used, and call a change of a few clicks noise, not a trend."


def weekly_review(site: str = "") -> str:
    scope = f"the site {site}" if site else "every site dotTide can read"
    return f"""Use dotTide for a weekly review of {scope}.

1. Call `sites` first. If a site has no access, say so and skip it.
2. For each site, call `search_queries` with days=7 and compare=true, by query and by page.
   List the three queries or pages with the biggest change in clicks, with both weeks' numbers.
3. For each site with GA4, call `traffic` with days=7 and compare=true, and report sessions
   and AI assistant referrals for both weeks.
4. For each site where `sites` shows Bing as ok, call `bing_queries` with days=28 and report
   Bing clicks and the top three Bing queries. Skip this step for sites without Bing.
5. Call `store_stats` and report only what changed: downloads, users, ratings, open support threads.
6. End with the single most useful thing to do this week, and why.

Keep it to five lines per site. {QUOTE}"""


def what_to_work_on(site: str) -> str:
    return f"""Use dotTide to decide what to work on next for {site}.

1. Call `opportunities` for {site}.
2. Pick the three items with the most to gain: striking-distance queries with the most
   impressions, the biggest click drops, or page-one queries with a low click-through rate.
3. For each, name the page, the query, the numbers, and one concrete change to make: a better
   title and description, a section that answers the query, or a refresh of an old page.

{QUOTE}"""


def index_check(site: str) -> str:
    return f"""Use dotTide to check whether anything is keeping {site} out of Google.

1. Call `index_health` for {site}.
2. Explain each item in `problems` in one plain sentence, with what to do about it.
3. If there are no problems, say so in one line and stop.

Don't suggest submitting sitemaps or requesting indexing through dotTide: it only reads."""
