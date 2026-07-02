"""Mean Well NPB/NPP CAN command definitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

class Command(IntEnum):
    """CAN command codes used by NPB-450/750/1200/1700 chargers."""

    OPERATION = 0x0000
    VOUT_SET = 0x0020
    IOUT_SET = 0x0030
    FAULT_STATUS = 0x0040
    READ_VIN = 0x0050
    READ_VOUT = 0x0060
    READ_IOUT = 0x0061
    READ_TEMPERATURE_1 = 0x0062
    MFR_ID_B0B5 = 0x0080
    MFR_ID_B6B11 = 0x0081
    MFR_MODEL_B0B5 = 0x0082
    MFR_MODEL_B6B11 = 0x0083
    MFR_REVISION_B0B5 = 0x0084
    MFR_LOCATION_B0B2 = 0x0085
    MFR_DATE_B0B5 = 0x0086
    MFR_SERIAL_B0B5 = 0x0087
    MFR_SERIAL_B6B11 = 0x0088
    CURVE_CC = 0x00B0
    CURVE_CV = 0x00B1
    CURVE_FV = 0x00B2
    CURVE_TC = 0x00B3
    CURVE_CONFIG = 0x00B4
    CURVE_CC_TIMEOUT = 0x00B5
    CURVE_CV_TIMEOUT = 0x00B6
    CURVE_FV_TIMEOUT = 0x00B7
    CHG_STATUS = 0x00B8
    CHG_RST_VBAT = 0x00B9
    SCALING_FACTOR = 0x00C0
    SYSTEM_STATUS = 0x00C1
    SYSTEM_CONFIG = 0x00C2

@dataclass(frozen=True)
class Register:
    """A readable charger register."""

    key: str
    name: str
    command: Command
    scale: float
    unit: str | None
    precision: int

READ_REGISTERS: tuple[Register, ...] = (
    Register("input_voltage", "Input voltage", Command.READ_VIN, 0.1, "V", 1),
    Register("output_voltage", "Output voltage", Command.READ_VOUT, 0.01, "V", 2),
    Register("output_current", "Output current", Command.READ_IOUT, 0.01, "A", 2),
    Register("temperature", "Internal temperature", Command.READ_TEMPERATURE_1, 0.1, "degC", 1),
    Register("fault_status", "Fault status", Command.FAULT_STATUS, 1, None, 0),
    Register("charge_status", "Charge status", Command.CHG_STATUS, 1, None, 0),
    Register("system_status", "System status", Command.SYSTEM_STATUS, 1, None, 0),
)
FAULT_BITS = {1: "otp", 2: "ovp", 3: "olp", 4: "short", 5: "ac_fail", 6: "output_off", 7: "high_temperature"}
CHARGE_STATUS_BITS = {0: "full", 1: "cc_mode", 2: "cv_mode", 3: "float_mode", 5: "stop", 10: "button_control", 13: "cc_timeout", 14: "cv_timeout", 15: "float_timeout"}
