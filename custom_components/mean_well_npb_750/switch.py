"""Switch platform for Mean Well NPB-750."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import MeanWellCoordinator
from .entity import MeanWellEntity

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator: MeanWellCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MeanWellOperationSwitch(coordinator)])

class MeanWellOperationSwitch(MeanWellEntity, SwitchEntity):
    _attr_name = "Output"
    _attr_translation_key = "output"

    def __init__(self, coordinator: MeanWellCoordinator) -> None:
        super().__init__(coordinator, "operation")

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.get("operation")
        return bool(value) if value is not None else None

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_operation(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_operation(False)
