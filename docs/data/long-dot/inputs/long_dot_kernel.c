#include <stdint.h>
#include "console.h"

volatile uint32_t expected_illegal;
enum { MAX_K=512, VARIANTS=3, SIZES=3, REPEATS=5 };
static int8_t input_a[MAX_K] __attribute__((aligned(64)));
static int8_t input_b[MAX_K] __attribute__((aligned(64)));
static volatile uint32_t output[4] __attribute__((aligned(64)));
static uint64_t samples[VARIANTS][SIZES][REPEATS];
static int32_t results[VARIANTS][SIZES];
static volatile int32_t expected_result;
static int32_t directed[2][6][VARIANTS];

static inline uint64_t cycle(void) {
  uint64_t result;
  __asm__ volatile("fence rw,rw\n csrr %0,cycle" : "=r"(result) : : "memory");
  return result;
}
static void fail(unsigned code) {
  __asm__ volatile("mv a0,%0\n .word 0x0000006b" : : "r"((uintptr_t)code) : "a0", "memory");
}
static uint32_t random_word(uint32_t *state) {
  *state ^= *state << 13; *state ^= *state >> 17; *state ^= *state << 5;
  return *state;
}
static int32_t golden(unsigned k) {
  int64_t result=0;
  for (unsigned i=0;i<k;++i) result+=(int32_t)input_a[i]*(int32_t)input_b[i];
  return (int32_t)result;
}
static void print_signed(int32_t value) {
  if (value<0) { putch('-'); print_uint((uint32_t)(-(int64_t)value)); }
  else print_uint((uint32_t)value);
}

#define E8_8 "vsetivli zero,8,e8,m1,ta,ma\n"
#define E8_16 "vsetivli zero,16,e8,m1,ta,ma\n"
#define E16_8 "vsetivli zero,8,e16,m1,tu,mu\n"
#define E16_16 "vsetivli zero,16,e16,m2,tu,mu\n"
#define E32_4 "vsetivli zero,4,e32,m1,tu,mu\n"
#define E32_16 "vsetivli zero,16,e32,m4,tu,mu\n"
#define FOUR_ACC_INIT \
  E32_4 "vmv.v.i v24,0\n vmv.v.i v25,0\n vmv.v.i v26,0\n vmv.v.i v27,0\n" E8_8
#define FOUR_ACC_FINISH \
  E32_4 "vadd.vv v24,v24,v25\n vadd.vv v26,v26,v27\n vadd.vv v24,v24,v26\n" \
  "vs1r.v v24,(%3)\n"
#define LOAD8(A,B,OP) \
  "vle8.v " A ",(%0)\n vle8.v " B ",(%1)\n" OP \
  "addi %0,%0,8\n addi %1,%1,8\n"
#define LOAD16(A,B,OP) \
  "vle8.v " A ",(%0)\n vle8.v " B ",(%1)\n" OP \
  "addi %0,%0,16\n addi %1,%1,16\n"
#define DOT_BODY \
  LOAD8("v0","v1",".word 0x0210040b\n") \
  LOAD8("v2","v3",".word 0x0231048b\n") \
  LOAD8("v4","v5",".word 0x0252050b\n") \
  LOAD8("v6","v7",".word 0x0273058b\n") \
  E32_4 "vadd.vv v24,v24,v8\n vadd.vv v25,v25,v9\n" \
  "vadd.vv v26,v26,v10\n vadd.vv v27,v27,v11\n" E8_8
#define REDUCE_BODY \
  LOAD8("v0","v1","vwmul.vv v8,v0,v1\n") \
  LOAD8("v2","v3","vwmul.vv v10,v2,v3\n") \
  LOAD8("v4","v5","vwmul.vv v12,v4,v5\n") \
  LOAD8("v6","v7","vwmul.vv v14,v6,v7\n") \
  E16_8 "vwredsum.vs v24,v8,v24\n vwredsum.vs v25,v10,v25\n" \
  "vwredsum.vs v26,v12,v26\n vwredsum.vs v27,v14,v27\n" E8_8
#define LANE_INIT \
  E32_16 "vmv.v.i v16,0\n vmv.v.i v20,0\n vmv.v.i v24,0\n vmv.v.i v28,0\n" E8_16
#define LANE_BODY \
  LOAD16("v0","v1","vwmul.vv v8,v0,v1\n") \
  LOAD16("v2","v3","vwmul.vv v12,v2,v3\n") \
  E16_16 "vwadd.wv v16,v16,v8\n vwadd.wv v20,v20,v12\n" E8_16
#define LANE_FINISH \
  E32_16 "vadd.vv v16,v16,v20\n vredsum.vs v24,v16,v28\n vs1r.v v24,(%3)\n"
#define ALL_VECTOR_REGS \
  "v0","v1","v2","v3","v4","v5","v6","v7","v8","v9","v10","v11", \
  "v12","v13","v14","v15","v16","v17","v18","v19","v20","v21","v22","v23", \
  "v24","v25","v26","v27","v28","v29","v30","v31"
#define KERNEL(NAME,INIT,BODY,FINISH) \
__attribute__((noinline)) static uint64_t NAME(unsigned k) { \
  for (unsigned i=0;i<4;++i) output[i]=0x5aa5a55a; \
  const int8_t *a=input_a,*b=input_b;unsigned remaining=k; \
  uint64_t begin=cycle(); \
  __asm__ volatile(INIT "1:\n" BODY "addi %2,%2,-32\n bnez %2,1b\n" FINISH \
    : "+&r"(a),"+&r"(b),"+&r"(remaining) : "r"(output) : "memory",ALL_VECTOR_REGS); \
  uint64_t elapsed=cycle()-begin; \
  if (output[0]!=(uint32_t)expected_result || output[1] || output[2] || output[3]) fail(96); \
  return elapsed; \
}
KERNEL(dot_four,FOUR_ACC_INIT,DOT_BODY,FOUR_ACC_FINISH)
KERNEL(rvv_reduce_four,FOUR_ACC_INIT,REDUCE_BODY,FOUR_ACC_FINISH)
KERNEL(rvv_lane_sixteen,LANE_INIT,LANE_BODY,LANE_FINISH)

int main(void) {
  typedef uint64_t (*kernel)(unsigned);
  const kernel functions[VARIANTS]={dot_four,rvv_reduce_four,rvv_lane_sixteen};
  const unsigned sizes[SIZES]={32,128,512};
  const unsigned directed_sizes[2]={32,512};
  const int edges[6][2]={{1,1},{-1,1},{-128,-128},{-128,127},{127,127},{0,-128}};
  for (unsigned size=0;size<2;++size)
    for (unsigned test=0;test<6;++test) {
      unsigned k=directed_sizes[size];
      for (unsigned i=0;i<k;++i) { input_a[i]=(int8_t)edges[test][0]; input_b[i]=(int8_t)edges[test][1]; }
      expected_result=(int32_t)((int64_t)k*edges[test][0]*edges[test][1]);
      for (unsigned variant=0;variant<VARIANTS;++variant) {
        (void)functions[variant](k);
        directed[size][test][variant]=(int32_t)output[0];
      }
    }
  uint32_t state=20261106;
  for (unsigned i=0;i<MAX_K;++i) { input_a[i]=(int8_t)random_word(&state); input_b[i]=(int8_t)random_word(&state); }
  for (unsigned variant=0;variant<VARIANTS;++variant)
    for (unsigned size=0;size<SIZES;++size) {
      expected_result=golden(sizes[size]);
      (void)functions[variant](sizes[size]);
      for (unsigned repeat=0;repeat<REPEATS;++repeat) samples[variant][size][repeat]=functions[variant](sizes[size]);
      results[variant][size]=(int32_t)output[0];
    }
  puts_uart("LONG_DOT_DIRECTED_PASS cases=12 lengths=2 variants=3\n");
  puts_uart("LONG_DIR_HEADER,k,case,expected,actual0,actual1,actual2\n");
  for (unsigned size=0;size<2;++size)
    for (unsigned test=2;test<=3;++test) {
      unsigned k=directed_sizes[size];
      puts_uart("LONG_DIR,");print_uint(k);putch(',');print_uint(test);putch(',');
      print_signed((int32_t)((int64_t)k*edges[test][0]*edges[test][1]));
      for (unsigned variant=0;variant<VARIANTS;++variant) { putch(',');print_signed(directed[size][test][variant]); }
      putch('\n');
    }
  puts_uart("LONG_DOT_HEADER,variant,k,c0,c1,c2,c3,c4,result\n");
  for (unsigned variant=0;variant<VARIANTS;++variant)
    for (unsigned size=0;size<SIZES;++size) {
      puts_uart("LONG_DOT,");print_uint(variant);putch(',');print_uint(sizes[size]);
      for (unsigned repeat=0;repeat<REPEATS;++repeat) { putch(',');print_uint(samples[variant][size][repeat]); }
      putch(',');print_signed(results[variant][size]);putch('\n');
    }
  puts_uart("LONG_DOT_PASS samples=45 lengths=3 full_128bit_final_results_checked=1\n");
  return 0;
}
