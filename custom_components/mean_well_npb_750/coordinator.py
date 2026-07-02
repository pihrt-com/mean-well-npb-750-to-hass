"""Data coordinator for the Mean Well NPB-750 integration."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .charger import ChargerIdentity, MeanWellNpbCharger
from .commands import CHARGE_STATUS_BITS, FAULT_BITS, READ_REGISTERS
from .const import CONF_ADDRESS, CONF_CAN_BITRATE, CONF_SERIAL_BAUDRATE, DEFAULT_ADDRESS, DEFAULT_CAN_BITRATE, DEFAULT_SCAN_INTERVAL, DEFAULT_SERIAL_BAUDRATE
from .waveshare import WaveshareUsbCan

_LOGGER = logging.getLogger(__name__)

class MeanWellCoordinator(DataUpdateCoordinator[dict[str, object]]):
    """Poll charger state and expose commands to entities."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.identity = ChargerIdentity()
        self.charger = MeanWellNpbCharger(WaveshareUsbCan(entry.data["device"], entry.data.get(CONF_SERIAL_BAUDRATE, DEFAULT_SERIAL_BAUDRATE), entry.data.get(CONF_CAN_BITRATE, DEFAULT_CAN_BITRATE)), entry.data.get(CONF_ADDRESS, DEFAULT_ADDRESS))
        super().__init__(hass, _LOGGER, name="Mean Well NPB-750", update_interval=timedelta(seconds=entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)))

    async def async_connect(self) -> None:
        await asyncio.to_thread(self.charger.connect)
        try:
            self.identity = await asyncio.to_thread(self.charger.read_identity)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Could not read charger identity: %s", err)

    async def async_shutdown(self) -> None:
        await asyncio.to_thread(self.charger.close)

    async def _async_update_data(self) -> dict[str, object]:
        try:
            return await asyncio.to_thread(self._read_data)
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(str(err)) from err

    def _read_data(self) -> dict[str, object]:
        data: dict[str, object] = {}
        raw: dict[str, int] = {}
        for register in READ_REGISTERS:
            value = self.charger.read_register(register.command, 2)
            raw[register.key] = value
            data[register.key] = value if register.scale == 1 else round(value * register.scale, register.precision)
        try:
            data["operation"] = self.charger.read_operation()
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Could not read operation state: %s", err)
        fault_status = int(data.get("fault_status", 0))
        charge_status = int(data.get("charge_status", 0))
        data["faults"] = [name for bit, name in FAULT_BITS.items() if fault_status & (1 << bit)]
        data["charge_flags"] = [name for bit, name in CHARGE_STATUS_BITS.items() if charge_status & (1 << bit)]
        data["raw"] = raw
        return data

    async def async_set_operation(self, enabled: bool) -> None:
        await asyncio.to_thread(self.charger.write_operation, enabled)
        await self.async_request_refresh()

    async def async_set_voltage(self, value: float) -> None:
        await asyncio.to_thread(self.charger.set_output_voltage, value)
        await self.async_request_refresh()

    async def async_set_current(self, value: float) -> None:
        await asyncio.to_thread(self.charger.set_output_current, value)
        await self.async_request_refresh()
