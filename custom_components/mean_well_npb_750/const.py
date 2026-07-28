"""Constants for the Mean Well NPB-750 integration."""

from __future__ import annotations

DOMAIN = "mean_well_npb_750"
CONF_ADDRESS = "address"
CONF_CAN_BITRATE = "can_bitrate"
CONF_OUTPUT_CURRENT_SETPOINT = "output_current_setpoint"
CONF_OUTPUT_VOLTAGE_SETPOINT = "output_voltage_setpoint"
CONF_SERIAL_BAUDRATE = "serial_baudrate"
DEFAULT_DEVICE = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"
DEFAULT_ADDRESS = 0x03
DEFAULT_CAN_BITRATE = 250000
DEFAULT_SERIAL_BAUDRATE = 2000000
DEFAULT_SCAN_INTERVAL = 10
PLATFORMS = ["sensor", "switch", "number", "button", "select"]
ATTR_RAW_VALUE = "raw_value"
