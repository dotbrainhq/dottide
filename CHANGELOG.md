# Changelog

## Unreleased

- `index_health` checks every sitemap and the index status of a site's top pages, and lists the problems to fix.
- `opportunities` lists what to work on next: queries in striking distance, pages and queries losing clicks, and page-one queries with a low click-through rate for their position.

## 0.2.0

- Published on PyPI: `uvx dottide` runs it with nothing to clone.
- `init` writes a starter profile to `~/.config/dottide/`.
- `discover` finds every Search Console property and GA4 property the key can read and adds the missing sites to a profile.

## 0.1.0 (not published)

- First version: the `sites`, `search_queries`, `traffic` and `store_stats` MCP tools, the matching commands, and the weekly snapshot.
- Keys stored in the macOS keychain with `dottide import-key`.
- Docs for Google setup, configuration and everyday use.
- README cover in light and dark.
