# Changelog

## 0.4.1

- `opportunities` adds `slipping_pages` and `slipping_queries`: pages and queries whose average position dropped the most against the previous period, for rows with enough impressions in both. A page that slides from page two to page three now shows even when it lost only a couple of clicks.
- When `low_ctr` comes back empty because no position band has three queries, `low_ctr_note` says so and `low_ctr_band_counts` gives each band's count.
- A site can list `brand_terms` in its profile, and queries containing them stay out of the `low_ctr` check. `discover` suggests a commented-out `brand_terms` line from each new site's domain.
- `traffic` lists the landing pages each AI assistant sent visits to, under `landing_pages` in `ai_referrals`.
- Gemini visits tagged with the bare source `gemini` now count in `ai_referrals`, and any source GA4 gives the `ai-assistant` medium counts as AI traffic.

## 0.4.0

- `page_queries` shows the queries behind one page, with the page's own totals and the clicks and impressions Google hides behind anonymized queries.
- `competing_pages` lists queries where two or more pages split the impressions, with every page's numbers and the page that wins most clicks. The What to work on prompt checks it.
- `search_queries`, `opportunities` and the two new tools take `country`, `device` and `search_type` filters, and every result repeats the filters it used. Discover and Google News give a plain error when asked for query rows, since Search Console has none for them.

## 0.3.1

- Bing setup has its own guide, linked from the README, and the Weekly review prompt includes Bing numbers where Bing is set up.
- Listing files for the official MCP registry and Glama.

## 0.3.0

- `opportunities` lists what to work on next: queries in striking distance, pages and queries losing clicks, and page-one queries with a low click-through rate for their position.
- `index_health` checks every sitemap and the index status of a site's top pages, and lists the problems to fix.
- `core_web_vitals` reports real-user LCP, INP and CLS with Google's ratings, plus a lab run, from PageSpeed Insights, on the same service account.
- `bing_queries` reads Bing Webmaster Tools clicks, impressions and position by query, and `import-secret` stores its API key from a hidden prompt.
- Ready-made MCP prompts: Weekly review, What to work on, and Index check.
- Keys work on Windows (Credential Manager) and Linux (Secret Service) as well as macOS, and dotTide warns when a key file can be read by other users.
- Tests run every Google and store reader against saved sample responses, with made-up data and no network calls.

## 0.2.0

- Published on PyPI: `uvx dottide` runs it with nothing to clone.
- `init` writes a starter profile to `~/.config/dottide/`.
- `discover` finds every Search Console property and GA4 property the key can read and adds the missing sites to a profile.

## 0.1.0 (not published)

- First version: the `sites`, `search_queries`, `traffic` and `store_stats` MCP tools, the matching commands, and the weekly snapshot.
- Keys stored in the macOS keychain with `dottide import-key`.
- Docs for Google setup, configuration and everyday use.
- README cover in light and dark.
