"""Home Assistant integration for Mean Well NPB-750 chargers."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, PLATFORMS
from .coordinator import MeanWellCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Mean Well NPB-750 from a config entry."""

    coordinator = MeanWellCoordinator(hass, entry)
    try:
        await coordinator.async_connect()
    except Exception as err:  # noqa: BLE001
        raise ConfigEntryNotReady(
            f"USB-CAN adapter was not found or could not be opened at {entry.data.get('device')}: {err}"
        ) from err

    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady as err:
        await coordinator.async_shutdown()
        raise ConfigEntryNotReady(
            "USB-CAN adapter was found and opened, but the MEAN WELL charger is not responding on CAN. "
            "Connect and power the charger, then check CANH/CANL/GND wiring, termination, CAN address, and bitrate."
        ) from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    coordinator: MeanWellCoordinator | None = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if coordinator is not None:
        await coordinator.async_shutdown()
    return unload_ok
