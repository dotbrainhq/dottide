"""dotTide MCP server and command line.

dottide                      run the MCP server on stdio (what MCP clients call)
dottide sites                print any report as JSON; also search_queries, traffic, store_stats
dottide snapshot [--out DIR] write the weekly snapshot, one file per profile
dottide import-key NAME FILE copy a service account key into the macOS keychain
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from dottide import keys, report, snapshot

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
) -> dict:
    """Search Console clicks, impressions, CTR (percent) and average position, by "query" or
    "page". Dates are YYYY-MM-DD; without them the range is the last `days` days ending three
    days ago. compare=true adds the previous period of the same length and the change."""
    return report.search_queries(site, by, start, end, days, compare, limit)


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
    t = sub.add_parser("traffic")
    t.add_argument("site")
    for p in (q, t):
        p.add_argument("--start")
        p.add_argument("--end")
        p.add_argument("--days", type=int, default=28)
        p.add_argument("--compare", action="store_true")
        p.add_argument("--limit", type=int, default=25)
    s = sub.add_parser("store_stats")
    s.add_argument("--profile")
    snap = sub.add_parser("snapshot")
    snap.add_argument("--out", help="folder for <profile>-<year>-W<week>.json; stdout if absent")
    k = sub.add_parser("import-key")
    k.add_argument("name", help="keychain item name, for example dottide-main")
    k.add_argument("file", help="path to the downloaded service account JSON key")
    args = parser.parse_args()

    if args.command == "import-key":
        print(f"stored {keys.store(args.name, args.file)} in keychain item {args.name}")
        return
    if args.command == "snapshot":
        snapshot.run(args.out)
        return
    if args.command == "sites":
        result = report.sites()
    elif args.command == "search_queries":
        result = report.search_queries(
            args.site, args.by, args.start, args.end, args.days, args.compare, args.limit
        )
    elif args.command == "traffic":
        result = report.traffic(
            args.site, args.start, args.end, args.days, args.compare, args.limit
        )
    else:
        result = report.store_stats(args.profile)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
