import random
import unittest
from reference import dot, pack, encode


class ReferenceTest(unittest.TestCase):
    def test_hand_calculated(self):
        for a, b, value in [(1, 1, 8), (-1, 1, -8), (-128, -128, 131072),
                            (-128, 127, -130048), (127, 127, 129032), (0, -128, 0)]:
            self.assertEqual(dot(pack([a] * 16), pack([b] * 16)), value & 0xFFFFFFFF)

    def test_high_lanes_ignored(self):
        rng = random.Random(20261104)
        for _ in range(1000):
            a, b = rng.getrandbits(64), rng.getrandbits(64)
            self.assertEqual(dot(a, b), dot(a | rng.getrandbits(64) << 64,
                                           b | rng.getrandbits(64) << 64))

    def test_encoding_fields(self):
        self.assertEqual(encode(12, 8, 10), 0x02A4060B)
        self.assertEqual(encode(0, 31, 31, 0), 0x01FF800B)


if __name__ == "__main__":
    unittest.main()
