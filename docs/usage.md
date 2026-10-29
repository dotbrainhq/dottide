# Using dotTide

dotTide answers the same four questions three ways: as MCP tools for Claude and other AI clients, as commands that print JSON, and as a weekly snapshot file for scripts and agents. All three share the same code, so they always agree.

## Dates

Search Console data settles about three days after the fact. Every range that doesn't name its own dates ends three days ago.

- **`days`:** how many days the range covers. Default 28.
- **`start` and `end`:** exact dates as `YYYY-MM-DD`. They override `days`.
- **`compare`:** adds the previous period of the same length, right before the range, with the change for each number.

## Filters

`search_queries`, `page_queries`, `opportunities` and `competing_pages` take three optional filters. Every result repeats the filters it used under `filters`.

| Option | Values | Meaning |
|---|---|---|
| `country` | A three-letter ISO 3166-1 code, like `usa` or `bgd` | Only searches from that country. |
| `device` | `desktop`, `mobile` or `tablet` | Only searches from that kind of device. |
| `search_type` | `web` (default), `image`, `video`, `news`, `discover` or `googleNews` | Which Google surface the numbers come from. |

Discover and Google News report pages only: Search Console has no query rows and no position for them. Use `search_queries` with `by` set to `page` for those two.

```
uvx dottide search_queries example.com --device mobile --compare
uvx dottide search_queries example.com --by page --search-type discover
uvx dottide opportunities example.com --country usa
```

## The tools

### `sites`

Every configured site, which key covers it, and whether access works at the moment you ask.

```
uvx dottide sites
```

For each profile you get the service account email, every Search Console property that key can see, and one line per site:

- **`search_console`:** `ok`, `not shared with this key` (with any near matches it can see), or `no key access`.
- **`ga4`:** `ok`, `not used` for sites without a `ga4_property`, or the Google error.

Run it first whenever something looks wrong.

### `search_queries`

Search Console clicks, impressions, click-through rate (percent) and average position, by query or by page.

```
uvx dottide search_queries example.com
uvx dottide search_queries example.com --by page --days 7 --compare
uvx dottide search_queries example.com --start 2026-09-01 --end 2026-09-30 --limit 50
```

| Option | Default | Meaning |
|---|---|---|
| `by` | `query` | `query` or `page`. |
| `limit` | 25 | How many rows, biggest first. |

The result carries `totals` for the whole site and `rows`. With `compare`, each number gains `previous_<field>` and `change_<field>`. A row that didn't exist in the previous period shows `null` there.

### `page_queries`

The queries that bring people to one page, and the share of the page's traffic Google doesn't show.

```
uvx dottide page_queries example.com https://example.com/pricing/
uvx dottide page_queries example.com https://example.com/pricing/ --compare --device mobile
```

| Option | Default | Meaning |
|---|---|---|
| `page` | required | The page's full URL, exactly as `search_queries` by page lists it, trailing slash included. |
| `limit` | 25 | How many query rows to show, biggest first. |

The result has the page's own `totals`, its query `rows`, and `hidden`. Search Console leaves rare queries out of query rows to protect searchers' privacy, but still counts them in the page's totals. `hidden` is the difference: the clicks and impressions from queries Google doesn't show, and each one's share of the page's total. On a small site this is often most of the clicks. With `compare`, `previous_hidden` holds the same numbers for the previous period.

### `opportunities`

What to work on next for a site, worked out from Search Console.

```
uvx dottide opportunities example.com
uvx dottide opportunities example.com --days 90 --min-impressions 20 --limit 20
```

| Option | Default | Meaning |
|---|---|---|
| `min_impressions` | 5 | Skip queries seen fewer times than this. Raise it for big sites, lower it for small ones. |
| `limit` | 10 | How many items in each list. |

It returns six lists, each item with its own numbers:

- **`striking_distance`:** queries at average position 8 to 20, most impressions first. These sit at the bottom of page one or the top of page two, where a better page can move them into view.
- **`losing_pages`** and **`losing_queries`:** the biggest click drops against the previous period of the same length, including rows that disappeared.
- **`slipping_pages`** and **`slipping_queries`:** the biggest drops in average position against the previous period, for rows with at least `min_impressions` in both periods and a drop of one position or more. A page that slides from 14.7 to 22.8 loses only a couple of clicks, so it sits low in `losing_pages`; here it shows by how far it fell. Raise `min_impressions` to keep low-traffic rows out.
- **`low_ctr`:** page-one queries whose click-through rate is under half of the site's own median for that position band (1 to 3, 4 to 7, 8 to 10). A band needs at least three queries before it counts, so small sites may see none. Compare a low row's title and description with the query. When the site has `brand_terms` in its profile, queries containing them are left out of the medians and the list, and the result shows `brand_terms` and `brand_queries_left_out`.

When few queries reach `min_impressions`, the result carries a `note` saying so. When `low_ctr` is empty because no band has three queries, the result adds `low_ctr_note` and `low_ctr_band_counts` with each band's count, so an empty list doesn't read as every query doing fine.

### `competing_pages`

Queries where two or more of a site's pages get impressions, so they split the clicks and often both rank lower. This is sometimes called cannibalization.

```
uvx dottide competing_pages example.com
uvx dottide competing_pages example.com --days 90 --min-impressions 10
```

| Option | Default | Meaning |
|---|---|---|
| `min_impressions` | 5 | A page counts only when it has at least this many impressions for the query. |
| `limit` | 10 | How many queries to list. |

Each item has the query, its total impressions and clicks, every competing page with its own numbers, `top_page` (the page with the most clicks) and that page's share of the clicks. The biggest overlaps come first. When no query has two pages over `min_impressions`, the result carries a `note`.

### `index_health`

Whether a site is healthy in Google's index.

```
uvx dottide index_health example.com
uvx dottide index_health example.com --pages 25
```

| Option | Default | Meaning |
|---|---|---|
| `pages` | 10 | How many top pages by clicks to check, up to 50. |
| `days` | 28 | The range used to pick the top pages. |

It returns:

- **`sitemaps`:** every sitemap Search Console knows for the property, with errors, warnings, how many URLs it submits, and how many days since Google last read it.
- **`top_pages_checked`:** for each top page, Google's verdict, coverage state (like "Submitted and indexed" or "Crawled - currently not indexed"), robots.txt and fetch state, last crawl, and whether Google picked a different canonical than the page asks for.
- **`problems`:** everything worth fixing, in plain words: sitemap errors, sitemaps Google hasn't read in over 30 days, pages not indexed, and canonical mismatches.

Each page checked uses one call to Google's URL Inspection API, which allows 2,000 calls a day per property. dotTide only reads: it never submits a sitemap or asks Google to index a page.

### `core_web_vitals`

Core Web Vitals for one page, from Google's PageSpeed Insights.

```
uvx dottide core_web_vitals example.com
uvx dottide core_web_vitals example.com --page https://example.com/pricing/ --strategy desktop
```

| Option | Default | Meaning |
|---|---|---|
| `page` | the site's home page | The full URL to test. |
| `strategy` | `mobile` | `mobile` or `desktop`. Google ranks on mobile. |

It returns:

- **`page_field`** and **`site_field`:** real-user numbers from the Chrome UX Report for the page and for the whole site: the 75th percentile of LCP (milliseconds), INP (milliseconds) and CLS, each rated good, needs improvement or poor against Google's thresholds, and `passes` when all three are good. Small sites often have too few visits for these, and the result says so in a `note`.
- **`lab`:** one simulated Lighthouse load: performance score out of 100, LCP, CLS, Total Blocking Time, First Contentful Paint and Speed Index. Lab numbers move a little between runs.

One run takes 10 to 30 seconds. It needs the PageSpeed Insights API turned on in the key's Google Cloud project (see [Google setup](google-setup.md)).

### `bing_queries`

Bing Webmaster Tools clicks, impressions and average position by query, plus site totals.

```
uvx dottide bing_queries example.com
uvx dottide bing_queries example.com --days 90 --limit 50
```

Bing updates these numbers about once a week, so short ranges can come back empty, and a newly added site shows nothing for a few days. Setting it up takes one API key: see [Bing setup](bing-setup.md). Once it's set up, `sites` reports Bing access for each site too.

### `traffic`

GA4 sessions by source and medium, with AI assistant referrals counted on their own. Only for sites that have `ga4_property`.

```
uvx dottide traffic example.com --compare
```

The result has `sessions`, `ai_sessions`, `ai_referrals` (one entry per assistant with sessions, engaged sessions and `landing_pages`) and the top `sources`. `landing_pages` lists the pages that assistant's visits started on, most sessions first, up to 10 or `limit`, whichever is smaller. It shows which pages the assistants link to. A `(not set)` page means GA4 didn't record where the session started. AI assistants are matched by referring domain: ChatGPT, Perplexity, Copilot, Gemini, Claude, Mistral, DeepSeek, Grok, Meta AI, You.com and Phind. Visits an assistant opens without a referrer land in `(direct)`, so treat the AI count as a floor.

### `store_stats`

Live public numbers, no key needed.

```
uvx dottide store_stats
uvx dottide store_stats --profile business
```

- **WordPress.org:** version, active installs, rating, ratings count, support threads and how many are resolved, last update, and downloads for each of the last seven full days.
- **Firefox Add-ons:** version, average daily users, weekly downloads, rating and ratings count.
- **GitHub:** stars and forks for each public repo, and the total.

A store that fails returns an `error` field for that item; the rest still come back.

### `discover`

Finds every Search Console property and every GA4 web stream the key can read, matches them by domain, and suggests a `[[sites]]` block for each site that isn't in a profile yet.

```
uvx dottide discover
uvx dottide discover --write
uvx dottide discover --profile business --write
```

Without `--write` it prints the blocks so you can check them. With `--write` it adds them to the profile file, above `[stores]`. When you have more than one profile, name the one to write to with `--profile`. When a domain has both a domain property and a URL-prefix property, discover picks the domain property, because it covers every subdomain.

Finding GA4 properties needs the Google Analytics Admin API turned on in your Google Cloud project. Without it, discover still finds every Search Console property and prints a note with the link to turn the API on.

In MCP clients, `discover` only reads: it returns what it found and the blocks to add, and you add them with the command above.

## Ready-made prompts

MCP clients that support prompts show these as commands. In Claude Code they appear in the `/` menu.

| Prompt | Arguments | What the agent does |
|---|---|---|
| Weekly review | `site`, optional | Compares last week with the week before for every site (or one), lists the biggest movers, AI referrals, Bing numbers where set up, and store changes, and ends with the most useful thing to do this week. |
| What to work on | `site` | Calls `opportunities` and `competing_pages`, and turns the three items with the most to gain into concrete changes. |
| Index check | `site` | Calls `index_health` and explains each problem in a plain sentence. |

Every prompt asks the agent to quote the numbers it used.

## From an MCP client

Claude Code:

```
claude mcp add --scope user dottide -- uvx dottide
```

Claude Desktop, Cursor, VS Code, Codex, Gemini CLI and others: see [Connecting AI clients](clients.md) for each one's config.

Every tool is marked read-only. Good first questions:

- "Which of my sites lost the most clicks this week compared with last week?"
- "Top 10 pages on example.com by impressions in the last 28 days."
- "How many visits did ChatGPT send to example.com this month?"
- "Downloads for my WordPress.org plugins this week."

## The weekly snapshot

```
uvx dottide snapshot --out ~/growth
```

This writes one file per profile, named `<profile>-<year>-W<week>.json`, covering the last full week (ending three days ago) against the week before. Without `--out` it prints to the terminal.

Each file has:

| Field | What it holds |
|---|---|
| `schema` | The file format version, currently `1`. |
| `profile` | The profile name. |
| `generated_at` | When the file was written, in UTC. |
| `week` | The `start` and `end` dates. |
| `sites` | Per site: `queries` and `pages` (top 10 each, with comparison) and `traffic` where GA4 is used. |
| `stores` | The same shape as `store_stats`. |

If one site fails, for example because its access was removed, that site carries an `error` field and the rest of the snapshot still gets written. Nothing is ever filled in with a guess.

### Running it every week

On macOS, a LaunchAgent can run the snapshot every Monday morning. Save this as `~/Library/LaunchAgents/com.example.dottide-snapshot.plist`, changing the output folder, then load it with `launchctl load` followed by the file path.

```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.example.dottide-snapshot</string>
  <key>ProgramArguments</key>
  <array>
    <string>/opt/homebrew/bin/uvx</string>
    <string>dottide</string><string>snapshot</string>
    <string>--out</string><string>/path/to/growth</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>8</integer><key>Minute</key><integer>30</integer></dict>
</dict>
</plist>
```

## When something fails

| Message | What to do |
|---|---|
| `no stored key` | Run `dottide import-key` with the name in your profile's `[key]`. |
| `not shared with this key` | Add the service account email to that site in Search Console as a Restricted user, or copy the exact property name that `sites` lists. A new share can take a few minutes. |
| `Google API 403 ... has not been used in project` | Turn on that API in the Google Cloud project that owns the key. See [Google setup](google-setup.md). |
| `Google API 403 ... sufficient permissions` on GA4 | Add the service account as a Viewer on the property, and check the numeric property ID. |
| `PageSpeed Insights API has not been used in project` | Turn on the PageSpeed Insights API in the key's Google Cloud project. |
| `Bing API 400` or `401` | The Bing API key is wrong or was revoked. Generate a new one and run `import-secret` again. |
| `reports pages only` | Discover and Google News have no query rows. Use `search_queries` with `by` set to `page`. |
| `country takes a three-letter ISO 3166-1 code` | Use the three-letter code, like `usa`, not `us`. |
| `page takes the full URL` | Pass the whole address, like `https://example.com/pricing/`. |
| `unknown site` | The name isn't in any profile. The error lists the names that are. |
| `GitHub rate limit, resets ...` | Wait until the time shown, or set `DOTTIDE_GITHUB_TOKEN`. |
