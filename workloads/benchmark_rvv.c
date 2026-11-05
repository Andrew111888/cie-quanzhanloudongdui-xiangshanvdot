#include <stdint.h>
#include "console.h"

volatile uint32_t expected_illegal;

static inline uint64_t cycle(void) {
  uint64_t value;
  __asm__ volatile("fence rw,rw\n csrr %0,cycle" : "=r"(value) : : "memory");
  return value;
}

static void fail(unsigned code) {
  __asm__ volatile("mv a0,%0\n .word 0x0000006b" : : "r"((uintptr_t)code) : "a0", "memory");
}

static const int8_t input[16] __attribute__((aligned(16))) =
  {-128,127,-7,9,31,-32,1,5,91,-42,77,23,12,-15,84,-16};
// The recurrence starts with high 96 bits zero, as does every subsequent result.
static const int8_t dependent_input[16] __attribute__((aligned(16))) = {1,1,1,1};
static const int8_t multiplier[16] __attribute__((aligned(16))) =
  {1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1};

#define CONFIG_TA "vsetivli zero,8,e8,m1,ta,ma\n"
#define CONFIG_TU "vsetivli zero,8,e8,m1,tu,mu\n"
#define LEGACY(D,C) \
  "vwmul.vv v16,v8,v10\n" \
  "vsetivli zero,4,e32,m1,tu,mu\n vmv.v.i " D ",0\n" \
  "vsetivli zero,8,e16,m1,tu,mu\n vwredsum.vs " D ",v16,v20\n" C
#define REUSE_ZERO(D,C) \
  "vwmul.vv v16,v8,v10\n" \
  "vsetivli zero,8,e16,m1,tu,mu\n vwredsum.vs " D ",v16,v20\n" C
#define MAKE_KERNEL(NAME,DEST,CONFIG,CORE) \
static uint64_t NAME(unsigned iterations, unsigned dependent) { \
  uint32_t out[4] __attribute__((aligned(16))); \
  const int8_t *a = dependent ? dependent_input : input; \
  __asm__ volatile( \
    "vsetivli zero,4,e32,m1,tu,mu\n vmv.v.i v12,0\n vmv.v.i v20,0\n" \
    "vl1re8.v v8,(%0)\n vl1re8.v v10,(%1)\n" CONFIG \
    : : "r"(a), "r"(multiplier) : "memory","v8","v10","v12","v20"); \
  unsigned batches = iterations / 8; \
  uint64_t begin = cycle(); \
  __asm__ volatile("1:\n .rept 8\n" CORE ".endr\n" \
    "addi %0,%0,-1\n bnez %0,1b\n vs1r.v " DEST ",(%1)\n" \
    : "+r"(batches) : "r"(out) : "memory","v8","v12","v16","v17","v20"); \
  uint64_t elapsed = cycle() - begin; \
  int32_t expected = dependent ? 4 : 6; \
  if (out[0] != (uint32_t)expected || out[1] || out[2] || out[3]) fail(82); \
  return elapsed; \
}

MAKE_KERNEL(legacy_ta_independent,"v12",CONFIG_TA,LEGACY("v12",CONFIG_TA))
MAKE_KERNEL(legacy_tu_independent,"v12",CONFIG_TU,LEGACY("v12",CONFIG_TU))
MAKE_KERNEL(legacy_ta_dependent,"v8",CONFIG_TA,LEGACY("v8",CONFIG_TA))
MAKE_KERNEL(legacy_tu_dependent,"v8",CONFIG_TU,LEGACY("v8",CONFIG_TU))
MAKE_KERNEL(reuse_ta_independent,"v12",CONFIG_TA,REUSE_ZERO("v12",CONFIG_TA))
MAKE_KERNEL(reuse_tu_independent,"v12",CONFIG_TU,REUSE_ZERO("v12",CONFIG_TU))
MAKE_KERNEL(reuse_ta_dependent,"v8",CONFIG_TA,REUSE_ZERO("v8",CONFIG_TA))
MAKE_KERNEL(reuse_tu_dependent,"v8",CONFIG_TU,REUSE_ZERO("v8",CONFIG_TU))
MAKE_KERNEL(dot_ta_independent,"v12",CONFIG_TA,".word 0x02a4060b\n")
MAKE_KERNEL(dot_tu_independent,"v12",CONFIG_TU,".word 0x02a4060b\n")
MAKE_KERNEL(dot_ta_dependent,"v8",CONFIG_TA,".word 0x02a4040b\n")
MAKE_KERNEL(dot_tu_dependent,"v8",CONFIG_TU,".word 0x02a4040b\n")

typedef uint64_t (*kernel)(unsigned, unsigned);
int main(void) {
  const kernel functions[3][2][2] = {
    {{legacy_ta_independent,legacy_ta_dependent},{legacy_tu_independent,legacy_tu_dependent}},
    {{reuse_ta_independent,reuse_ta_dependent},{reuse_tu_independent,reuse_tu_dependent}},
    {{dot_ta_independent,dot_ta_dependent},{dot_tu_independent,dot_tu_dependent}},
  };
  const unsigned lengths[] = {32,128,512};
  puts_uart("RVV_HEADER,variant,tail_undisturbed,dependent,iterations,repeat,cycles\n");
  for (unsigned variant=0; variant<3; ++variant)
    for (unsigned tu=0; tu<2; ++tu)
      for (unsigned dependent=0; dependent<2; ++dependent)
        for (unsigned size=0; size<3; ++size) {
          (void)functions[variant][tu][dependent](lengths[size],dependent);
          for (unsigned repeat=0; repeat<5; ++repeat) {
            uint64_t elapsed=functions[variant][tu][dependent](lengths[size],dependent);
            puts_uart("RVV,"); print_uint(variant); putch(','); print_uint(tu); putch(',');
            print_uint(dependent); putch(','); print_uint(lengths[size]); putch(',');
            print_uint(repeat); putch(','); print_uint(elapsed); putch('\n');
          }
        }
  puts_uart("RVV_BENCH_PASS samples=180 full_destination_checked=1\n");
  return 0;
}
