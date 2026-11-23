# xMatters for Home Assistant

Home Assistant Marketplace custom integration for xMatters on-call schedules and notifications.

Repository: https://github.com/geftactics/hass-xmatters

## Install from Home Assistant Marketplace

1. Open **Settings → Marketplace** in Home Assistant.
2. Select **Add from link** and enter `https://github.com/geftactics/hass-xmatters`.
3. Find **xMatters** in Marketplace and install it.
4. Add **xMatters** from **Settings → Devices & services**.

Before setup, create xMatters API credentials from your xMatters profile: open **Profile → More Actions → Manage API Keys**, create an API key, and copy both the key and secret. The secret is shown only when it is created.

The config flow asks for the xMatters company URL, username, API key, and API secret. The company URL should look like `yourcompany.xmatters.com`. It validates the URL and credentials, lists the user’s group memberships, and creates one Home Assistant config entry for the selected group. Multiple account/group entries are supported.

The initial integration creates entities for on-call status, current shift end, current shift remaining, next on-call start, and the last xMatters notification. The default polling interval is 60 seconds and the notification lookback is 7 days.

The integration uses HTTP Basic authentication with the API key as the username, prefixed with `x-api-key-` as required by xMatters, and the secret as the password. It makes read-only API requests for user, group, on-call, and event data.

## Local tests

The API filtering and date-range behavior can be tested without Home Assistant or xMatters credentials:

```sh
python3 -m unittest discover -s tests -v
```

The integration also treats notification-history failures as non-fatal, so on-call entities can still start if the xMatters events endpoint returns a permission or server error.
