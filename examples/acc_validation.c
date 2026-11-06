#include <stdint.h>
#include "console.h"

volatile uint32_t expected_illegal;
enum { RANDOM_CASES = 1000, MODES = 6, CHAIN_STEPS = 128 };
static uint32_t random_state = 20261106;
static uint32_t random_word(void) {
  random_state ^= random_state << 13;
  random_state ^= random_state >> 17;
  random_state ^= random_state << 5;
  return random_state;
}
static int error(unsigned code) {
  puts_uart("ACC_FAIL code="); print_uint(code); putch('\n');
  return (int)code;
}
static int32_t dot(const int8_t *a, const int8_t *b) {
  int32_t sum = 0;
  for (unsigned lane = 0; lane < 8; ++lane) sum += (int32_t)a[lane] * b[lane];
  return sum;
}
static uint32_t first_word(const int8_t *p) {
  uint32_t value = 0;
  for (unsigned i = 0; i < 4; ++i) value |= (uint32_t)(uint8_t)p[i] << (8 * i);
  return value;
}
static int complete_result(const uint32_t *out, uint32_t want) {
  return out[0] == want && !out[1] && !out[2] && !out[3];
}

// Reload all architectural source/destination bits before every alias mode.
// No memory operand is updated, so the three load addresses cannot alias an
// early-written GPR. The compiler is told every modified vector register.
static void calculate(const int8_t *a, const int8_t *b, const uint32_t *old,
                      uint32_t *out, unsigned mode) {
  __asm__ volatile(
    "vl1re8.v v8,(%0)\n vl1re8.v v10,(%1)\n vl1re8.v v12,(%2)\n"
    : : "r"(a), "r"(b), "r"(old) : "memory", "v8", "v10", "v12");
  if (mode & 256u) __asm__ volatile("vsetivli zero,8,e8,m1,ta,ma");
  else __asm__ volatile("vsetivli zero,8,e8,m1,tu,mu");
  switch (mode & 255u) {
    case 0: __asm__ volatile(".word 0x06a4060b" ::: "v12"); break;
    case 1: __asm__ volatile(".word 0x06a4040b\n vmv1r.v v12,v8" ::: "v8", "v12"); break;
    case 2: __asm__ volatile(".word 0x06a4050b\n vmv1r.v v12,v10" ::: "v10", "v12"); break;
    case 3: __asm__ volatile(".word 0x0684060b" ::: "v12"); break;
    case 4: __asm__ volatile(".word 0x0684040b\n vmv1r.v v12,v8" ::: "v8", "v12"); break;
    default: __asm__ volatile(".word 0x02a4060b" ::: "v12"); break;
  }
  __asm__ volatile("vs1r.v v12,(%0)" : : "r"(out) : "memory");
}

static int illegal_forms(void) {
  uint32_t before[4] __attribute__((aligned(16))) = {0xdeadbeef,0x12345678,0x87654321,0xabcdef01};
  uint32_t after[4] __attribute__((aligned(16)));
  for (unsigned kind = 0; kind < 7; ++kind) {
    __asm__ volatile("vl1re8.v v12,(%0)\n vsetivli zero,8,e8,m1,tu,mu"
                     : : "r"(before) : "memory", "v12");
    switch (kind) {
      case 0: __asm__ volatile("vsetivli zero,8,e16,m1,tu,mu"); break;
      case 1: __asm__ volatile("vsetivli zero,8,e8,m2,tu,mu"); break;
      case 2: __asm__ volatile("vsetivli zero,7,e8,m1,tu,mu"); break;
      case 3: __asm__ volatile("vsetivli zero,0,e8,m1,tu,mu"); break;
      case 4: __asm__ volatile("csrwi vstart,1"); break;
      case 5: __asm__ volatile("vsetivli zero,8,e8,mf2,tu,mu"); break;
      default: break;
    }
    expected_illegal = 1;
    __asm__ volatile("fence rw,rw" ::: "memory");
    if (kind == 6) __asm__ volatile(".word 0x04a4060b" ::: "memory", "v12");
    else __asm__ volatile(".word 0x06a4060b" ::: "memory", "v12");
    if (expected_illegal) return 30 + kind;
    uintptr_t actual_start, tval;
    __asm__ volatile("csrr %0,vstart\n csrr %1,mtval\n csrwi vstart,0\n vs1r.v v12,(%2)"
                     : "=&r"(actual_start), "=&r"(tval) : "r"(after) : "memory");
    if (actual_start != (kind == 4 ? 1u : 0u)) return 40 + kind;
    if (tval != (kind == 4 ? 0x06a4060bu : 0u)) return 50 + kind;
    for (unsigned i = 0; i < 4; ++i) if (after[i] != before[i]) return 60 + kind;
  }
  expected_illegal = 1;
  __asm__ volatile("fence rw,rw\n .word 0x0000007b" ::: "memory");
  uintptr_t tval;
  __asm__ volatile("csrr %0,mtval" : "=r"(tval));
  if (expected_illegal || tval != 0x7b) return 69;
  puts_uart("ACC_ILLEGAL_PASS forms=7 destination_and_vstart_preserved=1 ordinary_tval=123\n");
  return 0;
}

static int accumulator_chains(unsigned chains) {
  int8_t a[16] __attribute__((aligned(16)));
  int8_t b[16] __attribute__((aligned(16)));
  uint32_t seed[4][4] __attribute__((aligned(16)));
  uint32_t out[4][4] __attribute__((aligned(16)));
  for (unsigned i = 0; i < 16; ++i) { a[i] = -1; b[i] = 127; }
  for (unsigned j = 0; j < 4; ++j)
    for (unsigned i = 0; i < 4; ++i) seed[j][i] = i ? 0x5aa5a55a : 0x80000004u + j;
  __asm__ volatile(
    "vl1re8.v v8,(%0)\n vl1re8.v v10,(%1)\n"
    "vl1re8.v v12,(%2)\n vl1re8.v v14,(%3)\n"
    "vl1re8.v v16,(%4)\n vl1re8.v v18,(%5)\n"
    "vsetivli zero,8,e8,m1,ta,ma\n"
    : : "r"(a), "r"(b), "r"(seed[0]), "r"(seed[1]), "r"(seed[2]), "r"(seed[3])
    : "memory", "v8", "v10", "v12", "v14", "v16", "v18");
  for (unsigned i = 0; i < CHAIN_STEPS; ++i) {
    if (chains == 1) __asm__ volatile(".word 0x06a4060b" ::: "v12");
    else __asm__ volatile(
      ".word 0x06a4060b\n .word 0x06a4070b\n .word 0x06a4080b\n .word 0x06a4090b"
      ::: "v12", "v14", "v16", "v18");
  }
  __asm__ volatile(
    "vs1r.v v12,(%0)\n vs1r.v v14,(%1)\n vs1r.v v16,(%2)\n vs1r.v v18,(%3)"
    : : "r"(out[0]), "r"(out[1]), "r"(out[2]), "r"(out[3]) : "memory");
  for (unsigned j = 0; j < chains; ++j) {
    uint32_t want = seed[j][0] + (uint32_t)(CHAIN_STEPS * dot(a,b));
    if (!complete_result(out[j], want)) return 70 + j;
  }
  puts_uart("ACC_CHAIN_PASS chains="); print_uint(chains);
  puts_uart(" iterations="); print_uint(CHAIN_STEPS); putch('\n');
  return 0;
}

int main(void) {
  const int8_t limits[6][2] = {{1,1},{-1,1},{-128,-128},{-128,127},{127,127},{0,-128}};
  const uint32_t seeds[6] = {0x12345678,0xfffffff9,0x7fffffff,0x80000000,0xfffffffe,0xdeadbeef};
  int8_t a[16] __attribute__((aligned(16)));
  int8_t b[16] __attribute__((aligned(16)));
  uint32_t old[4] __attribute__((aligned(16)));
  uint32_t out[4] __attribute__((aligned(16)));
  uint32_t checksum = 0;
  for (unsigned test = 0; test < 6 + RANDOM_CASES; ++test) {
    for (unsigned i = 0; i < 16; ++i) {
      a[i] = test < 6 ? limits[test][0] : (int8_t)random_word();
      b[i] = test < 6 ? limits[test][1] : (int8_t)random_word();
    }
    old[0] = test < 6 ? seeds[test] : random_word();
    old[1] = 0x12345678; old[2] = random_word(); old[3] = random_word();
    for (unsigned policy = 0; policy < 2; ++policy)
    for (unsigned mode = 0; mode < MODES; ++mode) {
      uint32_t seed = mode == 1 || mode == 4 ? first_word(a) : mode == 2 ? first_word(b) : old[0];
      uint32_t sum = (uint32_t)dot(a, mode == 3 || mode == 4 ? a : b);
      uint32_t want = mode == 5 ? sum : seed + sum;
      calculate(a,b,old,out,mode | (policy << 8));
      if (!complete_result(out,want)) {
        puts_uart("ACC_MISMATCH test="); print_uint(test); puts_uart(" mode="); print_uint(mode);
        puts_uart(" expected="); print_uint(want); puts_uart(" actual="); print_uint(out[0]); putch('\n');
        return error(10 + mode);
      }
      checksum ^= out[0] + test * 17u + mode + policy * 0x9e3779b9u;
      if (test < 6 && mode == 0 && policy == 0) {
        puts_uart("ACC_CASE,"); print_uint(test); putch(','); print_uint(seed); putch(',');
        print_uint(want); putch(','); print_uint(out[0]); putch('\n');
      }
    }
    if (test < 6) {
      for (unsigned i = 8; i < 16; ++i) { a[i] = (int8_t)(41+i); b[i] = (int8_t)(-39-i); }
      calculate(a,b,old,out,0);
      if (!complete_result(out,old[0]+(uint32_t)dot(a,b))) return error(20);
    }
  }
  int status = accumulator_chains(1); if (status) return error(status);
  status = accumulator_chains(4); if (status) return error(status);
  status = illegal_forms(); if (status) return error(status);
  puts_uart("ACC_VALIDATION_PASS random_cases=1000 directed_cases=6 modes=6 tail_policies=2 high_source_pairs=6 chain_instructions=640 illegal_cases=7 checksum=");
  print_uint(checksum); putch('\n');
  return 0;
}
