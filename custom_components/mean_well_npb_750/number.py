"""Number platform for Mean Well NPB-750 setpoints."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent, UnitOfElectricPotential
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import MeanWellCoordinator
from .entity import MeanWellEntity

@dataclass(frozen=True, kw_only=True)
class MeanWellNumberDescription(NumberEntityDescription):
    method: str

NUMBERS: tuple[MeanWellNumberDescription, ...] = (
    MeanWellNumberDescription(key="output_voltage_set", translation_key="output_voltage_set", name="Output voltage set", native_min_value=21.0, native_max_value=42.0, native_step=0.01, native_unit_of_measurement=UnitOfElectricPotential.VOLT, mode=NumberMode.BOX, method="async_set_voltage"),
    MeanWellNumberDescription(key="output_current_set", translation_key="output_current_set", name="Output current set", native_min_value=0.0, native_max_value=32.0, native_step=0.01, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, mode=NumberMode.BOX, method="async_set_current"),
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator: MeanWellCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(MeanWellNumber(coordinator, description) for description in NUMBERS)

class MeanWellNumber(MeanWellEntity, NumberEntity):
    entity_description: MeanWellNumberDescription

    def __init__(self, coordinator: MeanWellCoordinator, description: MeanWellNumberDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        if self.entity_description.key == "output_voltage_set":
            saved_voltage = self.coordinator.saved_voltage_setpoint()
            if saved_voltage is not None:
                return saved_voltage
        if self.entity_description.key == "output_current_set":
            saved_current = self.coordinator.saved_current_setpoint()
            if saved_current is not None:
                return saved_current
        value = self.coordinator.data.get("output_voltage" if self.entity_description.key == "output_voltage_set" else "output_current")
        return float(value) if isinstance(value, int | float) else None

    @property
    def available(self) -> bool:
        return super().available and bool(self.coordinator.data.get("charger_connected"))

    async def async_set_native_value(self, value: float) -> None:
        method = getattr(self.coordinator, self.entity_description.method)
        await method(value)
