from pathlib import Path
import importlib.util
import sys
import types

WAVESHARE_PATH = Path(__file__).resolve().parents[1] / "custom_components" / "mean_well_npb_750" / "waveshare.py"
serial_stub = types.ModuleType("serial")
serial_stub.EIGHTBITS = 8
serial_stub.PARITY_NONE = "N"
serial_stub.STOPBITS_ONE = 1
serial_stub.Serial = object
sys.modules.setdefault("serial", serial_stub)
SPEC = importlib.util.spec_from_file_location("waveshare", WAVESHARE_PATH)
waveshare = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["waveshare"] = waveshare
SPEC.loader.exec_module(waveshare)
CanFrame = waveshare.CanFrame
WaveshareUsbCan = waveshare.WaveshareUsbCan

class FakeSerial:
    def __init__(self):
        self.writes = []
        self.read_buffer = bytearray()
        self.is_open = True
    def write(self, payload):
        self.writes.append(payload)
    def flush(self):
        pass
    def read(self, size=1):
        if not self.read_buffer:
            return b""
        data = self.read_buffer[:size]
        del self.read_buffer[:size]
        return bytes(data)

def test_variable_extended_frame_encoding():
    adapter = WaveshareUsbCan("/dev/null")
    fake = FakeSerial()
    adapter._serial = fake
    adapter.send(CanFrame(0x000C0103, b"\x60\x00", is_extended_id=True))
    assert fake.writes[-1] == bytes.fromhex("AA E2 03 01 0C 00 60 00 55")

def test_variable_extended_frame_decoding():
    adapter = WaveshareUsbCan("/dev/null")
    fake = FakeSerial()
    fake.read_buffer.extend(bytes.fromhex("AA E4 03 00 0C 00 60 00 10 27 55"))
    adapter._serial = fake
    frame = adapter.receive(0.01)
    assert frame is not None
    assert frame.arbitration_id == 0x000C0003
    assert frame.data == bytes.fromhex("60 00 10 27")

if __name__ == "__main__":
    test_variable_extended_frame_encoding()
    test_variable_extended_frame_decoding()
