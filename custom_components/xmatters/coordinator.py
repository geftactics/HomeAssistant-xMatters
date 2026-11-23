from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import XMattersApi, XMattersApiError
from .const import CONF_GROUP_ID, CONF_LOOKBACK_DAYS, CONF_USERNAME


class XMattersDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch one configured xMatters account/group on a regular interval."""

    def __init__(self, hass: HomeAssistant, api: XMattersApi, entry: ConfigEntry) -> None:
        self.api = api
        self.entry = entry
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name=f"xMatters {entry.title}",
            update_interval=timedelta(seconds=entry.data["scan_interval"]),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            user = await self.api.get_user(self.entry.data[CONF_USERNAME])
            shifts = await self.api.get_on_call(
                self.entry.data[CONF_GROUP_ID],
                user,
                days=90,
            )
            notification = await self.api.get_last_notification(
                user.get("targetName", self.entry.data[CONF_USERNAME]),
                self.entry.data[CONF_LOOKBACK_DAYS],
            )
            now = datetime.now().astimezone()
            current = [
                shift
                for shift in shifts
                if datetime.fromisoformat(shift["start"].replace("Z", "+00:00")) <= now
                < datetime.fromisoformat(shift["end"].replace("Z", "+00:00"))
            ]
            upcoming = [
                shift
                for shift in shifts
                if datetime.fromisoformat(shift["start"].replace("Z", "+00:00")) > now
            ]
            return {
                "user": user,
                "current": current,
                "upcoming": upcoming,
                "last_notification": notification,
                "updated": now,
            }
        except XMattersApiError as err:
            raise UpdateFailed(str(err)) from err
