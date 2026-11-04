"""Exercise one NEMU shared library through its real Difftest ABI, without RTL.

Run this script in a separate process for each library. The packed register
layout is bound to the pinned NEMU/Difftest pair documented in DIFFTEST_CHECKS.
"""
import argparse
import ctypes
import hashlib
from pathlib import Path
import struct
import sys

parser = argparse.ArgumentParser()
parser.add_argument('library', type=Path)
parser.add_argument('--expected-result', type=int, choices=(8, 9), required=True)
args = parser.parse_args()
if sys.byteorder != 'little':
    raise SystemExit('This pinned ABI probe requires a little-endian host')
path = args.library.resolve(strict=True)
reference = ctypes.CDLL(str(path))
signatures = {
    'difftest_set_ramsize': [ctypes.c_size_t],
    'difftest_init_v2': [ctypes.c_uint],
    'difftest_regcpy': [ctypes.c_void_p, ctypes.c_bool],
    'difftest_memcpy': [ctypes.c_uint64, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_bool],
    'difftest_exec': [ctypes.c_uint64],
}
for name, signature in signatures.items():
    function = getattr(reference, name)
    function.argtypes = signature
    function.restype = None

state = ctypes.create_string_buffer(1400)
reference.difftest_set_ramsize(128 * 1024 * 1024)
reference.difftest_init_v2(len(state))
reference.difftest_regcpy(state, False)


def put(offset, value):
    struct.pack_into('<Q', state, offset, value)


def get(offset):
    return struct.unpack_from('<Q', state, offset)[0]


put(512, 3)                    # machine mode
put(520, (get(520) & ~0x600) | 0x600)  # mstatus.VS = Dirty
put(656, 0x80000000)          # PC
put(664, 0)                   # non-virtualized execution
put(800 + 16 * 8, 0x0101010101010101)
put(800 + 16 * 10, 0x0101010101010101)
put(800 + 16 * 8 + 8, 0x7F7F7F7F7F7F7F7F)  # high source bytes ignored
put(800 + 16 * 10 + 8, 0x8080808080808080)
put(800 + 16 * 12, 0xFFFFFFFFFFFFFFFF)
put(800 + 16 * 12 + 8, 0xFFFFFFFFFFFFFFFF)
for offset, value in ((1312, 0), (1320, 0), (1328, 0), (1336, 0),
                      (1344, 8), (1352, 0), (1360, 16)):
    put(offset, value)
reference.difftest_regcpy(state, True)
instruction = ctypes.c_uint32(0x02A4060B)
reference.difftest_memcpy(0x80000000, ctypes.byref(instruction), 4, True)
reference.difftest_exec(1)
reference.difftest_regcpy(state, False)
actual = {'pc': get(656), 'v12_low': get(800 + 16 * 12),
          'v12_high': get(800 + 16 * 12 + 8), 'vstart': get(1312)}
expected = {'pc': 0x80000004, 'v12_low': args.expected_result,
            'v12_high': 0, 'vstart': 0}
if actual != expected:
    raise SystemExit(f'REF_ABI_FAIL expected={expected} actual={actual}')
print(f'REF_ABI_PASS sha256={hashlib.sha256(path.read_bytes()).hexdigest()} '
      f'v12_low={actual["v12_low"]} v12_high=0 vstart=0 pc=0x80000004', flush=True)
