// SPDX-License-Identifier: MulanPSL-2.0
#include <stdint.h>
#include "console.h"

volatile uint32_t expected_illegal;
static const int8_t a[16] __attribute__((aligned(16))) =
    {1,1,1,1,1,1,1,1,11,12,13,14,15,16,17,18};
static const int8_t b[16] __attribute__((aligned(16))) =
    {1,1,1,1,1,1,1,1,-11,-12,-13,-14,-15,-16,-17,-18};
static const uint32_t seed[4] __attribute__((aligned(16))) =
    {0x12345678,0xdeadbeef,0x76543210,0xabcdef01};
static uint32_t dot_result[4] __attribute__((aligned(16)));
static uint32_t acc_result[4] __attribute__((aligned(16)));

#define OPERANDS \
    "vl1re8.v v8,(%0)\n vl1re8.v v10,(%1)\n vl1re32.v v12,(%2)\n" \
    "vsetivli zero,8,e8,m1,ta,ma\n"
#define STORE "vs1r.v v12,(%3)\n fence rw,rw\n"

__attribute__((noinline)) static void dot(void) {
  __asm__ volatile(OPERANDS ".word 0x02a4060b\n" STORE
                   ::"r"(a),"r"(b),"r"(seed),"r"(dot_result)
                   :"memory","v8","v10","v12");
}

__attribute__((noinline)) static void accumulate(void) {
  __asm__ volatile(OPERANDS ".word 0x06a4060b\n" STORE
                   ::"r"(a),"r"(b),"r"(seed),"r"(acc_result)
                   :"memory","v8","v10","v12");
}

int main(void) {
  int32_t expected = 0;
  for (unsigned i = 0; i < 8; ++i) expected += (int32_t)a[i] * (int32_t)b[i];
  dot();
  accumulate();
  if (dot_result[0] != (uint32_t)expected) return 81;
  if (acc_result[0] != seed[0] + (uint32_t)expected) return 82;
  for (unsigned i = 1; i < 4; ++i)
    if (dot_result[i] || acc_result[i]) return 83;
  puts_uart("CURRENT_TRACE_PASS dot_low32="); print_uint(dot_result[0]);
  puts_uart(" acc_low32="); print_uint(acc_result[0]);
  puts_uart(" high96=0 cases=2\n");
  return 0;
}
