#include <stdint.h>
#include "console.h"

volatile uint32_t expected_illegal;

static void print_signed(int32_t value) {
  if (value < 0) {
    putch('-');
    print_uint((uint64_t)(-(int64_t)value));
  } else {
    print_uint((uint32_t)value);
  }
}

static void print_hex32(uint32_t value) {
  static const char digits[] = "0123456789abcdef";
  for (int shift = 28; shift >= 0; shift -= 4)
    putch(digits[(value >> shift) & 15u]);
}

int main(void) {
  const struct {
    const char *name;
    int8_t a;
    int8_t b;
    int32_t expected;
  } cases[] = {
    {"positive", 1, 1, 8},
    {"negative", -1, 1, -8},
    {"boundary_min_min", -128, -128, 131072},
    {"boundary_min_max", -128, 127, -130048},
    {"boundary_max_max", 127, 127, 129032},
    {"boundary_zero", 0, -128, 0},
  };
  int8_t a[16] __attribute__((aligned(16)));
  int8_t b[16] __attribute__((aligned(16)));
  uint32_t result[4] __attribute__((aligned(16)));

  for (unsigned n = 0; n < sizeof(cases) / sizeof(cases[0]); ++n) {
    for (unsigned i = 0; i < 16; ++i) {
      a[i] = i < 8 ? cases[n].a : (int8_t)(73 + i + n);
      b[i] = i < 8 ? cases[n].b : (int8_t)(-91 - i - n);
    }
    __asm__ volatile(
      "vsetivli zero,16,e8,m1,tu,mu\n"
      "vle8.v v8,(%1)\n"
      "vle8.v v10,(%2)\n"
      "vmv.v.i v12,-1\n"
      "vsetivli zero,8,e8,m1,tu,mu\n"
      ".word 0x02a4060b\n"
      "vs1r.v v12,(%0)\n"
      : : "r"(result), "r"(a), "r"(b)
      : "memory", "v8", "v10", "v12");

    int32_t reference = 0;
    for (unsigned i = 0; i < 8; ++i)
      reference += (int32_t)a[i] * b[i];
    const int passed = reference == cases[n].expected &&
      result[0] == (uint32_t)reference &&
      result[1] == 0 && result[2] == 0 && result[3] == 0;

    puts_uart("BASIC_CASE name="); puts_uart(cases[n].name);
    puts_uart(" a="); print_signed(cases[n].a);
    puts_uart(" b="); print_signed(cases[n].b);
    puts_uart(" count=8 expected="); print_signed(cases[n].expected);
    puts_uart(" actual="); print_signed((int32_t)result[0]);
    puts_uart(" vd=");
    for (int word = 3; word >= 0; --word) print_hex32(result[word]);
    puts_uart(passed ? " PASS\n" : " FAIL\n");
    if (!passed) return 10 + n;
  }
  puts_uart("VDOT_BASIC_PASS directed_cases=6\n");
  return 0;
}
