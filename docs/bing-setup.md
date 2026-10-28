# Bing setup

Optional. Bing powers Copilot's web answers, so its search numbers are worth a look next to Google's. dotTide reads them from Bing Webmaster Tools with one API key that covers every site in your Bing account. It takes about five minutes.

## 1. Add your sites to Bing Webmaster Tools

1. Open [Bing Webmaster Tools](https://www.bing.com/webmasters) and sign in. A Microsoft, Google or Facebook account works. Use the account you want to own your Bing data.
2. Choose **Import from Google Search Console**, sign in with the Google account that owns your sites, and pick the sites to import. Bing verifies them for you, so there's nothing to add to your sites.

If a site isn't in Search Console, add it by hand with **Add your site** and follow Bing's verification steps.

## 2. Create an API key

1. In Bing Webmaster Tools, open **Settings**, then **API access**.
2. Choose **API Key** and generate one. The key covers every site in this Bing account.
3. Keep it on screen. Don't paste it into a chat, an issue or a file.

## 3. Store the key

```
uvx dottide import-secret dottide-bing
```

The command asks for the key with a hidden prompt and stores it in your system's secret store: the macOS keychain, Windows Credential Manager or the Linux Secret Service. Then close the Bing page.

## 4. Point your profile at the key

Add this section to your profile in `~/.config/dottide/` (see [Configuration](configuration.md)):

```
[bing]
keychain = "dottide-bing"
```

dotTide works out each site's Bing address from its Search Console property. If a site uses a different address in Bing, like `https://www.example.com/`, add `bing = "https://www.example.com/"` to that site's block.

## 5. Check access

```
uvx dottide sites
uvx dottide bing_queries example.com
```

Every site should show `"bing": "ok"`.

## Good to know

- **New sites start empty.** A site added to Bing Webmaster Tools can show no numbers for a few days, and Bing updates them about once a week. `bing_queries` says so instead of returning a blank.
- **Short ranges can be empty.** Bing reports by week, so a seven-day range sometimes falls between two reports. Try `--days 28` or more.
- **Replacing the key:** generate a new key in Bing and run `import-secret dottide-bing` again; dotTide uses the new one from then on.

## Fixing a failed check

- **`not in Bing Webmaster Tools`:** the site isn't in this Bing account, or its address differs. Add the site in Bing, or set `bing = "..."` on the site to the exact address Bing shows.
- **`Bing API 400` or `401`:** the key is wrong or was revoked. Generate a new one and run `import-secret` again.
- **`no stored secret named 'dottide-bing'`:** run step 3.
- **`profile ... has no [bing] keychain`:** add the section from step 4.
