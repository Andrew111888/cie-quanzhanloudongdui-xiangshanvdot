#include <stdint.h>
#include "console.h"

volatile uint32_t expected_illegal;
static uint32_t rng = 20261105;
static uint32_t next_random(void) {
  rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5;
  return rng;
}
static uint32_t dot(const int8_t *a, const int8_t *b) {
  int32_t sum = 0;
  for (unsigned i = 0; i < 8; ++i) sum += (int32_t)a[i] * b[i];
  return (uint32_t)sum;
}
static int result_is(const uint32_t *value, uint32_t expected) {
  return value[0] == expected && !value[1] && !value[2] && !value[3];
}
#define STR1(x) #x
#define STR(x) STR1(x)
#define VDOT(d,a,b) ".word (0x0200000b | (" STR(b) " << 20) | (" STR(a) " << 15) | (" STR(d) " << 7))\n"

int main(void) {
  int8_t a[8][16] __attribute__((aligned(16)));
  int8_t b[16] __attribute__((aligned(16)));
  uint32_t out[12][4] __attribute__((aligned(16)));
  const uint32_t sentinel[4] __attribute__((aligned(16))) =
    {0x01234567, 0x89abcdef, 0x76543210, 0xfedcba98};
  unsigned taken = 0;
  for (unsigned burst = 0; burst < 64; ++burst) {
    for (unsigned j = 0; j < 8; ++j)
      for (unsigned i = 0; i < 16; ++i) a[j][i] = (int8_t)next_random();
    for (unsigned i = 0; i < 16; ++i) b[i] = (int8_t)next_random();
    __asm__ volatile(
      "vsetivli zero,16,e8,m1,tu,mu\n mv t0,%0\n"
      "vle8.v v8,(t0)\n addi t0,t0,16\n"
      "vle8.v v9,(t0)\n addi t0,t0,16\n"
      "vle8.v v10,(t0)\n addi t0,t0,16\n"
      "vle8.v v11,(t0)\n addi t0,t0,16\n"
      "vle8.v v12,(t0)\n addi t0,t0,16\n"
      "vle8.v v13,(t0)\n addi t0,t0,16\n"
      "vle8.v v14,(t0)\n addi t0,t0,16\n vle8.v v15,(t0)\n"
      "vle8.v v24,(%1)\n vle8.v v26,(%2)\n vle8.v v27,(%2)\n"
      "vsetivli zero,8,e8,m1,tu,mu\n"
      // Independent values expose destination-tag or data pipeline shifts.
      VDOT(16,8,24) VDOT(17,9,24) VDOT(18,10,24) VDOT(19,11,24)
      VDOT(20,12,24) VDOT(21,13,24) VDOT(22,14,24) VDOT(23,15,24)
      "mv t0,%3\n"
      "vs1r.v v16,(t0)\n addi t0,t0,16\n"
      "vs1r.v v17,(t0)\n addi t0,t0,16\n"
      "vs1r.v v18,(t0)\n addi t0,t0,16\n"
      "vs1r.v v19,(t0)\n addi t0,t0,16\n"
      "vs1r.v v20,(t0)\n addi t0,t0,16\n"
      "vs1r.v v21,(t0)\n addi t0,t0,16\n"
      "vs1r.v v22,(t0)\n addi t0,t0,16\n"
      "vs1r.v v23,(t0)\n addi t0,t0,16\n"
      // Vector producer, dot consumer, then a chain through aliased v8.
      "vadd.vv v8,v8,v9\n" VDOT(25,8,24)
      "vs1r.v v25,(t0)\n addi t0,t0,16\n"
      ".rept 16\n" VDOT(8,8,24) ".endr\n"
      "vs1r.v v8,(t0)\n"
      : : "r"(a), "r"(b), "r"(sentinel), "r"(out)
      : "t0", "memory", "v8", "v9", "v10", "v11", "v12", "v13", "v14", "v15",
        "v16", "v17", "v18", "v19", "v20", "v21", "v22", "v23", "v24", "v25", "v26", "v27");
    uint64_t numerator = ((uint64_t)next_random() << 32) | next_random();
    uint64_t denominator = next_random() | 1u;
    uint64_t quotient;
    __asm__ volatile("divu %0,%1,%2" : "=r"(quotient) : "r"(numerator), "r"(denominator));
    if (quotient & 1) {
      ++taken;
      __asm__ volatile(VDOT(26,9,24) ::: "v26");
    } else {
      __asm__ volatile(VDOT(27,9,24) ::: "v27");
    }
    __asm__ volatile("vs1r.v v26,(%0)\n vs1r.v v27,(%1)" : : "r"(out[10]), "r"(out[11]) : "memory");
    for (unsigned j = 0; j < 8; ++j) if (!result_is(out[j], dot(a[j],b))) return 81;
    int8_t mixed[8], packed[8];
    for (unsigned i = 0; i < 8; ++i) mixed[i] = (int8_t)((uint8_t)a[0][i] + (uint8_t)a[1][i]);
    uint32_t expected = dot(mixed,b);
    if (!result_is(out[8], expected)) return 82;
    for (unsigned repeat = 1; repeat < 16; ++repeat) {
      for (unsigned i = 0; i < 8; ++i) packed[i] = i < 4 ? (int8_t)(expected >> (8*i)) : 0;
      expected = dot(packed,b);
    }
    if (!result_is(out[9], expected)) return 83;
    unsigned selected = (quotient & 1) ? 10 : 11;
    unsigned untouched = selected == 10 ? 11 : 10;
    if (!result_is(out[selected], dot(a[1],b))) return 84;
    for (unsigned i = 0; i < 4; ++i) if (out[untouched][i] != sentinel[i]) return 85;
  }
  if (!taken || taken == 64) return 86;
  puts_uart("PIPELINE_PASS bursts=64 vdot_instructions=1664 taken=");
  print_uint(taken); puts_uart(" not_taken="); print_uint(64-taken); putch('\n');
  return 0;
}
