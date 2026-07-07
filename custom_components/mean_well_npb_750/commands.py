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
    Register("output_voltage", "Output voltage", Command.READ_VOUT, 0.01, "V", 2),
    Register("output_current", "Output current", Command.READ_IOUT, 0.01, "A", 2),
    Register("temperature", "Internal temperature", Command.READ_TEMPERATURE_1, 0.1, "degC", 1),
    Register("fault_status", "Fault status", Command.FAULT_STATUS, 1, None, 0),
    Register("charge_status", "Charge status", Command.CHG_STATUS, 1, None, 0),
    Register("system_status", "System status", Command.SYSTEM_STATUS, 1, None, 0),
)
FAULT_BITS = {
    1: "Prehrati nabijecky",
    2: "Prepeti na vystupu",
    3: "Nadproud na vystupu",
    4: "Zkrat na vystupu",
    5: "Chyba AC napajeni",
    6: "Vystup vypnuty",
    7: "Vysoka vnitrni teplota",
}
CHARGE_STATUS_BITS = {
    0: "Baterie plne nabita",
    1: "Rezim konstantniho proudu",
    2: "Rezim konstantniho napeti",
    3: "Udrzovaci nabijeni",
    6: "Probuzeni neni dokonceno",
    10: "Zkrat teplotni kompenzace",
    11: "Baterie nedetekovana",
    13: "Vyprsel cas konstantniho proudu",
    14: "Vyprsel cas konstantniho napeti",
    15: "Vyprsel cas udrzovaciho nabijeni",
}
SYSTEM_STATUS_BITS = {
    5: "Inicializace",
    6: "Chyba EEPROM",
}
