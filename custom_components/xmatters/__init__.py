from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import XMattersApi
from .const import CONF_API_KEY, CONF_API_SECRET, CONF_INSTANCE, DOMAIN, PLATFORMS
from .coordinator import XMattersDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api = XMattersApi(
        async_get_clientsession(hass),
        entry.data[CONF_INSTANCE],
        entry.data[CONF_API_KEY],
        entry.data[CONF_API_SECRET],
    )
    coordinator = XMattersDataUpdateCoordinator(hass, api, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
