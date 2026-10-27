# Google setup

dotTide reads Google data through a service account: a robot Google account with a key file. One service account can read every site you share with it, even when the sites belong to different Google accounts. Most people need just one. Make a second only if you want two groups of sites that no single key can read.

Do these steps once per service account, signed in as the Google account that should own the key. It takes about ten minutes.

The service account never gets a password and never signs in anywhere. It can only read the sites you share with it, and you can remove it from any site in one click.

## 1. Create the project

1. Open the [Google Cloud console](https://console.cloud.google.com/) and sign in with the profile's Google account.
2. Open the project picker at the top of the page and select **New project**.
3. Name it `dottide`. Leave the organization as **No organization**, then select **Create**.
4. Wait for the notification, then select the new project in the project picker.

## 2. Turn on the APIs

1. Open [Google Search Console API](https://console.cloud.google.com/apis/library/searchconsole.googleapis.com) and select **Enable**.
2. If any of your sites use GA4, also enable [Google Analytics Data API](https://console.cloud.google.com/apis/library/analyticsdata.googleapis.com), which reads the numbers, and [Google Analytics Admin API](https://console.cloud.google.com/apis/library/analyticsadmin.googleapis.com), which lets `dottide discover` find your GA4 properties.

Check that the project picker still shows `dottide` before each **Enable**.

## 3. Create the service account

1. Open [Service accounts](https://console.cloud.google.com/iam-admin/serviceaccounts) and select **Create service account**.
2. Name it `dottide-reader`. Select **Create and continue**.
3. Skip the role and the user access steps: the account needs no project role. Select **Done**.
4. Copy the account's email. It looks like `dottide-reader@dottide.iam.gserviceaccount.com`.

## 4. Download the key

1. Select the new service account, then open the **Keys** tab.
2. Select **Add key**, then **Create new key**, choose **JSON**, and select **Create**.
3. The browser downloads one JSON file. Treat it like a password: don't email it, don't put it in a repo.

## 5. Share each site with the service account

Do this signed in as whichever Google account owns the site. It can be a different account from step 1.

### Search Console

1. Open [Search Console](https://search.google.com/search-console) and pick the site's property.
2. Go to **Settings**, then **Users and permissions**, then **Add user**.
3. Paste the service account email, choose **Restricted**, and select **Add**.

### GA4, only for sites that have it

1. Open [Google Analytics](https://analytics.google.com/) and pick the site's property.
2. Go to **Admin**, then **Property access management**, select **+**, then **Add users**.
3. Paste the service account email, clear **Notify new users by email**, choose the **Viewer** role, and select **Add**.
4. Still in **Admin**, open **Property details** and copy the **Property ID**. It's a number like `123456789`, not the `G-` measurement ID.

## 6. Store the key and check access

```
uv run dottide import-key dottide-main ~/Downloads/<downloaded-key>.json
```

The command copies the key into the macOS keychain and reads it back to confirm. Then delete the downloaded file and empty the Trash.

Make a profile in `~/.config/dottide/` with just the `[key]` section (see [Configuration](configuration.md)), then let dotTide find your sites and add them:

```
uv run dottide discover
uv run dottide discover --write
uv run dottide sites
```

The first command shows what it found, the second adds it to the profile, and `sites` checks access for each one.

Every site should show `"search_console": "ok"`, and `"ga4": "ok"` where GA4 is used. A new share can take a few minutes to show up.

## Fixing a failed check

- **`not shared with this key`:** the site's owner hasn't added the service account email yet, or the property name in your profile differs from Search Console. `sites` prints the properties the key can see; copy the exact one.
- **`Google API 403 ... has not been used in project`:** the API from step 2 isn't enabled in this project.
- **`Google API 403 ... does not have sufficient permissions`** on GA4: the service account isn't a Viewer on that property, or the Property ID is wrong.
- **`no keychain item`:** run the `import-key` command from step 6.
