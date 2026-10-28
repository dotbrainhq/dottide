<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/dotbrainhq/dottide/main/.github/assets/cover-dark.png">
  <img src="https://raw.githubusercontent.com/dotbrainhq/dottide/main/.github/assets/cover-light.png" alt="dotTide: every site's numbers, one place. Search Console, GA4 and store stats across Google accounts, for you and your AI agents. Local and read-only. Next to the text, the dotTide icon: a wave running across a green tile, with one dot under the surface.">
</picture>

# dotTide

dotTide is a read-only MCP server and command-line tool that gives Claude, Cursor, Codex and other AI agents the numbers for every site you run. It reads Google Search Console and Google Analytics 4 (GA4) across multiple Google accounts, plus WordPress.org, Firefox Add-ons and GitHub stats, and writes a weekly snapshot for scripts and agents.

Nothing gets added to your sites. dotTide only reads numbers you already have, and your keys stay on your Mac.

## Why

If your sites sit under different Google accounts, checking them means logging in and out of each one. The weekly check slips to monthly, and any AI agent you ask works from stale numbers. Store numbers for plugins, extensions and repos live in yet more places.

dotTide reads all of it with one read-only key, and answers the same way in Claude, on the command line, and in a weekly JSON file.

## What it does

- **`sites`:** every configured site, which key covers it, and whether Search Console and GA4 access works when you ask.
- **`search_queries`:** clicks, impressions, CTR and average position by query or page, for any date range, with an optional comparison to the previous period.
- **`traffic`:** GA4 sessions by source and medium, with AI assistant referrals (ChatGPT, Perplexity, Copilot, Gemini, Claude and others) counted separately. Only for sites that have GA4.
- **`store_stats`:** live public numbers that need no key: WordPress.org plugins, Firefox Add-ons, GitHub stars.
- **`opportunities`:** what to work on next: queries in striking distance, pages and queries losing clicks, and page-one queries with a low click-through rate for their position.
- **`index_health`:** every sitemap's state, and whether the top pages are in Google's index, with a plain list of problems to fix.
- **`discover`:** finds every Search Console property and GA4 property the key can read, and writes the profile entries for you.
- **Ready-made prompts:** a weekly review, what to work on, and an index check, shown as commands in Claude and other MCP clients.
- **Weekly snapshot:** last full week against the week before, one JSON file per profile, for scripts and agents that read files.

## How access works

No site moves to a new Google account. You create one Google service account, and whichever Google account owns a site invites that service account's email:

- **Search Console:** as a Restricted user.
- **GA4:** as a Viewer.

The service account can only read, and you can remove it from any site in one click. Its key lives in the macOS keychain.

## Quick start

You need macOS and [uv](https://docs.astral.sh/uv/). There is nothing to clone: `uvx` downloads dotTide the first time you run it.

1. Write a starter profile, then add a plugin slug, an add-on slug or a GitHub user under `[stores]` in it:

```
uvx dottide init
```

2. Check that it runs. Store numbers need no Google setup at all:

```
uvx dottide store_stats
```

3. Set up Google access by following [Google setup](https://github.com/dotbrainhq/dottide/blob/main/docs/google-setup.md). It takes about ten minutes, plus a minute per site.

4. Store the key, let dotTide find your sites, and check access:

```
uvx dottide import-key dottide-main ~/Downloads/<downloaded-key>.json
uvx dottide discover --write
uvx dottide sites
```

5. Connect it to Claude Code:

```
claude mcp add --scope user dottide -- uvx dottide
```

To update later, run `uvx dottide@latest sites` once; after that `uvx dottide` uses the new version.

## Documentation

- [Google setup](https://github.com/dotbrainhq/dottide/blob/main/docs/google-setup.md): the service account, click by click, and sharing each site.
- [Configuration](https://github.com/dotbrainhq/dottide/blob/main/docs/configuration.md): profiles, every field, keys and environment variables.
- [Using dotTide](https://github.com/dotbrainhq/dottide/blob/main/docs/usage.md): each tool and its options, MCP clients, the weekly snapshot and its format, and fixes for common errors.
- [Asking an AI agent for your numbers](https://github.com/dotbrainhq/dottide/blob/main/docs/examples.md): example prompts for weekly checks, content to refresh, AI referrals and store numbers, plus a saved Claude Code command.
- [Connecting AI clients](https://github.com/dotbrainhq/dottide/blob/main/docs/clients.md): Claude Code, Claude Desktop, Cursor, Windsurf, VS Code, Codex, Gemini CLI, Grok, and agents without MCP.

## Good to know

- Search Console data settles about three days after the fact, so default ranges end three days ago.
- Every Google scope dotTide asks for is read-only, and no tool can change anything.
- GitHub allows 60 anonymous requests an hour per IP. Set `DOTTIDE_GITHUB_TOKEN` to a read-only token if you hit the limit.

## Contributing

See [CONTRIBUTING.md](https://github.com/dotbrainhq/dottide/blob/main/CONTRIBUTING.md). Security reports go through [SECURITY.md](https://github.com/dotbrainhq/dottide/blob/main/SECURITY.md).

## License

The code is released under the [MIT License](https://github.com/dotbrainhq/dottide/blob/main/LICENSE). The dotTide name and icon are not covered by the license, so please use your own name and icon if you ship a copy.
