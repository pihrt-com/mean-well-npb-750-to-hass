"""Waveshare USB-CAN-A serial protocol support."""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

import serial

HEADER = 0xAA
END = 0x55
VARIABLE_CONFIG = 0x12
CAN_BITRATE_CODES = {1000000: 0x01, 800000: 0x02, 500000: 0x03, 400000: 0x04, 250000: 0x05, 200000: 0x06, 125000: 0x07, 100000: 0x08, 50000: 0x09, 20000: 0x0A, 10000: 0x0B, 5000: 0x0C}

@dataclass(frozen=True)
class CanFrame:
    """A CAN 2.0 frame."""

    arbitration_id: int
    data: bytes
    is_extended_id: bool = True
    is_remote_frame: bool = False

class WaveshareUsbCan:
    """Serial transport for Waveshare USB-CAN-A in variable-length mode."""

    def __init__(self, port: str, serial_baudrate: int = 2000000, can_bitrate: int = 250000, timeout: float = 0.2) -> None:
        self._port = port
        self._serial_baudrate = serial_baudrate
        self._can_bitrate = can_bitrate
        self._timeout = timeout
        self._serial: serial.Serial | None = None

    def open(self) -> None:
        """Open the serial port and configure the adapter."""

        if self._serial and self._serial.is_open:
            return
        self._serial = serial.Serial(self._port, self._serial_baudrate, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=self._timeout, write_timeout=self._timeout)
        self.configure()

    def close(self) -> None:
        """Close the serial port."""

        if self._serial:
            self._serial.close()
            self._serial = None

    def configure(self) -> None:
        """Set variable protocol, extended frames, 250 kbit/s CAN, normal mode."""

        if self._can_bitrate not in CAN_BITRATE_CODES:
            raise ValueError(f"Unsupported CAN bitrate: {self._can_bitrate}")
        payload = bytearray([HEADER, END, VARIABLE_CONFIG, CAN_BITRATE_CODES[self._can_bitrate], 0x02, 0, 0, 0, 0, 0, 0, 0, 0, 0x00, 0x00, 0, 0, 0, 0])
        payload.append(sum(payload[2:]) & 0xFF)
        self._write(bytes(payload))

    def send(self, frame: CanFrame) -> None:
        """Send a CAN frame."""

        if len(frame.data) > 8:
            raise ValueError("CAN 2.0 frames can carry at most 8 data bytes")
        frame_type = 0xC0 | len(frame.data)
        if frame.is_extended_id:
            frame_type |= 0x20
            frame_id = frame.arbitration_id.to_bytes(4, "little")
        else:
            frame_id = frame.arbitration_id.to_bytes(2, "little")
        if frame.is_remote_frame:
            frame_type |= 0x10
        self._write(bytes([HEADER, frame_type]) + frame_id + frame.data + bytes([END]))

    def receive(self, timeout: float = 1.0) -> CanFrame | None:
        """Receive one CAN frame from the adapter."""

        serial_port = self._require_serial()
        deadline = monotonic() + timeout
        while monotonic() < deadline:
            marker = serial_port.read(1)
            if not marker or marker[0] != HEADER:
                continue
            type_raw = serial_port.read(1)
            if not type_raw:
                continue
            frame_type = type_raw[0]
            length = frame_type & 0x0F
            is_extended = bool(frame_type & 0x20)
            is_remote = bool(frame_type & 0x10)
            id_len = 4 if is_extended else 2
            frame_id_raw = serial_port.read(id_len)
            data = serial_port.read(length)
            end = serial_port.read(1)
            if len(frame_id_raw) != id_len or len(data) != length or end != bytes([END]):
                continue
            return CanFrame(int.from_bytes(frame_id_raw, "little"), data, is_extended, is_remote)
        return None

    def _write(self, payload: bytes) -> None:
        serial_port = self._require_serial()
        serial_port.write(payload)
        serial_port.flush()

    def _require_serial(self) -> serial.Serial:
        if not self._serial or not self._serial.is_open:
            raise RuntimeError("Serial port is not open")
        return self._serial
