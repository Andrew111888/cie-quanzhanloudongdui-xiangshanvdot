#include <stdint.h>
#include "console.h"

/* Probe the existing decoder's early illegal-instruction checks before the
 * custom execution-unit configuration checks. No legal operation is executed. */
volatile uint32_t expected_illegal;
static unsigned cases, failures;
static uint32_t checksum;
#define STR1(x) #x
#define STR(x) STR1(x)
#define WORD(op,vm,d,a,b) (((op) << 26) | ((vm) << 25) | ((b) << 20) | ((a) << 15) | ((d) << 7) | 0x0b)
#define M1 "vsetivli zero,8,e8,m1,tu,mu\n"
#define M2 "vsetivli zero,8,e8,m2,tu,mu\n"
#define M4 "vsetivli zero,8,e8,m4,tu,mu\n"
#define M8 "vsetivli zero,8,e8,m8,tu,mu\n"
#define VILL "li t0,8\n li t1,256\n vsetvl zero,t0,t1\n"
#define PROBE(op,cfg,vm,d,a,b,start,early) do { \
  const uint32_t before[4] __attribute__((aligned(16))) = {0x89abcdef,0x12345678,0x76543210,0xfedcba98}; \
  uint32_t after[4] __attribute__((aligned(16))); \
  uintptr_t actual_start, actual_tval; \
  __asm__ volatile("csrwi vstart,0\n" M1 \
    "vl1re32.v v0,(%0)\n vl1re32.v v24,(%0)\n vl1re32.v v25,(%0)\n" \
    : : "r"(before) : "memory","v0","v24","v25"); \
  expected_illegal=1; \
  __asm__ volatile(cfg "csrwi vstart," STR(start) "\n fence rw,rw\n" \
    ".word " STR(WORD(op,vm,d,a,b)) "\n" \
    "csrr %0,vstart\n csrr %1,mtval\n csrwi vstart,0\n" M1 \
    "vs1r.v v" STR(d) ",(%2)\n" \
    : "=&r"(actual_start),"=&r"(actual_tval) : "r"(after) \
    : "t0","t1","memory","v0","v24","v25"); \
  uint32_t instruction=WORD(op,vm,d,a,b); \
  uintptr_t want_tval=(early)?instruction:0; \
  unsigned bad=expected_illegal || actual_start!=(start) || actual_tval!=want_tval; \
  for(unsigned i=0;i<4;++i) bad |= after[i]!=before[i]; \
  ++cases; failures += !!bad; checksum ^= instruction + (uint32_t)actual_tval + (uint32_t)actual_start; \
  if (bad) { puts_uart("PRECEDENCE_CASE,");print_uint(cases);putch(',');print_uint(instruction); \
  putch(',');print_uint(want_tval);putch(',');print_uint(actual_tval); \
  putch(',');print_uint(actual_start);putch(',');print_uint(!!bad);putch('\n'); } \
} while(0)
#define ALL_FOR_OPERATION(op) do { \
  PROBE(op,M2,1,24,9,16,0,1); \
  PROBE(op,M2,1,24,8,17,0,1); \
  PROBE(op,M2,1,25,8,16,0,1); \
  PROBE(op,M4,1,24,9,16,0,1); \
  PROBE(op,M4,1,24,8,17,0,1); \
  PROBE(op,M4,1,25,8,16,0,1); \
  PROBE(op,M8,1,24,9,16,0,1); \
  PROBE(op,M8,1,24,8,17,0,1); \
  PROBE(op,M8,1,25,8,16,0,1); \
  PROBE(op,M2,1,24,8,16,0,0); \
  PROBE(op,M4,1,24,8,16,0,0); \
  PROBE(op,M8,1,24,8,16,0,0); \
  PROBE(op,M1,0,0,8,16,0,1); \
  PROBE(op,M1,0,24,8,16,0,0); \
  PROBE(op,VILL,1,24,8,16,0,1); \
  PROBE(op,M1,1,24,8,16,1,1); \
  PROBE(op,"vsetivli zero,8,e16,m1,tu,mu\n",1,24,8,16,1,1); \
  PROBE(op,M2,1,24,8,16,1,1); \
  PROBE(op,M2,0,0,9,17,1,1); \
  PROBE(op,"vsetivli zero,8,e8,mf2,tu,mu\n",1,24,8,16,0,0); \
  PROBE(op,"vsetivli zero,8,e8,mf4,tu,mu\n",1,24,8,16,0,0); \
  PROBE(op,"vsetivli zero,8,e8,mf8,tu,mu\n",1,24,8,16,0,0); \
  PROBE(op,"vsetivli zero,8,e16,mf8,tu,mu\n",1,24,8,16,0,1); \
  PROBE(op,"vsetivli zero,8,e64,mf2,tu,mu\n",1,24,8,16,0,1); \
} while(0)
int main(void) {
  ALL_FOR_OPERATION(0);
  ALL_FOR_OPERATION(1);
  puts_uart(failures ? "ACC_PRECEDENCE_FAIL cases=" : "ACC_PRECEDENCE_PASS cases=");
  print_uint(cases);puts_uart(" failures=");print_uint(failures);
  puts_uart(" checksum=");print_uint(checksum);putch('\n');
  return failures ? 91 : 0;
}
