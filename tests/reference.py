"""Independent mathematical oracle; integer inputs are complete 128-bit registers."""
import json
from pathlib import Path

CONTRACT = json.loads((Path(__file__).resolve().parents[1] / "contract.json").read_text())


def signed_byte(reg, lane):
    byte = (reg >> (8 * lane)) & 255
    return byte if byte < 128 else byte - 256


def dot(vs1, vs2):
    if not (0 <= vs1 < 1 << 128 and 0 <= vs2 < 1 << 128):
        raise ValueError("source must be a 128-bit unsigned register image")
    return sum(signed_byte(vs1, i) * signed_byte(vs2, i) for i in range(8)) & 0xFFFFFFFF


def pack(values):
    if len(values) != 16 or any(not -128 <= v <= 127 for v in values):
        raise ValueError("expected 16 signed int8 elements")
    return sum((v & 255) << (8 * i) for i, v in enumerate(values))


def encode(vd, vs1, vs2, vm=1):
    if any(not 0 <= r < 32 for r in (vd, vs1, vs2)) or vm not in (0, 1):
        raise ValueError("invalid register or vm")
    return (int(CONTRACT["match"], 16) | vm << 25 | vs2 << 20 | vs1 << 15 | vd << 7)
