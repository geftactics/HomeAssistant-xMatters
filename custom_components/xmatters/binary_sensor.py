from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_GROUP_NAME, DOMAIN
from .coordinator import XMattersDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([XMattersOnCallBinarySensor(entry.runtime_data, entry)])


class XMattersOnCallBinarySensor(CoordinatorEntity[XMattersDataUpdateCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "On call"
    _attr_icon = "mdi:account-box"

    def __init__(self, coordinator: XMattersDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_on_call"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.title, "manufacturer": "xMatters"}

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("current"))

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        current = self.coordinator.data.get("current", [])
        return {"group": self._entry.data[CONF_GROUP_NAME], "current_shifts": len(current)}
