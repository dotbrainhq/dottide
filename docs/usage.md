# Using dotTide

dotTide answers the same four questions three ways: as MCP tools for Claude and other AI clients, as commands that print JSON, and as a weekly snapshot file for scripts and agents. All three share the same code, so they always agree.

## Dates

Search Console data settles about three days after the fact. Every range that doesn't name its own dates ends three days ago.

- **`days`:** how many days the range covers. Default 28.
- **`start` and `end`:** exact dates as `YYYY-MM-DD`. They override `days`.
- **`compare`:** adds the previous period of the same length, right before the range, with the change for each number.

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

### `traffic`

GA4 sessions by source and medium, with AI assistant referrals counted on their own. Only for sites that have `ga4_property`.

```
uvx dottide traffic example.com --compare
```

The result has `sessions`, `ai_sessions`, `ai_referrals` (one entry per assistant with sessions and engaged sessions) and the top `sources`. AI assistants are matched by referring domain: ChatGPT, Perplexity, Copilot, Gemini, Claude, Mistral, DeepSeek, Grok, Meta AI, You.com and Phind. Visits an assistant opens without a referrer land in `(direct)`, so treat the AI count as a floor.

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
| `no keychain item` | Run `dottide import-key` with the name in your profile's `[key]`. |
| `not shared with this key` | Add the service account email to that site in Search Console as a Restricted user, or copy the exact property name that `sites` lists. A new share can take a few minutes. |
| `Google API 403 ... has not been used in project` | Turn on that API in the Google Cloud project that owns the key. See [Google setup](google-setup.md). |
| `Google API 403 ... sufficient permissions` on GA4 | Add the service account as a Viewer on the property, and check the numeric property ID. |
| `unknown site` | The name isn't in any profile. The error lists the names that are. |
| `GitHub rate limit, resets ...` | Wait until the time shown, or set `DOTTIDE_GITHUB_TOKEN`. |
