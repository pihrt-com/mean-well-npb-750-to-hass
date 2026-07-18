"""Button platform for Mean Well NPB-750 diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import MeanWellCoordinator
from .entity import MeanWellEntity


@dataclass(frozen=True, kw_only=True)
class MeanWellButtonDescription(ButtonEntityDescription):
    method: str


BUTTONS: tuple[MeanWellButtonDescription, ...] = (
    MeanWellButtonDescription(
        key="test_adapter",
        translation_key="test_adapter",
        name="Test USB-CAN adapter",
        method="async_test_adapter",
    ),
    MeanWellButtonDescription(
        key="test_charger",
        translation_key="test_charger",
        name="Test charger communication",
        method="async_test_charger",
    ),
    MeanWellButtonDescription(
        key="restart_charging",
        translation_key="restart_charging",
        name="Restart charging",
        method="async_restart_charging",
    ),
    MeanWellButtonDescription(
        key="force_charging",
        translation_key="force_charging",
        name="Force charging start",
        method="async_force_charging",
    ),
    MeanWellButtonDescription(
        key="enable_automatic_recharge",
        translation_key="enable_automatic_recharge",
        name="Enable automatic recharge",
        method="async_enable_automatic_recharge",
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator: MeanWellCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(MeanWellButton(coordinator, description) for description in BUTTONS)


class MeanWellButton(MeanWellEntity, ButtonEntity):
    entity_description: MeanWellButtonDescription

    def __init__(self, coordinator: MeanWellCoordinator, description: MeanWellButtonDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        method: Callable[[], Awaitable[None]] = getattr(self.coordinator, self.entity_description.method)
        await method()
