from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.storage import Store

from .api import XMattersApi, XMattersApiError
from .const import CONF_GROUP_ID, CONF_USERNAME, DEFAULT_LOOKBACK_DAYS

_LOGGER = logging.getLogger(__name__)


class XMattersDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch one configured xMatters account/group on a regular interval."""

    def __init__(self, hass: HomeAssistant, api: XMattersApi, entry: ConfigEntry) -> None:
        self.api = api
        self.entry = entry
        self._notification_store: Store[dict[str, Any]] = Store(
            hass,
            1,
            f"xmatters_last_notification_v2_{entry.entry_id}",
        )
        self._last_notification: dict[str, Any] | None = None
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name=f"xMatters {entry.title}",
            update_interval=timedelta(seconds=entry.data["scan_interval"]),
        )

    async def async_load_last_notification(self) -> None:
        stored = await self._notification_store.async_load()
        if isinstance(stored, dict):
            self._last_notification = stored

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            user = await self.api.get_user(self.entry.data[CONF_USERNAME])
            shifts = await self.api.get_on_call(
                self.entry.data[CONF_GROUP_ID],
                user,
                days=90,
            )
            try:
                notification = await self.api.get_last_notification(
                    user["id"],
                    self.entry.data[CONF_GROUP_ID],
                    DEFAULT_LOOKBACK_DAYS,
                )
            except XMattersApiError as err:
                # Notification history is useful but should not prevent the
                # on-call entities from starting when this endpoint is not
                # available to the API user or has a transient server error.
                _LOGGER.warning("Unable to fetch xMatters notification history: %s", err)
                notification = self._last_notification
            if _is_newer_notification(notification, self._last_notification):
                self._last_notification = notification
                await self._notification_store.async_save(notification)
            else:
                notification = self._last_notification
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


def _is_newer_notification(
    notification: dict[str, Any] | None,
    previous: dict[str, Any] | None,
) -> bool:
    """Return whether notification is newer than the persisted event."""
    if not notification:
        return False
    if not previous:
        return True
    created = notification.get("created")
    previous_created = previous.get("created")
    if not created or not previous_created:
        return notification.get("id") != previous.get("id")
    return created > previous_created
