// SPDX-License-Identifier: MulanPSL-2.0
#include <stdint.h>
#include "console.h"

volatile uint32_t expected_illegal;
static const int8_t a[16] __attribute__((aligned(16))) =
  {-128,-128,-128,-128,-128,-128,-128,-128,11,12,13,14,15,16,17,18};
static const int8_t b[16] __attribute__((aligned(16))) =
  {-128,-128,-128,-128,-128,-128,-128,-128,-11,-12,-13,-14,-15,-16,-17,-18};
static uint32_t ordinary[4] __attribute__((aligned(16)));
static uint32_t baseline[4] __attribute__((aligned(16)));

/* Both paths receive the same preloaded sources and zero destination. The
 * baseline also prepares a zero reduction seed before the observed interval. */
#define PREPARE \
  "vl1re8.v v8,(%0)\n vl1re8.v v10,(%1)\n" \
  "vsetivli zero,4,e32,m1,tu,mu\n vmv.v.i v12,0\n vmv.v.i v0,0\n" \
  "vsetivli zero,8,e8,m1,ta,ma\n"
#define STORE "vs1r.v v12,(%2)\n fence rw,rw\n"

__attribute__((noinline)) static void use_vdot(void) {
  __asm__ volatile(PREPARE ".word 0x02a4060b\n" STORE
    ::"r"(a),"r"(b),"r"(ordinary):"memory","v0","v8","v10","v12");
}

__attribute__((noinline)) static void use_rvv(void) {
  __asm__ volatile(PREPARE
    "vwmul.vv v16,v8,v10\n"
    "vsetivli zero,8,e16,m1,tu,mu\n"
    "vwredsum.vs v12,v16,v0\n" STORE
    ::"r"(a),"r"(b),"r"(baseline):"memory","v0","v8","v10","v12","v16","v17");
}

int main(void) {
  int32_t expected=0;
  for (unsigned i=0;i<8;++i) expected+=(int32_t)a[i]*(int32_t)b[i];
  use_vdot();use_rvv();
  if (ordinary[0]!=(uint32_t)expected || baseline[0]!=(uint32_t)expected) return 91;
  for (unsigned i=1;i<4;++i) if (ordinary[i] || baseline[i]) return 92;
  puts_uart("BASELINE_WAVE_PASS expected=");print_uint(expected);
  puts_uart(" vdot=");print_uint(ordinary[0]);
  puts_uart(" rvv=");print_uint(baseline[0]);puts_uart(" high96=0\n");
  return 0;
}
