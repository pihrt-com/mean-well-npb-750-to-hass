"""Sensors for the Mean Well NPB-750 integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfTemperature
from homeassistant.core import HomeAssistant

from .commands import READ_REGISTERS
from .const import ATTR_RAW_VALUE, DOMAIN
from .coordinator import MeanWellCoordinator
from .entity import MeanWellEntity

UNIT_MAP = {"V": UnitOfElectricPotential.VOLT, "A": UnitOfElectricCurrent.AMPERE, "degC": UnitOfTemperature.CELSIUS}
DEVICE_CLASS_MAP = {"V": SensorDeviceClass.VOLTAGE, "A": SensorDeviceClass.CURRENT, "degC": SensorDeviceClass.TEMPERATURE}

@dataclass(frozen=True, kw_only=True)
class MeanWellSensorDescription(SensorEntityDescription):
    raw_key: str | None = None

SENSORS: tuple[MeanWellSensorDescription, ...] = tuple(
    MeanWellSensorDescription(key=r.key, translation_key=r.key, name=r.name, native_unit_of_measurement=UNIT_MAP.get(r.unit or ""), device_class=DEVICE_CLASS_MAP.get(r.unit or ""), state_class=SensorStateClass.MEASUREMENT if r.unit else None, suggested_display_precision=r.precision if r.unit else None, raw_key=r.key)
    for r in READ_REGISTERS
) + (
    MeanWellSensorDescription(key="adapter_status", translation_key="adapter_status", name="USB-CAN adapter status"),
    MeanWellSensorDescription(key="charger_status", translation_key="charger_status", name="Charger status"),
    MeanWellSensorDescription(key="last_error", translation_key="last_error", name="Last communication message"),
    MeanWellSensorDescription(key="can_settings", translation_key="can_settings", name="CAN settings"),
    MeanWellSensorDescription(key="device_path", translation_key="device_path", name="Serial device"),
    MeanWellSensorDescription(key="faults", translation_key="faults", name="Faults"),
    MeanWellSensorDescription(key="charge_flags", translation_key="charge_flags", name="Charge flags"),
    MeanWellSensorDescription(key="system_flags", translation_key="system_flags", name="System flags"),
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator: MeanWellCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(MeanWellSensor(coordinator, description) for description in SENSORS)

class MeanWellSensor(MeanWellEntity, SensorEntity):
    entity_description: MeanWellSensorDescription

    def __init__(self, coordinator: MeanWellCoordinator, description: MeanWellSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        value = self.coordinator.data.get(self.entity_description.key)
        if isinstance(value, list):
            return ", ".join(value) if value else "ok"
        if value is None and self.entity_description.key == "last_error":
            return "ok"
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.raw_key is None:
            return None
        raw = self.coordinator.data.get("raw", {})
        if not isinstance(raw, dict):
            return None
        raw_value = raw.get(self.entity_description.raw_key)
        if raw_value is None:
            return None
        return {ATTR_RAW_VALUE: raw_value, "raw_hex": f"0x{raw_value:04X}"}
