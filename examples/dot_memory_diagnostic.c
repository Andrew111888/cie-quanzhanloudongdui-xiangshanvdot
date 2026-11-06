#include <stdint.h>
#include "console.h"

volatile uint32_t expected_illegal;
#ifndef DIAG_BLOCKS
#define DIAG_BLOCKS 128
#endif
#ifndef DIAG_REPEATS
#define DIAG_REPEATS 3
#endif
_Static_assert(DIAG_BLOCKS > 0 && DIAG_BLOCKS % 4 == 0, "four-way loop");
static int8_t input_a[DIAG_BLOCKS][16] __attribute__((aligned(64)));
static int8_t input_b[DIAG_BLOCKS][16] __attribute__((aligned(64)));
static uint32_t output[DIAG_BLOCKS][4] __attribute__((aligned(64)));
static int32_t golden[DIAG_BLOCKS];

static uint32_t random_word(uint32_t *state) {
  *state ^= *state << 13; *state ^= *state >> 17; *state ^= *state << 5;
  return *state;
}
static inline uint64_t cycle(void) {
  uint64_t result;
  __asm__ volatile("fence rw,rw\n csrr %0,cycle" : "=r"(result) : : "memory");
  return result;
}
static void fail(unsigned code) {
  __asm__ volatile("mv a0,%0\n .word 0x0000006b" : : "r"((uintptr_t)code) : "a0", "memory");
}
static void prepare(void) {
  uint32_t state = 20261106;
  const int edges[6][2] = {{1,1},{-1,1},{-128,-128},{-128,127},{127,127},{0,-128}};
  for (unsigned block=0; block<DIAG_BLOCKS; ++block) {
    golden[block]=0;
    for (unsigned lane=0; lane<16; ++lane) {
      input_a[block][lane]=(int8_t)random_word(&state);
      input_b[block][lane]=(int8_t)random_word(&state);
      if (block<6 && lane<8) {
        input_a[block][lane]=(int8_t)edges[block][0];
        input_b[block][lane]=(int8_t)edges[block][1];
      }
      if (lane<8) golden[block]+=(int32_t)input_a[block][lane]*input_b[block][lane];
    }
  }
}

#define TA "vsetivli zero,8,e8,m1,ta,ma\n"
#define TU "vsetivli zero,8,e8,m1,tu,mu\n"
#define FULL_STORE "vs1r.v v12,(%2)\n"
#define ACTIVE_STORE "vse8.v v12,(%2)\n"
#define STEP(A,B,DOT,STORE) \
  "vle8.v " A ",(%0)\n vle8.v " B ",(%1)\n" DOT STORE \
  "addi %0,%0,16\n addi %1,%1,16\n addi %2,%2,16\n"
#define DOT_8_10 ".word 0x02a4060b\n"
#define DOT_16_18 ".word 0x0328060b\n"
#define DOT_20_22 ".word 0x036a060b\n"
#define DOT_24_26 ".word 0x03ac060b\n"
#define FIXED(STORE) \
  STEP("v8","v10",DOT_8_10,STORE) STEP("v8","v10",DOT_8_10,STORE) \
  STEP("v8","v10",DOT_8_10,STORE) STEP("v8","v10",DOT_8_10,STORE)
#define ROTATE(STORE) \
  STEP("v8","v10",DOT_8_10,STORE) STEP("v16","v18",DOT_16_18,STORE) \
  STEP("v20","v22",DOT_20_22,STORE) STEP("v24","v26",DOT_24_26,STORE)
#define KERNEL(NAME,CONFIG,BODY) \
__attribute__((noinline)) static uint64_t NAME(uint32_t *checksum) { \
  /* Common untimed initialization makes both store sizes produce the same 128-bit memory result. */ \
  for (unsigned i=0; i<DIAG_BLOCKS; ++i) \
    for (unsigned j=0; j<4; ++j) output[i][j]=0; \
  __asm__ volatile("vsetivli zero,16,e8,m1,tu,mu\n" \
    "vmv.v.i v8,0\n vmv.v.i v10,0\n vmv.v.i v12,0\n vmv.v.i v16,0\n" \
    "vmv.v.i v18,0\n vmv.v.i v20,0\n vmv.v.i v22,0\n vmv.v.i v24,0\n vmv.v.i v26,0\n" \
    CONFIG : : : "memory","v8","v10","v12","v16","v18","v20","v22","v24","v26"); \
  const int8_t *a=&input_a[0][0], *b=&input_b[0][0]; \
  uint32_t *destination=&output[0][0]; unsigned remaining=DIAG_BLOCKS; \
  uint64_t begin=cycle(); \
  __asm__ volatile("1:\n" BODY "addi %3,%3,-4\n bnez %3,1b\n" \
    : "+r"(a),"+r"(b),"+r"(destination),"+r"(remaining) : \
    : "memory","v8","v10","v12","v16","v18","v20","v22","v24","v26"); \
  uint64_t elapsed=cycle()-begin; uint32_t digest=2166136261u; \
  for (unsigned i=0; i<DIAG_BLOCKS; ++i) { \
    if (output[i][0]!=(uint32_t)golden[i] || output[i][1] || output[i][2] || output[i][3]) fail(93); \
    digest=(digest ^ output[i][0])*16777619u; \
  } \
  *checksum=digest; return elapsed; \
}
KERNEL(fixed_ta_16,TA,FIXED(FULL_STORE))
KERNEL(fixed_tu_16,TU,FIXED(FULL_STORE))
KERNEL(rotate_ta_16,TA,ROTATE(FULL_STORE))
KERNEL(rotate_tu_16,TU,ROTATE(FULL_STORE))
KERNEL(fixed_ta_8,TA,FIXED(ACTIVE_STORE))
KERNEL(fixed_tu_8,TU,FIXED(ACTIVE_STORE))
KERNEL(rotate_ta_8,TA,ROTATE(ACTIVE_STORE))
KERNEL(rotate_tu_8,TU,ROTATE(ACTIVE_STORE))

int main(void) {
  prepare();
  typedef uint64_t (*kernel)(uint32_t*);
  const kernel functions[2][2][2] = {
    {{fixed_ta_16,fixed_tu_16},{rotate_ta_16,rotate_tu_16}},
    {{fixed_ta_8,fixed_tu_8},{rotate_ta_8,rotate_tu_8}}
  };
  puts_uart("MEMDIAG_HEADER,tail_undisturbed,rotating,store_bytes,blocks,repeat,cycles,checksum\n");
  uint32_t expected_checksum=0;
  for (unsigned small=0; small<2; ++small)
    for (unsigned rotating=0; rotating<2; ++rotating)
      for (unsigned tu=0; tu<2; ++tu) {
        uint32_t checksum;
        (void)functions[small][rotating][tu](&checksum);
        if (!small && !rotating && !tu) expected_checksum=checksum;
        if (checksum!=expected_checksum) fail(94);
        for (unsigned repeat=0; repeat<DIAG_REPEATS; ++repeat) {
          uint64_t elapsed=functions[small][rotating][tu](&checksum);
          if (checksum!=expected_checksum) fail(95);
          puts_uart("MEMDIAG,"); print_uint(tu); putch(','); print_uint(rotating); putch(',');
          print_uint(small?8:16); putch(','); print_uint(DIAG_BLOCKS); putch(',');
          print_uint(repeat); putch(','); print_uint(elapsed); putch(','); print_uint(checksum); putch('\n');
        }
      }
  puts_uart("MEMORY_DIAGNOSTIC_PASS samples="); print_uint(8*DIAG_REPEATS);
  puts_uart(" blocks="); print_uint(DIAG_BLOCKS);
  puts_uart(" all_128bit_memory_results_checked=1\n");
  return 0;
}
