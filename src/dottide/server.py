"""dotTide MCP server and command line.

dottide                      run the MCP server on stdio (what MCP clients call)
dottide sites                print any report as JSON; also search_queries, traffic, store_stats
dottide init                 write a starter profile to ~/.config/dottide/main.toml
dottide discover [--write]   suggest profile entries for sites the key can read
dottide opportunities SITE   queries and pages worth working on
dottide page_queries SITE URL one page's queries and the share Google hides
dottide competing_pages SITE queries where two or more pages compete
dottide index_health SITE    sitemap state and index status of the top pages
dottide core_web_vitals SITE Core Web Vitals from PageSpeed Insights
dottide bing_queries SITE    Bing Webmaster Tools clicks and impressions by query
dottide snapshot [--out DIR] write the weekly snapshot, one file per profile
dottide import-key NAME FILE copy a service account key into the system secret store
dottide import-secret NAME   store an API key (like Bing's) from a hidden prompt
"""

from __future__ import annotations

import argparse
import getpass
import json
import logging
import sys

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from dottide import bing, indexhealth, keys, prompts, report, snapshot, vitals
from dottide import discover as finder
from dottide import opportunities as chances
from dottide.config import init_profile
from dottide.google import SEARCH_TYPES

READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=True)

server = MCPServer(
    name="dottide",
    instructions=(
        "Read-only numbers for every configured site and product. Call `sites` first to see "
        "which sites exist and whether their access works. Search Console data lags about "
        "three days, so default ranges end three days ago."
    ),
)


@server.tool(annotations=READ_ONLY)
def sites() -> dict:
    """Every configured site, which key covers it, and whether Search Console and GA4 access
    works at the moment of the call."""
    return report.sites()


@server.tool(annotations=READ_ONLY)
def search_queries(
    site: str,
    by: str = "query",
    start: str | None = None,
    end: str | None = None,
    days: int = 28,
    compare: bool = False,
    limit: int = 25,
    country: str | None = None,
    device: str | None = None,
    search_type: str = "web",
) -> dict:
    """Search Console clicks, impressions, CTR (percent) and average position, by "query" or
    "page". Dates are YYYY-MM-DD; without them the range is the last `days` days ending three
    days ago. compare=true adds the previous period of the same length and the change.
    Optional filters: country (three-letter ISO code like "usa"), device ("desktop", "mobile"
    or "tablet") and search_type ("web", "image", "video", "news", "discover" or
    "googleNews"; default "web"). Discover and Google News have page rows only. The result
    echoes the filters it used."""
    return report.search_queries(
        site, by, start, end, days, compare, limit, country, device, search_type
    )


@server.tool(annotations=READ_ONLY)
def page_queries(
    site: str,
    page: str,
    start: str | None = None,
    end: str | None = None,
    days: int = 28,
    compare: bool = False,
    limit: int = 25,
    country: str | None = None,
    device: str | None = None,
    search_type: str = "web",
) -> dict:
    """The queries that bring people to one page (full URL), with the page's own totals and
    `hidden`: the clicks and impressions Search Console counts for the page but leaves out of
    its query rows, because Google anonymizes rare queries. Same dates, compare and filters as
    search_queries."""
    return report.page_queries(
        site, page, start, end, days, compare, limit, country, device, search_type
    )


@server.tool(annotations=READ_ONLY)
def traffic(
    site: str,
    start: str | None = None,
    end: str | None = None,
    days: int = 28,
    compare: bool = False,
    limit: int = 25,
) -> dict:
    """GA4 sessions by source and medium, plus AI assistant referrals (ChatGPT, Perplexity,
    Copilot, Gemini, Claude and others) totalled separately. Only for sites with GA4."""
    return report.traffic(site, start, end, days, compare, limit)


@server.tool(annotations=READ_ONLY)
def store_stats(profile: str | None = None) -> dict:
    """Live public store numbers that need no keys: WordPress.org plugins (installs, rating,
    downloads last 7 days), Firefox Add-ons (daily users, ratings), GitHub stars."""
    return report.store_stats(profile)


@server.tool(annotations=READ_ONLY)
def opportunities(
    site: str,
    start: str | None = None,
    end: str | None = None,
    days: int = 28,
    min_impressions: int = 5,
    limit: int = 10,
    country: str | None = None,
    device: str | None = None,
    search_type: str = "web",
) -> dict:
    """What to work on next for a site, from Search Console: queries in striking distance
    (position 8 to 20, by impressions), pages and queries that lost the most clicks against the
    previous period, and page-one queries whose CTR is under half the site's own median for
    that position. When low_ctr is empty because no position band has three queries,
    low_ctr_note says so and low_ctr_band_counts gives each band's count. Every item carries
    its numbers. Same date rules and filters as search_queries, except Discover and Google
    News, which have no query rows."""
    return chances.opportunities(
        site, start, end, days, min_impressions, limit, country, device, search_type
    )


@server.tool(annotations=READ_ONLY)
def competing_pages(
    site: str,
    start: str | None = None,
    end: str | None = None,
    days: int = 28,
    min_impressions: int = 5,
    limit: int = 10,
    country: str | None = None,
    device: str | None = None,
    search_type: str = "web",
) -> dict:
    """Queries where two or more pages of the site each get at least `min_impressions`, so they
    split the clicks (cannibalization). For each query: every page with its clicks, impressions
    and position, the page with most clicks and its share. Biggest overlaps first. Same dates
    and filters as search_queries."""
    return chances.competing_pages(
        site, start, end, days, min_impressions, limit, country, device, search_type
    )


@server.tool(annotations=READ_ONLY)
def index_health(site: str, pages: int = 10, days: int = 28) -> dict:
    """Is the site healthy in Google's index? Every sitemap Search Console knows (errors,
    warnings, when Google last read it, URLs submitted) and the index status of the top `pages`
    pages by clicks over the last `days` days (verdict, coverage, last crawl, Google's chosen
    canonical). `problems` lists anything to fix in plain words. Reads only: it never submits a
    sitemap or requests indexing. Each page checked uses one URL Inspection call."""
    return indexhealth.index_health(site, pages, days)


@server.tool(annotations=READ_ONLY)
def core_web_vitals(site: str, page: str | None = None, strategy: str = "mobile") -> dict:
    """Core Web Vitals for a page (default: the site's home page) from PageSpeed Insights.
    page_field and site_field hold real-user 75th-percentile LCP, INP and CLS with Google's
    good / needs improvement / poor rating, when Google has enough visits; lab holds one
    Lighthouse run (performance score, LCP, CLS, TBT, FCP, Speed Index). strategy is "mobile"
    or "desktop". One run takes 10 to 30 seconds."""
    return vitals.core_web_vitals(site, page, strategy)


@server.tool(annotations=READ_ONLY)
def bing_queries(
    site: str,
    start: str | None = None,
    end: str | None = None,
    days: int = 28,
    limit: int = 25,
) -> dict:
    """Bing Webmaster Tools clicks, impressions and average position by query, plus site
    totals, for a range. Bing feeds Copilot. Needs a [bing] key in the site's profile. Bing
    updates these numbers about once a week."""
    return bing.bing_queries(site, start, end, days, limit)


@server.tool(annotations=READ_ONLY)
def discover(profile: str | None = None) -> dict:
    """Every Search Console property and GA4 web stream the key can read, matched by domain,
    with ready-to-paste [[sites]] blocks for any site not in a profile yet. Reads only; the
    user adds the blocks with `dottide discover --write`."""
    return finder.discover(profile)


@server.prompt(title="Weekly review")
def weekly_review(site: str = "") -> str:
    """Week-over-week review of every site, or one site: clicks, top movers, AI referrals, Bing
    where it's set up, and store changes, ending with the most useful thing to do this week."""
    return prompts.weekly_review(site)


@server.prompt(title="What to work on")
def what_to_work_on(site: str) -> str:
    """The three changes with the most to gain on a site, from its opportunities."""
    return prompts.what_to_work_on(site)


@server.prompt(title="Index check")
def index_check(site: str) -> str:
    """Anything keeping a site's pages out of Google, in plain words."""
    return prompts.index_check(site)


def main() -> None:
    # httpx logs every request URL at INFO; keep stderr for real problems.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    if len(sys.argv) == 1:
        server.run("stdio")
        return
    parser = argparse.ArgumentParser(prog="dottide")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("sites")
    q = sub.add_parser("search_queries")
    q.add_argument("site")
    q.add_argument("--by", default="query", choices=["query", "page"])
    pq = sub.add_parser("page_queries")
    pq.add_argument("site")
    pq.add_argument("page", help="the page's full URL")
    t = sub.add_parser("traffic")
    t.add_argument("site")
    for p in (q, pq, t):
        p.add_argument("--start")
        p.add_argument("--end")
        p.add_argument("--days", type=int, default=28)
        p.add_argument("--compare", action="store_true")
        p.add_argument("--limit", type=int, default=25)
    s = sub.add_parser("store_stats")
    s.add_argument("--profile")
    o = sub.add_parser("opportunities")
    o.add_argument("site")
    o.add_argument("--start")
    o.add_argument("--end")
    o.add_argument("--days", type=int, default=28)
    o.add_argument("--min-impressions", type=int, default=5)
    o.add_argument("--limit", type=int, default=10)
    c = sub.add_parser("competing_pages")
    c.add_argument("site")
    c.add_argument("--start")
    c.add_argument("--end")
    c.add_argument("--days", type=int, default=28)
    c.add_argument("--min-impressions", type=int, default=5)
    c.add_argument("--limit", type=int, default=10)
    for p in (q, pq, o, c):
        p.add_argument("--country", help="three-letter ISO code, like usa")
        p.add_argument("--device", choices=["desktop", "mobile", "tablet"])
        p.add_argument("--search-type", default="web", choices=list(SEARCH_TYPES))
    h = sub.add_parser("index_health")
    h.add_argument("site")
    h.add_argument("--pages", type=int, default=10)
    h.add_argument("--days", type=int, default=28)
    v = sub.add_parser("core_web_vitals")
    v.add_argument("site")
    v.add_argument("--page", help="full URL to test; default is the site's home page")
    v.add_argument("--strategy", default="mobile", choices=["mobile", "desktop"])
    b = sub.add_parser("bing_queries")
    b.add_argument("site")
    b.add_argument("--start")
    b.add_argument("--end")
    b.add_argument("--days", type=int, default=28)
    b.add_argument("--limit", type=int, default=25)
    i = sub.add_parser("init")
    i.add_argument("--profile", default="main", help="profile name, which is also the file name")
    d = sub.add_parser("discover")
    d.add_argument("--profile", help="only use this profile's key, and write to it")
    d.add_argument("--write", action="store_true", help="append the new sites to the profile")
    snap = sub.add_parser("snapshot")
    snap.add_argument("--out", help="folder for <profile>-<year>-W<week>.json; stdout if absent")
    sec = sub.add_parser("import-secret")
    sec.add_argument("name", help="name for the stored secret, for example dottide-bing")
    k = sub.add_parser("import-key")
    k.add_argument("name", help="name for the stored key, for example dottide-main")
    k.add_argument("file", help="path to the downloaded service account JSON key")
    args = parser.parse_args()
    try:
        _run(args)
    except (OSError, ValueError, RuntimeError) as exc:
        # Expected problems (missing key, unknown site, existing file) get one clear line.
        sys.exit(f"dottide: {exc}")


def _filters(args: argparse.Namespace) -> tuple:
    return args.country, args.device, args.search_type


def _run(args: argparse.Namespace) -> None:
    if args.command == "import-key":
        print(f"stored {keys.store(args.name, args.file)} in the secret store as {args.name}")
        return
    if args.command == "import-secret":
        keys.store_secret(args.name, getpass.getpass(f"Paste the secret for {args.name}: "))
        print(f"stored {args.name} in the secret store")
        return
    if args.command == "init":
        path = init_profile(args.profile)
        print(f"wrote {path}")
        print("next: dottide import-key dottide-main <key.json>, then dottide discover --write")
        return
    if args.command == "discover":
        found = finder.discover(args.profile)
        if args.write and found["new_sites"]:
            path = finder.write(args.profile, found["toml"])
            print(f"added {len(found['new_sites'])} sites to {path}")
        elif found["new_sites"]:
            print(found["toml"])
            print(
                f"\n# {len(found['new_sites'])} new sites. Add them with --write.", file=sys.stderr
            )
        else:
            print("Every site the key can read is already in a profile.")
        for error in found.get("errors", []):
            print(f"note: {error}", file=sys.stderr)
        return
    if args.command == "snapshot":
        snapshot.run(args.out)
        return
    if args.command == "sites":
        result = report.sites()
    elif args.command == "search_queries":
        result = report.search_queries(
            args.site,
            args.by,
            args.start,
            args.end,
            args.days,
            args.compare,
            args.limit,
            *_filters(args),
        )
    elif args.command == "page_queries":
        result = report.page_queries(
            args.site,
            args.page,
            args.start,
            args.end,
            args.days,
            args.compare,
            args.limit,
            *_filters(args),
        )
    elif args.command == "opportunities":
        result = chances.opportunities(
            args.site,
            args.start,
            args.end,
            args.days,
            args.min_impressions,
            args.limit,
            *_filters(args),
        )
    elif args.command == "competing_pages":
        result = chances.competing_pages(
            args.site,
            args.start,
            args.end,
            args.days,
            args.min_impressions,
            args.limit,
            *_filters(args),
        )
    elif args.command == "index_health":
        result = indexhealth.index_health(args.site, args.pages, args.days)
    elif args.command == "core_web_vitals":
        result = vitals.core_web_vitals(args.site, args.page, args.strategy)
    elif args.command == "bing_queries":
        result = bing.bing_queries(args.site, args.start, args.end, args.days, args.limit)
    elif args.command == "traffic":
        result = report.traffic(
            args.site, args.start, args.end, args.days, args.compare, args.limit
        )
    else:
        result = report.store_stats(args.profile)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
