from __future__ import annotations

from datetime import datetime

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_GROUP_NAME, DOMAIN
from .coordinator import XMattersDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([XMattersOnCallCalendar(entry.runtime_data, entry)])


class XMattersOnCallCalendar(CoordinatorEntity[XMattersDataUpdateCoordinator], CalendarEntity):
    _attr_has_entity_name = True
    _attr_name = "On-call schedule"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator: XMattersDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.title, "manufacturer": "xMatters"}

    @property
    def event(self) -> CalendarEvent | None:
        shifts = self._matching_shifts(datetime.now().astimezone())
        return self._event_for(shifts[0]) if shifts else None

    async def async_get_events(self, hass: HomeAssistant, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
        return [
            self._event_for(shift)
            for shift in self._matching_shifts(start_date)
            if _parse(shift["start"]) < end_date and _parse(shift["end"]) > start_date
        ]

    def _matching_shifts(self, start_date: datetime) -> list[dict]:
        return sorted(
            [
                shift
                for shift in self.coordinator.data.get("current", []) + self.coordinator.data.get("upcoming", [])
                if _parse(shift["end"]) >= start_date
            ],
            key=lambda shift: shift["start"],
        )

    def _event_for(self, shift: dict) -> CalendarEvent:
        group = shift.get("group", {})
        name = shift.get("shift", {}).get("name") or shift.get("shift", {}).get("targetName") or "On call"
        group_name = group.get("name") or group.get("targetName") or self.coordinator.entry.data[CONF_GROUP_NAME]
        return CalendarEvent(
            start=_parse(shift["start"]),
            end=_parse(shift["end"]),
            summary=f"{group_name}: {name}",
            description="xMatters on-call coverage",
        )


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
