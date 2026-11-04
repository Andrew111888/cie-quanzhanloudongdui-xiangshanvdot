#include <stdint.h>
#include <stddef.h>
#include "console.h"

volatile uint32_t expected_illegal;
#ifndef RANDOM_CASES
#define RANDOM_CASES 1000
#endif
static uint32_t random_state = 20261104;
static uint32_t next_random(void) {
  random_state ^= random_state << 13;
  random_state ^= random_state >> 17;
  random_state ^= random_state << 5;
  return random_state;
}
static int32_t reference(const int8_t *a, const int8_t *b) {
  int32_t value = 0;
  for (unsigned i = 0; i < 8; ++i) value += (int32_t)a[i] * b[i];
  return value;
}
static void calculate(const int8_t *a, const int8_t *b, uint32_t *out, unsigned mode) {
  // Initialize all source and destination bits, then set the supported vl.
  __asm__ volatile(
    "vsetivli zero,16,e8,m1,tu,mu\n"
    "vle8.v v8,(%0)\n vle8.v v10,(%1)\n vmv.v.i v12,-1\n"
    "vsetivli zero,8,e8,m1,tu,mu\n"
    : : "r"(a), "r"(b) : "memory", "v8", "v10", "v12");
  switch (mode) {
    case 0: __asm__ volatile(".word 0x02a4060b" ::: "v12"); break; // vd12,vs1=8,vs2=10
    case 1: __asm__ volatile(".word 0x02a4040b\n vmv1r.v v12,v8" ::: "v8", "v12"); break;
    case 2: __asm__ volatile(".word 0x02a4050b\n vmv1r.v v12,v10" ::: "v10", "v12"); break;
    case 3: __asm__ volatile(".word 0x0284060b" ::: "v12"); break; // vs1=vs2=8
    default:
      // The widened products occupy v16's low 128 bits (8 x 16 bits).
      __asm__ volatile(
        "vwmul.vv v16,v8,v10\n"
        "vsetivli zero,4,e32,m1,tu,mu\n vmv.v.i v24,0\n"
        "vsetivli zero,8,e16,m1,tu,mu\n vwredsum.vs v24,v16,v24\n"
        "vmv1r.v v12,v24\n" ::: "memory", "v16", "v17", "v24", "v12");
  }
  __asm__ volatile("vs1r.v v12,(%0)" : : "r"(out) : "memory");
}

#ifdef VDOT_PROBE_STANDARD_VSTART
static int probe_standard_vmul_vstart(void) {
  // Optional probe: compare the selected core's behavior before and after changes.
  // Some implementations may trap for nonzero arithmetic vstart.
  uint8_t a[16] __attribute__((aligned(16)));
  uint8_t b[16] __attribute__((aligned(16)));
  uint8_t before[16] __attribute__((aligned(16)));
  uint8_t after[16] __attribute__((aligned(16)));
  uintptr_t current_vstart;
  for (unsigned i = 0; i < 16; ++i) {
    a[i] = i + 1;
    b[i] = 2;
    before[i] = 0x5a;
  }
  __asm__ volatile(
    "vsetivli zero,16,e8,m1,tu,mu\n"
    "vle8.v v8,(%1)\n vle8.v v10,(%2)\n vle8.v v12,(%3)\n"
    "csrwi vstart,3\n vmul.vv v12,v8,v10\n csrr %0,vstart\n"
    "vs1r.v v12,(%4)"
    : "=&r"(current_vstart)
    : "r"(a), "r"(b), "r"(before), "r"(after)
    : "memory", "v8", "v10", "v12");
  if (current_vstart != 0) return 60;
  for (unsigned i = 0; i < 16; ++i)
    if (after[i] != (i < 3 ? before[i] : (uint8_t)(a[i] * b[i]))) return 61;
  return 0;
}
#endif

static int test_illegal(void) {
  // Exact destination image must survive an illegal instruction, including vl=0.
  uint32_t before[4] __attribute__((aligned(16))) = {0xdeadbeef,0x12345678,0x87654321,0xabcdef01};
  uint32_t after[4] __attribute__((aligned(16)));
  for (unsigned kind = 0; kind < 7; ++kind) {
    __asm__ volatile("vl1re8.v v12,(%0)\n vsetivli zero,8,e8,m1,tu,mu" : : "r"(before) : "memory", "v12");
    switch (kind) {
      case 0: __asm__ volatile("vsetivli zero,8,e16,m1,tu,mu"); break;
      case 1: __asm__ volatile("vsetivli zero,8,e8,m2,tu,mu"); break;
      case 2: __asm__ volatile("vsetivli zero,7,e8,m1,tu,mu"); break;
      case 3: __asm__ volatile("vsetivli zero,0,e8,m1,tu,mu"); break;
      case 4: __asm__ volatile("csrwi vstart,1"); break;
      case 5: __asm__ volatile("vsetivli zero,8,e8,mf2,tu,mu"); break;
      default: break; // masked form
    }
    expected_illegal = 1;
    __asm__ volatile("fence rw,rw" ::: "memory");
    if (kind == 6) __asm__ volatile(".word 0x00a4060b" ::: "memory", "v12");
    else __asm__ volatile(".word 0x02a4060b" ::: "memory", "v12");
    if (expected_illegal) return 30 + kind;
    uintptr_t current_vstart;
    __asm__ volatile("csrr %0,vstart\n csrwi vstart,0\n vs1r.v v12,(%1)"
                     : "=r"(current_vstart) : "r"(after) : "memory");
    if (current_vstart != (kind == 4 ? 1u : 0u)) return 40 + kind;
    for (unsigned i = 0; i < 4; ++i) if (after[i] != before[i]) return 50 + kind;
  }
  return 0;
}

int main(void) {
  int8_t a[16] __attribute__((aligned(16)));
  int8_t b[16] __attribute__((aligned(16)));
  uint32_t out[4] __attribute__((aligned(16)));
  const int8_t limits[][2] = {{1,1},{-1,1},{-128,-128},{-128,127},{127,127},{0,-128}};
  int status = 0;
#ifdef VDOT_PROBE_STANDARD_VSTART
  status = probe_standard_vmul_vstart();
  if (status) return status;
#endif
  for (unsigned n = 0; n < 6 + RANDOM_CASES; ++n) {
    for (unsigned i = 0; i < 16; ++i) {
      a[i] = n < 6 ? limits[n][0] : (int8_t)next_random();
      b[i] = n < 6 ? limits[n][1] : (int8_t)next_random();
    }
    for (unsigned mode = 0; mode < 5; ++mode) {
      calculate(a, b, out, mode);
      uint32_t want = (uint32_t)reference(a, mode == 3 ? a : b);
      if (out[0] != want || out[1] || out[2] || out[3]) return 10 + mode;
    }
  }
  status = test_illegal();
  if (status) return status;
  puts_uart("VDOT_PASS random_cases="); print_uint(RANDOM_CASES);
  puts_uart(" directed_cases=6 modes=5 illegal_cases=7\n");
  return 0;
}
