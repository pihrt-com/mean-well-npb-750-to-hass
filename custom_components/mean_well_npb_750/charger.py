"""Mean Well NPB charger protocol over CAN."""

from __future__ import annotations

from dataclasses import dataclass
from time import sleep

from .commands import Command
from .waveshare import CanFrame, WaveshareUsbCan

CONTROLLER_TO_CHARGER_BASE = 0x000C0100
CHARGER_TO_CONTROLLER_BASE = 0x000C0000

@dataclass(frozen=True)
class ChargerIdentity:
    """Device identity text assembled from manufacturer registers."""

    manufacturer: str | None = None
    model: str | None = None
    revision: str | None = None
    serial_number: str | None = None

class MeanWellNpbCharger:
    """Low-level Mean Well NPB/NPP CAN client."""

    def __init__(self, adapter: WaveshareUsbCan, address: int = 0x03) -> None:
        if not 0 <= address <= 0x03:
            raise ValueError("NPB CAN address must be between 0x00 and 0x03")
        self._adapter = adapter
        self._address = address

    @property
    def address(self) -> int:
        return self._address

    def connect(self) -> None:
        self._adapter.open()

    def configure_adapter(self) -> None:
        self._adapter.open()
        self._adapter.configure()

    def close(self) -> None:
        self._adapter.close()

    def read_register(self, command: Command, response_len: int = 2) -> int:
        data = self.query(command, response_len)
        return int.from_bytes(data[:response_len], "little")

    def read_text(self, first: Command, second: Command | None = None) -> str | None:
        chunks = [self.query(first, 6)]
        if second is not None:
            chunks.append(self.query(second, 6))
        text = b"".join(chunks).decode("ascii", errors="ignore").strip("\x00 ")
        return text or None

    def read_identity(self) -> ChargerIdentity:
        return ChargerIdentity(
            manufacturer=self.read_text(Command.MFR_ID_B0B5, Command.MFR_ID_B6B11),
            model=self.read_text(Command.MFR_MODEL_B0B5, Command.MFR_MODEL_B6B11),
            revision=self.read_text(Command.MFR_REVISION_B0B5),
            serial_number=self.read_text(Command.MFR_SERIAL_B0B5, Command.MFR_SERIAL_B6B11),
        )

    def read_operation(self) -> bool:
        return bool(self.read_register(Command.OPERATION, 1))

    def write_operation(self, enabled: bool) -> None:
        self.write_register(Command.OPERATION, bytes([0x01 if enabled else 0x00]))

    def restart_charging(self, *, force: bool = False) -> None:
        """Pulse remote operation off/on to restart charger-mode charging."""

        self.write_operation(False)
        sleep(2.0 if force else 1.0)
        self.write_operation(True)
        if force:
            sleep(3.0)
            self.write_operation(False)
            sleep(1.0)
        self.write_operation(True)

    def enable_automatic_recharge(self) -> int:
        """Enable RSTE in SYSTEM_CONFIG and return the written value."""

        system_config = self.read_register(Command.SYSTEM_CONFIG, 2)
        updated = system_config | 0x0008
        self.write_register(Command.SYSTEM_CONFIG, updated.to_bytes(2, "little"))
        sleep(0.2)
        return updated

    def set_output_voltage(self, volts: float) -> None:
        self.write_register(Command.VOUT_SET, int(round(volts / 0.01)).to_bytes(2, "little"))

    def set_output_current(self, amps: float) -> None:
        self.write_register(Command.IOUT_SET, int(round(amps / 0.01)).to_bytes(2, "little"))

    def query(self, command: Command, response_len: int) -> bytes:
        self._send(command)
        frame = self._wait_for_response(command)
        payload = frame.data[2:]
        if len(payload) < response_len:
            raise TimeoutError(f"Short response for command 0x{command:04X}")
        return payload[:response_len]

    def write_register(self, command: Command, payload: bytes) -> None:
        self._send(command, payload)
        sleep(0.05)

    def _send(self, command: Command, payload: bytes = b"") -> None:
        can_id = CONTROLLER_TO_CHARGER_BASE | self._address
        data = int(command).to_bytes(2, "little") + payload
        self._adapter.send(CanFrame(can_id, data, is_extended_id=True))

    def _wait_for_response(self, command: Command, timeout: float = 1.0) -> CanFrame:
        expected_id = CHARGER_TO_CONTROLLER_BASE | self._address
        while True:
            frame = self._adapter.receive(timeout)
            if frame is None:
                raise TimeoutError(f"No response for command 0x{command:04X}")
            if frame.arbitration_id != expected_id or len(frame.data) < 2:
                continue
            if int.from_bytes(frame.data[:2], "little") == command:
                return frame
