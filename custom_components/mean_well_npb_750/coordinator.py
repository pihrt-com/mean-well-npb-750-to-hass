"""Data coordinator for the Mean Well NPB-750 integration."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .charger import ChargerIdentity, MeanWellNpbCharger
from .commands import CHARGE_STATUS_BITS, FAULT_BITS, READ_REGISTERS, SYSTEM_STATUS_BITS
from .const import CONF_ADDRESS, CONF_CAN_BITRATE, CONF_SERIAL_BAUDRATE, DEFAULT_ADDRESS, DEFAULT_CAN_BITRATE, DEFAULT_SCAN_INTERVAL, DEFAULT_SERIAL_BAUDRATE
from .waveshare import WaveshareUsbCan

_LOGGER = logging.getLogger(__name__)

class MeanWellCoordinator(DataUpdateCoordinator[dict[str, object]]):
    """Poll charger state and expose commands to entities."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.identity = ChargerIdentity()
        self.device = entry.data["device"]
        self.serial_baudrate = entry.data.get(CONF_SERIAL_BAUDRATE, DEFAULT_SERIAL_BAUDRATE)
        self.can_bitrate = entry.data.get(CONF_CAN_BITRATE, DEFAULT_CAN_BITRATE)
        self.address = entry.data.get(CONF_ADDRESS, DEFAULT_ADDRESS)
        self.charger = MeanWellNpbCharger(WaveshareUsbCan(self.device, self.serial_baudrate, self.can_bitrate), self.address)
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
        return await asyncio.to_thread(self._read_data)

    def _read_data(self) -> dict[str, object]:
        data: dict[str, object] = self._base_data()
        raw: dict[str, int] = {}
        try:
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
            system_status = int(data.get("system_status", 0))
            curve_config = int(data.get("curve_config", 0))
            system_config = int(data.get("system_config", 0))
            fault_flags = _decode_bits(fault_status, FAULT_BITS)
            charge_flags = _decode_bits(charge_status, CHARGE_STATUS_BITS)
            system_flags = _decode_system_status(system_status)
            data["fault_status"] = _join_flags(fault_flags, "Bez chyb")
            data["charge_status"] = _join_flags(charge_flags, "Bez aktivnich priznaku nabijeni")
            data["system_status"] = _join_flags(system_flags, "Bez aktivnich systemovych priznaku")
            data["curve_config"] = _decode_curve_config(curve_config)
            data["system_config"] = _decode_system_config(system_config)
            data["faults"] = fault_flags
            data["charge_flags"] = charge_flags
            data["system_flags"] = system_flags
            data["charging_attention"] = _charging_attention(data, fault_flags, charge_flags)
            data["charger_connected"] = True
            data["charger_status"] = "Nabijecka MEAN WELL odpovida na CAN"
            data["last_error"] = None
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Charger did not answer: %s", err)
            data["charger_connected"] = False
            data["charger_status"] = "Nabijecka MEAN WELL neodpovida na CAN"
            data["last_error"] = (
                "USB-CAN prevodnik byl nalezen a otevren, ale nabijecka MEAN WELL neodpovida na CAN. "
                "Zkontrolujte napajeni nabijecky, CANH/CANL/GND, terminaci, adresu a rychlost CAN."
            )
            data["faults"] = []
            data["charge_flags"] = []
            data["system_flags"] = []
            data["charging_attention"] = "Nabijecka neodpovida"
        data["raw"] = raw
        return data

    def _base_data(self) -> dict[str, object]:
        return {
            "adapter_connected": True,
            "adapter_status": "USB-CAN prevodnik nalezen a otevren",
            "charger_connected": False,
            "charger_status": "Nabijecka MEAN WELL zatim neoverena",
            "last_error": None,
            "can_settings": f"CAN {self.can_bitrate} bit/s, extended frame, address {self.address}",
            "device_path": self.device,
            "serial_settings": f"Serial {self.serial_baudrate} bit/s",
        }

    async def async_test_adapter(self) -> None:
        await asyncio.to_thread(self.charger.configure_adapter)
        self.async_set_updated_data(
            {
                **(self.data or self._base_data()),
                "adapter_connected": True,
                "adapter_status": "USB-CAN prevodnik odpovedel na otevreni a konfiguraci",
                "last_error": None,
            }
        )

    async def async_test_charger(self) -> None:
        await self.async_request_refresh()

    async def async_set_operation(self, enabled: bool) -> None:
        currently_enabled = bool((self.data or {}).get("operation"))
        output_current = (self.data or {}).get("output_current")
        current_is_zero = isinstance(output_current, int | float) and output_current < 0.1
        if enabled and (not currently_enabled or current_is_zero):
            await asyncio.to_thread(self.charger.restart_charging, force=current_is_zero)
        else:
            await asyncio.to_thread(self.charger.write_operation, enabled)
        await self.async_request_refresh()

    async def async_restart_charging(self) -> None:
        await asyncio.to_thread(self.charger.restart_charging)
        await self.async_request_refresh()

    async def async_force_charging(self) -> None:
        await asyncio.to_thread(self.charger.restart_charging, force=True)
        await self.async_request_refresh()

    async def async_enable_automatic_recharge(self) -> None:
        await asyncio.to_thread(self.charger.enable_automatic_recharge)
        await self.async_request_refresh()

    async def async_set_voltage(self, value: float) -> None:
        await asyncio.to_thread(self.charger.set_output_voltage, value)
        await self.async_request_refresh()

    async def async_set_current(self, value: float) -> None:
        await asyncio.to_thread(self.charger.set_output_current, value)
        await self.async_request_refresh()


def _decode_bits(value: int, labels: dict[int, str]) -> list[str]:
    return [label for bit, label in labels.items() if value & (1 << bit)]


def _decode_system_status(value: int) -> list[str]:
    flags = ["DC vystup v normalnim rozsahu" if value & (1 << 1) else "DC vystup je prilis nizky"]
    flags.extend(_decode_bits(value, SYSTEM_STATUS_BITS))
    return flags


def _decode_curve_config(value: int) -> str:
    mode = "Rezim nabijecky" if value & (1 << 7) else "Rezim zdroje"
    return f"{mode}, raw 0x{value:04X}"


def _decode_system_config(value: int) -> str:
    flags = []
    flags.append("Automaticky restart nabijeni povolen" if value & (1 << 3) else "Automaticky restart nabijeni vypnuty")
    if value & (1 << 10):
        flags.append("Zapis do EEPROM vypnuty")
    else:
        flags.append("Zapis do EEPROM povoleny")
    return f"{', '.join(flags)}, raw 0x{value:04X}"


def _charging_attention(data: dict[str, object], fault_flags: list[str], charge_flags: list[str]) -> str:
    operation = data.get("operation")
    output_current = data.get("output_current")
    if operation is not True or not isinstance(output_current, int | float) or output_current >= 0.1:
        return "ok"
    if fault_flags:
        return f"Vystup je zapnuty, ale proud netece. Chybove priznaky: {', '.join(fault_flags)}"
    if charge_flags:
        return f"Vystup je zapnuty, ale proud netece. Priznaky nabijeni: {', '.join(charge_flags)}"
    return "Vystup je zapnuty, ale proud netece. Nabijecka muze byt v ochrannem nebo latch stavu; pokud nepomuze Vynutit start nabijeni, muze byt nutny AC re-power."


def _join_flags(flags: list[str], empty: str) -> str:
    return ", ".join(flags) if flags else empty
