# Configuration

dotTide reads profiles: small TOML files that say which Google key to use, which sites to read, and which store pages to count. Nothing in a profile is secret. The key itself lives in the macOS keychain or in a file outside any repo.

## Where profiles live

By default dotTide loads every `.toml` file in `~/.config/dottide/`. The file name is the profile name, so `~/.config/dottide/business.toml` is the `business` profile. Files whose names start with `_` are skipped, which is handy for parking a profile without deleting it.

Set `DOTTIDE_CONFIG` to load something else:

```
DOTTIDE_CONFIG=~/.config/dottide/business.toml uv run dottide sites
DOTTIDE_CONFIG=/path/to/folder uv run dottide sites
```

Point an agent at a single file when it should only see one profile.

## One profile or several

Profiles decide two things: which key reads a site, and which weekly snapshot file a site lands in. Common setups:

- **One profile:** one key, every site, one weekly file.
- **Several profiles, one key:** every profile names the same keychain item. The sites split into separate weekly files, for example one per brand.
- **Several profiles, several keys:** each profile has its own service account, so no single key can read everything.

## The file, field by field

Copy [`config.example.toml`](../config.example.toml) and fill it in.

```
[key]
keychain = "dottide-main"

[[sites]]
name = "example.com"
search_console = "sc-domain:example.com"
ga4_property = "123456789"

[[sites]]
name = "blog.example.org"
search_console = "https://blog.example.org/"

[stores]
wordpress_org = ["my-plugin-slug"]
firefox = ["my-addon-slug"]
github_owners = ["my-org"]
```

### `[key]`

Set exactly one of these:

| Field | What it holds |
|---|---|
| `keychain` | The name of a macOS keychain item made with `dottide import-key`. Recommended. |
| `file` | A path to the service account JSON key. Use this on machines without a keychain. Keep the file outside any repo and readable only by you (`chmod 600`). |

A profile with only `[stores]` needs no `[key]` at all.

### `[[sites]]`

One block per site.

| Field | Required | What it holds |
|---|---|---|
| `name` | Yes | The name you use in tool calls, usually the domain. Must be unique across all profiles. |
| `search_console` | No | The Search Console property, written exactly as Search Console shows it. A domain property looks like `sc-domain:example.com`. A URL-prefix property is the full URL with the trailing slash, like `https://example.com/`. |
| `ga4_property` | No | The numeric GA4 property ID from Admin, then Property details. It's a number like `123456789`, not the `G-` measurement ID. Leave it out for sites without GA4. |

Not sure which Search Console property you have? Run `uv run dottide sites`. It lists every property the key can see, so you can copy the exact one.

### `[stores]`

Public numbers that need no key.

| Field | What it holds |
|---|---|
| `wordpress_org` | Plugin slugs from WordPress.org, the part after `/plugins/` in the plugin's URL. |
| `firefox` | Firefox Add-ons slugs, the part after `/addon/` in the add-on's URL. |
| `github_owners` | GitHub users or organizations. Only their public repos that aren't forks are counted. |

When several profiles list the same slug, `store_stats` counts it once.

## Keys

Store a downloaded key in the keychain, then delete the file:

```
uv run dottide import-key dottide-main ~/Downloads/key.json
```

The command checks that the file is a Google service account key, stores it, and reads it back to confirm. The key is passed to the keychain on standard input, so it never shows up in the process list.

To replace a key, create a new one in the Google Cloud console, run `import-key` again with the same name, then delete the old key in the console.

## Environment variables

| Variable | What it does |
|---|---|
| `DOTTIDE_CONFIG` | One profile file or a folder of them. Default `~/.config/dottide/`. |
| `DOTTIDE_GITHUB_TOKEN` | Optional read-only GitHub token. GitHub allows 60 anonymous requests an hour per IP; a token raises that. |
