"""Config flow for the Mean Well NPB-750 integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import CONF_ADDRESS, CONF_CAN_BITRATE, CONF_SERIAL_BAUDRATE, DEFAULT_ADDRESS, DEFAULT_CAN_BITRATE, DEFAULT_DEVICE, DEFAULT_SERIAL_BAUDRATE, DOMAIN

class MeanWellConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mean Well NPB-750."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""

        if user_input is not None:
            user_input = dict(user_input)
            user_input[CONF_ADDRESS] = int(user_input[CONF_ADDRESS])
            user_input[CONF_CAN_BITRATE] = int(user_input[CONF_CAN_BITRATE])
            user_input[CONF_SERIAL_BAUDRATE] = int(user_input[CONF_SERIAL_BAUDRATE])
            await self.async_set_unique_id(f"{user_input[CONF_DEVICE]}-{user_input[CONF_ADDRESS]}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=f"Mean Well NPB-750 ({user_input[CONF_DEVICE]})", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_DEVICE, default=DEFAULT_DEVICE): selector.TextSelector(),
            vol.Required(CONF_ADDRESS, default=DEFAULT_ADDRESS): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=3, mode=selector.NumberSelectorMode.BOX)),
            vol.Required(CONF_CAN_BITRATE, default=DEFAULT_CAN_BITRATE): selector.SelectSelector(selector.SelectSelectorConfig(options=["250000", "125000", "500000", "1000000"], mode=selector.SelectSelectorMode.DROPDOWN)),
            vol.Required(CONF_SERIAL_BAUDRATE, default=DEFAULT_SERIAL_BAUDRATE): selector.SelectSelector(selector.SelectSelectorConfig(options=["2000000", "1228800", "115200", "38400", "19200", "9600"], mode=selector.SelectSelectorMode.DROPDOWN)),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors={})

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        """Import YAML configuration."""

        return await self.async_step_user(user_input)
