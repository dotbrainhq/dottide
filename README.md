<p align="center"><img src="brand/png/sizes/dottide-icon-128.png" width="96" height="96" alt="dotTide icon: a wave running across a green tile, with one dot under the surface."></p>

# dotTide

Read-only numbers for every site and product you run, in one place, for you and your AI agents. Search Console and GA4 across different Google accounts, plus public store numbers, behind four MCP tools and a weekly snapshot.

Nothing gets added to your sites. dotTide only reads numbers you already have, and your keys stay on your Mac.

## Why

If your sites sit under different Google accounts, checking them means logging in and out of each one. The weekly check slips to monthly, and any AI agent you ask works from stale numbers. Store numbers for plugins, extensions and repos live in yet more places.

dotTide reads all of it with one read-only key, and answers the same way in Claude, on the command line, and in a weekly JSON file.

## What it does

- **`sites`:** every configured site, which key covers it, and whether Search Console and GA4 access works when you ask.
- **`search_queries`:** clicks, impressions, CTR and average position by query or page, for any date range, with an optional comparison to the previous period.
- **`traffic`:** GA4 sessions by source and medium, with AI assistant referrals (ChatGPT, Perplexity, Copilot, Gemini, Claude and others) counted separately. Only for sites that have GA4.
- **`store_stats`:** live public numbers that need no key: WordPress.org plugins, Firefox Add-ons, GitHub stars.
- **Weekly snapshot:** last full week against the week before, one JSON file per profile, for scripts and agents that read files.

## How access works

No site moves to a new Google account. You create one Google service account, and whichever Google account owns a site invites that service account's email:

- **Search Console:** as a Restricted user.
- **GA4:** as a Viewer.

The service account can only read, and you can remove it from any site in one click. Its key lives in the macOS keychain.

## Quick start

You need macOS, [uv](https://docs.astral.sh/uv/) and Python 3.12 or newer.

1. Get the code.

```
git clone https://github.com/dotbrainhq/dottide.git
cd dottide
uv sync
```

2. Check that it runs. Store numbers need no Google setup at all:

```
mkdir -p ~/.config/dottide
cp config.example.toml ~/.config/dottide/main.toml
```

Add a plugin slug, an add-on slug or a GitHub user under `[stores]` in that file, then:

```
uv run dottide store_stats
```

3. Set up Google access by following [Google setup](docs/google-setup.md). It takes about ten minutes, plus a minute per site.

4. Store the key, add your sites to the profile, and check access:

```
uv run dottide import-key dottide-main ~/Downloads/<downloaded-key>.json
uv run dottide sites
```

5. Connect it to Claude Code:

```
claude mcp add --scope user dottide -- uv run --quiet --project "$PWD" dottide
```

## Documentation

- [Google setup](docs/google-setup.md): the service account, click by click, and sharing each site.
- [Configuration](docs/configuration.md): profiles, every field, keys and environment variables.
- [Using dotTide](docs/usage.md): each tool and its options, MCP clients, the weekly snapshot and its format, and fixes for common errors.

## Good to know

- Search Console data settles about three days after the fact, so default ranges end three days ago.
- Every Google scope dotTide asks for is read-only, and no tool can change anything.
- GitHub allows 60 anonymous requests an hour per IP. Set `DOTTIDE_GITHUB_TOKEN` to a read-only token if you hit the limit.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security reports go through [SECURITY.md](SECURITY.md).

## License

The code is released under the [MIT License](LICENSE). The dotTide name and icon are not covered by the license, so please use your own name and icon if you ship a copy.
