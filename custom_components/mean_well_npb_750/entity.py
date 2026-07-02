"""Base entity helpers for the Mean Well NPB-750 integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MeanWellCoordinator

class MeanWellEntity(CoordinatorEntity[MeanWellCoordinator]):
    """Base entity for Mean Well NPB-750."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MeanWellCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        identity = self.coordinator.identity
        return DeviceInfo(identifiers={(DOMAIN, self.coordinator.entry.entry_id)}, manufacturer=identity.manufacturer or "MEAN WELL", model=identity.model or "NPB-750-24", name="Mean Well NPB-750", sw_version=identity.revision, serial_number=identity.serial_number)
