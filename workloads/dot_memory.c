#include <stdint.h>
#include "console.h"

volatile uint32_t expected_illegal;
enum { MAX_BLOCKS=512 };
static int8_t input_a[MAX_BLOCKS][16] __attribute__((aligned(64)));
static int8_t input_b[MAX_BLOCKS][16] __attribute__((aligned(64)));
static uint32_t output[MAX_BLOCKS][4] __attribute__((aligned(64)));
static int32_t golden[MAX_BLOCKS];

static inline uint64_t cycle(void) {
  uint64_t value;
  __asm__ volatile("fence rw,rw\n csrr %0,cycle" : "=r"(value) : : "memory");
  return value;
}

static void fail(unsigned code) {
  __asm__ volatile("mv a0,%0\n .word 0x0000006b" : : "r"((uintptr_t)code) : "a0", "memory");
}

static uint32_t random_word(uint32_t *state) {
  *state ^= *state << 13;
  *state ^= *state >> 17;
  *state ^= *state << 5;
  return *state;
}

static void prepare(void) {
  uint32_t state=20261105;
  const int values[6][2]={{1,1},{-1,1},{-128,-128},{-128,127},{127,127},{0,-128}};
  for (unsigned block=0; block<MAX_BLOCKS; ++block) {
    golden[block]=0;
    for (unsigned lane=0; lane<16; ++lane) {
      input_a[block][lane]=(int8_t)random_word(&state);
      input_b[block][lane]=(int8_t)random_word(&state);
      if (block<6 && lane<8) {
        input_a[block][lane]=(int8_t)values[block][0];
        input_b[block][lane]=(int8_t)values[block][1];
      }
      if (lane<8)
        golden[block]+=(int32_t)input_a[block][lane]*(int32_t)input_b[block][lane];
    }
  }
}

#define CONFIG_TA "vsetivli zero,8,e8,m1,ta,ma\n"
#define CONFIG_TU "vsetivli zero,8,e8,m1,tu,mu\n"
#define LOAD_INPUTS "vle8.v v8,(%0)\n vle8.v v10,(%1)\n"
#define LEGACY(C) \
  "vwmul.vv v16,v8,v10\n" \
  "vsetivli zero,4,e32,m1,tu,mu\n vmv.v.i v12,0\n" \
  "vsetivli zero,8,e16,m1,tu,mu\n vwredsum.vs v12,v16,v20\n" C
#define REUSE_ZERO(C) \
  "vwmul.vv v16,v8,v10\n" \
  "vsetivli zero,8,e16,m1,tu,mu\n vwredsum.vs v12,v16,v20\n" C
#define MAKE_KERNEL(NAME,CONFIG,CORE) \
static uint64_t NAME(unsigned blocks, uint32_t *checksum) { \
  for (unsigned i=0; i<blocks; ++i) \
    for (unsigned j=0; j<4; ++j) output[i][j]=0x5aa5a55a; \
  __asm__ volatile("vsetivli zero,4,e32,m1,tu,mu\n vmv.v.i v12,0\n vmv.v.i v20,0\n" CONFIG \
    ::: "memory","v12","v20"); \
  const int8_t *a=&input_a[0][0], *b=&input_b[0][0]; \
  uint32_t *destination=&output[0][0]; unsigned remaining=blocks; \
  uint64_t begin=cycle(); \
  __asm__ volatile("1:\n" LOAD_INPUTS CORE \
    "vs1r.v v12,(%2)\n addi %0,%0,16\n addi %1,%1,16\n addi %2,%2,16\n" \
    "addi %3,%3,-1\n bnez %3,1b\n" \
    : "+r"(a),"+r"(b),"+r"(destination),"+r"(remaining) : \
    : "memory","v8","v10","v12","v16","v17","v20"); \
  uint64_t elapsed=cycle()-begin; \
  uint32_t digest=2166136261u; \
  for (unsigned i=0; i<blocks; ++i) { \
    if (output[i][0]!=(uint32_t)golden[i] || output[i][1] || output[i][2] || output[i][3]) fail(83); \
    digest=(digest ^ output[i][0])*16777619u; \
  } \
  *checksum=digest; return elapsed; \
}

MAKE_KERNEL(legacy_ta,CONFIG_TA,LEGACY(CONFIG_TA))
MAKE_KERNEL(legacy_tu,CONFIG_TU,LEGACY(CONFIG_TU))
MAKE_KERNEL(reuse_ta,CONFIG_TA,REUSE_ZERO(CONFIG_TA))
MAKE_KERNEL(reuse_tu,CONFIG_TU,REUSE_ZERO(CONFIG_TU))
MAKE_KERNEL(dot_ta,CONFIG_TA,".word 0x02a4060b\n")
MAKE_KERNEL(dot_tu,CONFIG_TU,".word 0x02a4060b\n")

typedef uint64_t (*kernel)(unsigned,uint32_t*);
int main(void) {
  prepare();
  const kernel functions[3][2]={{legacy_ta,legacy_tu},{reuse_ta,reuse_tu},{dot_ta,dot_tu}};
  const unsigned lengths[]={32,128,512};
  puts_uart("MEMORY_HEADER,variant,tail_undisturbed,blocks,repeat,cycles,checksum\n");
  for (unsigned variant=0; variant<3; ++variant)
    for (unsigned tu=0; tu<2; ++tu)
      for (unsigned size=0; size<3; ++size) {
        uint32_t checksum;
        (void)functions[variant][tu](lengths[size],&checksum);
        for (unsigned repeat=0; repeat<5; ++repeat) {
          uint64_t elapsed=functions[variant][tu](lengths[size],&checksum);
          puts_uart("MEMORY,"); print_uint(variant); putch(','); print_uint(tu); putch(',');
          print_uint(lengths[size]); putch(','); print_uint(repeat); putch(',');
          print_uint(elapsed); putch(','); print_uint(checksum); putch('\n');
        }
      }
  puts_uart("MEMORY_DOT_PASS samples=90 all_blocks_and_128bit_results_checked=1\n");
  return 0;
}
