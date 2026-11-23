# xMatters for Home Assistant

HACS-compatible Home Assistant custom integration for xMatters on-call schedules and notifications.

Repository: https://github.com/geftactics/hass-xmatters

## Home Assistant integration

Install the repository through HACS as a custom repository, or copy `custom_components/xmatters` into the `custom_components` directory of your Home Assistant configuration. Restart Home Assistant, then add **xMatters** from Settings → Devices & services.

The config flow asks for the xMatters company URL, username, API key, and API secret. It validates the credentials, lists the user’s group memberships, and creates one Home Assistant config entry for the selected group. Multiple account/group entries are supported.

The initial integration creates entities for on-call status, current shift end, current shift remaining, next on-call start, and the last xMatters notification. The default polling interval is 60 seconds and the notification lookback is 7 days; both are configurable during setup.

The integration uses HTTP Basic authentication with the API key as the username, prefixed with `x-api-key-` as required by xMatters, and the secret as the password. It makes read-only API requests for user, group, on-call, and event data.
