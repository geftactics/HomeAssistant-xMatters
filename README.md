# xMatters for Home Assistant

![Integration usage](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.xmatters.total)

Home Assistant Marketplace custom integration for xMatters on-call schedules and notifications.

- [Features](#features)
- [How to install](#how-to-install)
- [How to set up](#how-to-set-up)
  - [Create xMatters API credentials](#create-xmatters-api-credentials)
  - [Add the integration](#add-the-integration)
- [Entities](#entities)

## Features

- Current on-call status for a selected xMatters group.
- Current shift end time and remaining minutes.
- Next scheduled on-call shift.
- Calendar entity containing up to 90 days of on-call coverage.
- Last xMatters notification delivered to the configured user.
- Multiple xMatters accounts and groups supported through separate config entries.

## How to install

The integration is installed through Home Assistant Marketplace. After installation, add the integration from **Settings → Devices & services**.

[![Open your Home Assistant instance and open a repository in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=geftactics&repository=HomeAssistant-xMatters&category=integration)

To install:

1. Select the button above, or open **Settings → Marketplace**.
2. If prompted, choose **Add from link** and enter `https://github.com/geftactics/HomeAssistant-xMatters`.
3. Select **xMatters** and install it.
4. Go to **Settings → Devices & services → Add integration** and search for **xMatters**.

## How to set up

### Create xMatters API credentials

Create an API key and secret in xMatters before starting the Home Assistant setup:

1. Open your xMatters profile.
2. Select **More Actions → Manage API Keys**.
3. Create a new API key credential.
4. Copy the API key and secret. The secret may only be shown when the credential is created.

The API key uses the permissions of the xMatters user who created it, so that user must be able to view people, group memberships, on-call schedules, and events.

### Add the integration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=xmatters)

During setup, enter:

- **Company URL**: for example, `yourcompany.xmatters.com`.
- **Username**: your xMatters target name or web login.
- **API key** and **API secret**: the credentials created above.
- **Polling interval**: defaults to 60 seconds; values from 30 to 3600 seconds are accepted.

The credentials are validated before Home Assistant asks you to select a group. Each account/group selection creates a separate config entry, so the same account can monitor multiple groups.

## Entities

Each configured account/group creates:

- `binary_sensor`: whether the user is currently on call.
- `sensor`: current shift end time.
- `sensor`: current shift remaining in minutes.
- `sensor`: next on-call start time.
- `sensor`: timestamp and details of the last xMatters notification.
- `calendar`: current and upcoming on-call coverage.

The integration requests up to 90 days of future schedule data from xMatters. The “Next on call” sensor exposes the first upcoming shift; the calendar contains all returned coverage.
