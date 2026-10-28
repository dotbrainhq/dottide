# Configuration

dotTide reads profiles: small TOML files that say which Google key to use, which sites to read, and which store pages to count. Nothing in a profile is secret. The key itself lives in the macOS keychain or in a file outside any repo.

## Where profiles live

By default dotTide loads every `.toml` file in `~/.config/dottide/`. The file name is the profile name, so `~/.config/dottide/business.toml` is the `business` profile. Files whose names start with `_` are skipped, which is handy for parking a profile without deleting it.

Set `DOTTIDE_CONFIG` to load something else:

```
DOTTIDE_CONFIG=~/.config/dottide/business.toml uvx dottide sites
DOTTIDE_CONFIG=/path/to/folder uvx dottide sites
```

Point an agent at a single file when it should only see one profile.

## One profile or several

Profiles decide two things: which key reads a site, and which weekly snapshot file a site lands in. Common setups:

- **One profile:** one key, every site, one weekly file.
- **Several profiles, one key:** every profile names the same stored key. The sites split into separate weekly files, for example one per brand.
- **Several profiles, several keys:** each profile has its own service account, so no single key can read everything.

## The file, field by field

`uvx dottide init` writes a starter profile to `~/.config/dottide/main.toml`; add `--profile business` for another name. It never overwrites a file. The starter looks like this once filled in:

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
| `keychain` | The name of a key stored with `dottide import-key`, in the macOS keychain, Windows Credential Manager or the Linux Secret Service. Recommended. |
| `file` | A path to the service account JSON key. Use this on machines without a secret store, like a headless Linux server. Keep the file outside any repo and readable only by you (`chmod 600`). |

A profile with only `[stores]` needs no `[key]` at all.

### `[[sites]]`

One block per site.

| Field | Required | What it holds |
|---|---|---|
| `name` | Yes | The name you use in tool calls, usually the domain. Must be unique across all profiles. |
| `search_console` | No | The Search Console property, written exactly as Search Console shows it. A domain property looks like `sc-domain:example.com`. A URL-prefix property is the full URL with the trailing slash, like `https://example.com/`. |
| `bing` | No | The site's URL in Bing Webmaster Tools, like `https://example.com/`. Only needed when it differs from the Search Console property. |
| `ga4_property` | No | The numeric GA4 property ID from Admin, then Property details. It's a number like `123456789`, not the `G-` measurement ID. Leave it out for sites without GA4. |

You rarely need to type these by hand: `uvx dottide discover --write` finds every site the key can read and adds the blocks for you. To check a property name yourself, `uvx dottide sites` lists every property the key can see.

### `[bing]`

Optional. Add it to read Bing Webmaster Tools numbers for the profile's sites:

```
[bing]
keychain = "dottide-bing"
```

The value is the name of a Bing API key stored with `dottide import-secret dottide-bing`. See [Using dotTide](usage.md#bing_queries) for getting the key.

### `[stores]`

Public numbers that need no key.

| Field | What it holds |
|---|---|
| `wordpress_org` | Plugin slugs from WordPress.org, the part after `/plugins/` in the plugin's URL. |
| `firefox` | Firefox Add-ons slugs, the part after `/addon/` in the add-on's URL. |
| `github_owners` | GitHub users or organizations. Only their public repos that aren't forks are counted. |

When several profiles list the same slug, `store_stats` counts it once.

## Keys

Store a downloaded key in your system's secret store, then delete the file:

```
uvx dottide import-key dottide-main ~/Downloads/key.json
```

The command checks that the file is a Google service account key, stores it, and reads it back to confirm. On macOS the key is passed to the keychain on standard input, so it never shows up in the process list. On Windows and Linux it goes through the `keyring` library, split into small chunks because Windows limits the size of one credential. Linux needs a running Secret Service, such as GNOME Keyring or KWallet; without one, use `file` and keep the file at mode 600. dotTide warns when a key file can be read by other users.

To replace a key, create a new one in the Google Cloud console, run `import-key` again with the same name, then delete the old key in the console.

## Environment variables

| Variable | What it does |
|---|---|
| `DOTTIDE_CONFIG` | One profile file or a folder of them. Default `~/.config/dottide/`. |
| `DOTTIDE_GITHUB_TOKEN` | Optional read-only GitHub token. GitHub allows 60 anonymous requests an hour per IP; a token raises that. |
