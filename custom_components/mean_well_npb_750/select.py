"""Select platform for Mean Well NPB-750 operating mode."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import MeanWellCoordinator
from .entity import MeanWellEntity

MODE_CHARGER = "Nabijec"
MODE_POWER_SUPPLY = "Zdroj"
OPTIONS = [MODE_CHARGER, MODE_POWER_SUPPLY]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator: MeanWellCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MeanWellOperatingModeSelect(coordinator)])


class MeanWellOperatingModeSelect(MeanWellEntity, SelectEntity):
    """Select charger mode or power-supply mode."""

    _attr_name = "Rezim"
    _attr_translation_key = "operating_mode"
    _attr_options = OPTIONS

    def __init__(self, coordinator: MeanWellCoordinator) -> None:
        super().__init__(coordinator, "operating_mode")

    @property
    def current_option(self) -> str | None:
        raw = self.coordinator.data.get("raw", {})
        if not isinstance(raw, dict):
            return None
        curve_config = raw.get("curve_config")
        if not isinstance(curve_config, int):
            return None
        return MODE_CHARGER if curve_config & 0x0080 else MODE_POWER_SUPPLY

    async def async_select_option(self, option: str) -> None:
        if option not in OPTIONS:
            raise ValueError(f"Unsupported operating mode: {option}")
        await self.coordinator.async_set_power_supply_mode(option == MODE_POWER_SUPPLY)
