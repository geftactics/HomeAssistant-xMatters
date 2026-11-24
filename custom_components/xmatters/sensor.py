from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XMattersDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([
        XMattersCurrentShiftEnds(entry.runtime_data, entry),
        XMattersNextOnCall(entry.runtime_data, entry),
        XMattersLastNotification(entry.runtime_data, entry),
        XMattersLastNotificationTime(entry.runtime_data, entry),
    ])


class XMattersSensor(CoordinatorEntity[XMattersDataUpdateCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: XMattersDataUpdateCoordinator, entry: ConfigEntry, suffix: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{suffix}"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.title, "manufacturer": "xMatters"}


class XMattersCurrentShiftEnds(XMattersSensor):
    _attr_name = "Current shift ends"
    _attr_icon = "mdi:clock-end"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "current_shift_ends")

    @property
    def native_value(self):
        current = self.coordinator.data.get("current", [])
        return _parse_time(current[0]["end"]) if current else None


class XMattersNextOnCall(XMattersSensor):
    _attr_name = "Next on call"
    _attr_icon = "mdi:calendar-clock"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "next_on_call")

    @property
    def native_value(self):
        upcoming = self.coordinator.data.get("upcoming", [])
        return _parse_time(upcoming[0]["start"]) if upcoming else None


class XMattersLastNotification(XMattersSensor):
    _attr_name = "Last notification"
    _attr_icon = "mdi:message"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "last_notification")

    @property
    def native_value(self):
        notification = self.coordinator.data.get("last_notification")
        if not notification:
            return None
        name = notification.get("name") or notification.get("eventId")
        return str(name)[:255] if name else None

    @property
    def extra_state_attributes(self):
        notification = self.coordinator.data.get("last_notification") or {}
        return {key: notification[key] for key in ("id", "name", "status", "priority", "incidentId") if key in notification}


class XMattersLastNotificationTime(XMattersSensor):
    _attr_name = "Last notification time"
    _attr_icon = "mdi:clock-alert"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "last_notification_time")

    @property
    def native_value(self):
        notification = self.coordinator.data.get("last_notification")
        return _parse_time(notification["created"]) if notification and notification.get("created") else None

    @property
    def extra_state_attributes(self):
        notification = self.coordinator.data.get("last_notification") or {}
        return {key: notification[key] for key in ("id", "name", "status", "priority", "incidentId") if key in notification}


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
