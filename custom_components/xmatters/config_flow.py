from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import XMattersApi, XMattersApiError, XMattersAuthError, normalise_instance
from .const import (
    CONF_API_KEY,
    CONF_API_SECRET,
    CONF_GROUP_ID,
    CONF_GROUP_NAME,
    CONF_INSTANCE,
    CONF_LOOKBACK_DAYS,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    DEFAULT_LOOKBACK_DAYS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


class XMattersConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle xMatters config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._credentials: dict[str, Any] = {}
        self._user: dict[str, Any] = {}
        self._memberships: list[dict[str, Any]] = []

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input:
            try:
                api = XMattersApi(
                    async_get_clientsession(self.hass),
                    user_input[CONF_INSTANCE],
                    user_input[CONF_API_KEY],
                    user_input[CONF_API_SECRET],
                )
                user, memberships = await api.validate(user_input[CONF_USERNAME])
                if not memberships:
                    errors["base"] = "no_groups"
                else:
                    self._credentials = {**user_input, CONF_INSTANCE: normalise_instance(user_input[CONF_INSTANCE])}
                    self._user = user
                    self._memberships = memberships
                    return await self.async_step_group()
            except XMattersAuthError:
                errors["base"] = "invalid_auth"
            except XMattersApiError:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_INSTANCE): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_API_KEY): str,
                    vol.Required(CONF_API_SECRET): str,
                    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
                    vol.Optional(CONF_LOOKBACK_DAYS, default=DEFAULT_LOOKBACK_DAYS): vol.All(vol.Coerce(int), vol.Range(min=1, max=30)),
                }
            ),
            errors=errors,
        )

    async def async_step_group(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input:
            group_id = user_input[CONF_GROUP_ID]
            group_name = next(
                (membership.get("group", {}).get("targetName", group_id) for membership in self._memberships if membership.get("group", {}).get("id") == group_id),
                group_id,
            )
            unique_id = f"{self._credentials[CONF_INSTANCE]}:{self._user['id']}:{group_id}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            data = {**self._credentials, CONF_GROUP_ID: group_id, CONF_GROUP_NAME: group_name}
            return self.async_create_entry(title=f"{self._user.get('targetName', self._credentials[CONF_USERNAME])}: {group_name}", data=data)

        options = [
            selector.SelectOptionDict(
                value=membership.get("group", {}).get("id"),
                label=membership.get("group", {}).get("targetName", membership.get("group", {}).get("id", "")),
            )
            for membership in self._memberships
            if membership.get("group", {}).get("id")
        ]
        return self.async_show_form(
            step_id="group",
            data_schema=vol.Schema({vol.Required(CONF_GROUP_ID): selector.SelectSelector(selector.SelectSelectorConfig(options=options))}),
        )
