#include <stdint.h>
#include "console.h"
#include "identity.h"
volatile uint32_t expected_illegal;
int main(void) {
  puts_uart("hello xiangshan, I am " VDOT_IDENTITY ", " VDOT_IP "\n");
  int8_t a[16] __attribute__((aligned(16)));
  int8_t b[16] __attribute__((aligned(16)));
  uint8_t out[16] __attribute__((aligned(16)));
  for (unsigned i = 0; i < 16; ++i) { a[i] = i - 8; b[i] = 3*i; }
  __asm__ volatile(
    "vsetivli zero,16,e8,m1,tu,mu\n"
    "vle8.v v8,(%0)\n vle8.v v10,(%1)\n"
    ".global vadd_target_pc\n vadd_target_pc:\n vadd.vv v12,v8,v10\n"
    "vse8.v v12,(%2)\n" : : "r"(a), "r"(b), "r"(out)
    : "memory", "v8", "v10", "v12");
  for (unsigned i = 0; i < 16; ++i) if (out[i] != (uint8_t)(a[i]+b[i])) return 1;
  puts_uart("VADD_PASS\n");
  return 0;
}
