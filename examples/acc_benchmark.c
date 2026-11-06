#include <stdint.h>
#include "console.h"

volatile uint32_t expected_illegal;
#ifndef ACC_BENCH_SHARD
#define ACC_BENCH_SHARD 0
#endif
#ifndef ACC_BENCH_SHARDS
#define ACC_BENCH_SHARDS 1
#endif
#define SELECT_GROUP(x) ((x) % ACC_BENCH_SHARDS == ACC_BENCH_SHARD)
enum { MAX_K=512, LONG_VARIANTS=4, CHAIN_VARIANTS=2, SIZES=3,
       CHAIN_COUNTS=4, REPEATS=5, MAX_CHAINS=8 };
static int8_t input_a[MAX_K] __attribute__((aligned(64)));
static int8_t input_b[MAX_K] __attribute__((aligned(64)));
static volatile uint32_t output[4] __attribute__((aligned(64)));
static uint64_t long_samples[LONG_VARIANTS][SIZES][REPEATS];
static int32_t long_results[LONG_VARIANTS][SIZES];
static int32_t long_directed[2][6][LONG_VARIANTS];
static volatile int32_t expected_result;
static uint32_t chain_initial[MAX_CHAINS][4] __attribute__((aligned(64)));
static volatile uint32_t chain_output[MAX_CHAINS][4] __attribute__((aligned(64)));
static uint64_t chain_samples[CHAIN_VARIANTS][CHAIN_COUNTS][SIZES][REPEATS];
static uint32_t chain_results[CHAIN_VARIANTS][CHAIN_COUNTS][SIZES][MAX_CHAINS][4];
static uint32_t chain_directed[6][CHAIN_VARIANTS][CHAIN_COUNTS];
static volatile uint32_t chain_dot;
static volatile uint32_t chain_seed;

static inline uint64_t cycle(void) {
  uint64_t result;
  __asm__ volatile("fence rw,rw\n csrr %0,cycle" : "=r"(result) : : "memory");
  return result;
}
static void fail(unsigned code) {
  __asm__ volatile("mv a0,%0\n .word 0x0000006b" : : "r"((uintptr_t)code) : "a0", "memory");
}
static uint32_t random_word(uint32_t *state) {
  *state^=*state<<13; *state^=*state>>17; *state^=*state<<5;
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
/* funct6=1, vm=1; rd is the same accumulator read and overwritten. */
#define ACC_BODY \
  LOAD8("v0","v1",".word 0x06100c0b\n") \
  LOAD8("v2","v3",".word 0x06310c8b\n") \
  LOAD8("v4","v5",".word 0x06520d0b\n") \
  LOAD8("v6","v7",".word 0x06730d8b\n")
#define ALL_VECTOR_REGS \
  "v0","v1","v2","v3","v4","v5","v6","v7","v8","v9","v10","v11", \
  "v12","v13","v14","v15","v16","v17","v18","v19","v20","v21","v22","v23", \
  "v24","v25","v26","v27","v28","v29","v30","v31"
#define LONG_KERNEL(NAME,INIT,BODY,FINISH) \
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
LONG_KERNEL(dot_four,FOUR_ACC_INIT,DOT_BODY,FOUR_ACC_FINISH)
LONG_KERNEL(rvv_reduce_four,FOUR_ACC_INIT,REDUCE_BODY,FOUR_ACC_FINISH)
LONG_KERNEL(rvv_lane_sixteen,LANE_INIT,LANE_BODY,LANE_FINISH)
LONG_KERNEL(acc_four,FOUR_ACC_INIT,ACC_BODY,FOUR_ACC_FINISH)

/* The following register-loop probes preload all inputs and accumulator seeds.
 * Time includes the loop, required per-iteration configurations and final stores;
 * it is not a measurement of bare FU latency. */
#define CHAIN_PRELOAD \
  E8_8 "vle8.v v0,(%0)\n vle8.v v1,(%1)\n" \
  "vl1re32.v v16,(%2)\n addi t0,%2,16\n vl1re32.v v17,(t0)\n" \
  "addi t0,t0,16\n vl1re32.v v18,(t0)\n addi t0,t0,16\n vl1re32.v v19,(t0)\n" \
  "addi t0,t0,16\n vl1re32.v v20,(t0)\n addi t0,t0,16\n vl1re32.v v21,(t0)\n" \
  "addi t0,t0,16\n vl1re32.v v22,(t0)\n addi t0,t0,16\n vl1re32.v v23,(t0)\n"
#define DOTS_1 ".word 0x02100c0b\n"
#define DOTS_2 DOTS_1 ".word 0x02100c8b\n"
#define DOTS_4 DOTS_2 ".word 0x02100d0b\n .word 0x02100d8b\n"
#define DOTS_8 DOTS_4 ".word 0x02100e0b\n .word 0x02100e8b\n .word 0x02100f0b\n .word 0x02100f8b\n"
#define ADDS_1 "vadd.vv v16,v16,v24\n"
#define ADDS_2 ADDS_1 "vadd.vv v17,v17,v25\n"
#define ADDS_4 ADDS_2 "vadd.vv v18,v18,v26\n vadd.vv v19,v19,v27\n"
#define ADDS_8 ADDS_4 "vadd.vv v20,v20,v28\n vadd.vv v21,v21,v29\n vadd.vv v22,v22,v30\n vadd.vv v23,v23,v31\n"
#define ACCS_1 ".word 0x0610080b\n"
#define ACCS_2 ACCS_1 ".word 0x0610088b\n"
#define ACCS_4 ACCS_2 ".word 0x0610090b\n .word 0x0610098b\n"
#define ACCS_8 ACCS_4 ".word 0x06100a0b\n .word 0x06100a8b\n .word 0x06100b0b\n .word 0x06100b8b\n"
#define STORES_1 "vs1r.v v16,(%1)\n"
#define STORES_2 STORES_1 "addi t0,%1,16\n vs1r.v v17,(t0)\n"
#define STORES_4 STORES_2 "addi t0,t0,16\n vs1r.v v18,(t0)\n addi t0,t0,16\n vs1r.v v19,(t0)\n"
#define STORES_8 STORES_4 "addi t0,t0,16\n vs1r.v v20,(t0)\n addi t0,t0,16\n vs1r.v v21,(t0)\n addi t0,t0,16\n vs1r.v v22,(t0)\n addi t0,t0,16\n vs1r.v v23,(t0)\n"
#define CHAIN_KERNEL(NAME,N,BODY,STORES) \
__attribute__((noinline)) static uint64_t NAME(unsigned iterations) { \
  for (unsigned i=0;i<MAX_CHAINS;++i) { \
    chain_initial[i][0]=chain_seed+i*0x10203u; \
    for (unsigned j=1;j<4;++j) chain_initial[i][j]=0; \
    for (unsigned j=0;j<4;++j) chain_output[i][j]=0x5aa5a55a; \
  } \
  __asm__ volatile(CHAIN_PRELOAD : : "r"(input_a),"r"(input_b),"r"(chain_initial) \
                   : "t0","memory",ALL_VECTOR_REGS); \
  unsigned remaining=iterations; \
  uint64_t begin=cycle(); \
  __asm__ volatile("1:\n" BODY "addi %0,%0,-1\n bnez %0,1b\n" STORES \
                   : "+&r"(remaining) : "r"(chain_output) : "t0","memory",ALL_VECTOR_REGS); \
  uint64_t elapsed=cycle()-begin; \
  for (unsigned i=0;i<N;++i) { \
    uint32_t want=chain_initial[i][0]+iterations*chain_dot; \
    if (chain_output[i][0]!=want || chain_output[i][1] || chain_output[i][2] || chain_output[i][3]) fail(97); \
  } \
  for (unsigned i=N;i<MAX_CHAINS;++i) \
    for (unsigned j=0;j<4;++j) if (chain_output[i][j]!=0x5aa5a55a) fail(98); \
  return elapsed; \
}
CHAIN_KERNEL(dot_add_1,1,DOTS_1 E32_4 ADDS_1 E8_8,STORES_1)
CHAIN_KERNEL(dot_add_2,2,DOTS_2 E32_4 ADDS_2 E8_8,STORES_2)
CHAIN_KERNEL(dot_add_4,4,DOTS_4 E32_4 ADDS_4 E8_8,STORES_4)
CHAIN_KERNEL(dot_add_8,8,DOTS_8 E32_4 ADDS_8 E8_8,STORES_8)
CHAIN_KERNEL(acc_chain_1,1,ACCS_1,STORES_1)
CHAIN_KERNEL(acc_chain_2,2,ACCS_2,STORES_2)
CHAIN_KERNEL(acc_chain_4,4,ACCS_4,STORES_4)
CHAIN_KERNEL(acc_chain_8,8,ACCS_8,STORES_8)

static uint32_t output_checksum(unsigned chains) {
  uint32_t result=0;
  for (unsigned i=0;i<chains;++i) result^=chain_output[i][0];
  return result;
}

int main(void) {
  typedef uint64_t (*kernel)(unsigned);
  const kernel long_functions[LONG_VARIANTS]={dot_four,rvv_reduce_four,rvv_lane_sixteen,acc_four};
  const kernel chain_functions[CHAIN_VARIANTS][CHAIN_COUNTS]={
    {dot_add_1,dot_add_2,dot_add_4,dot_add_8},
    {acc_chain_1,acc_chain_2,acc_chain_4,acc_chain_8}};
  const unsigned sizes[SIZES]={32,128,512};
  const unsigned counts[CHAIN_COUNTS]={1,2,4,8};
  const unsigned directed_sizes[2]={32,512};
  const int edges[6][2]={{1,1},{-1,1},{-128,-128},{-128,127},{127,127},{0,-128}};
  unsigned long_count=0,chain_count=0;
  if (ACC_BENCH_SHARD==0) {
  for (unsigned size=0;size<2;++size)
    for (unsigned test=0;test<6;++test) {
      unsigned k=directed_sizes[size];
      for (unsigned i=0;i<k;++i) { input_a[i]=(int8_t)edges[test][0]; input_b[i]=(int8_t)edges[test][1]; }
      expected_result=(int32_t)((int64_t)k*edges[test][0]*edges[test][1]);
      for (unsigned variant=0;variant<LONG_VARIANTS;++variant) {
        (void)long_functions[variant](k);
        long_directed[size][test][variant]=(int32_t)output[0];
      }
    }
  for (unsigned test=0;test<6;++test) {
    for (unsigned i=0;i<8;++i) { input_a[i]=(int8_t)edges[test][0]; input_b[i]=(int8_t)edges[test][1]; }
    chain_dot=(uint32_t)golden(8);
    chain_seed=(edges[test][0]*edges[test][1]<0)?0x80000000u:0x7ffffff0u;
    for (unsigned variant=0;variant<CHAIN_VARIANTS;++variant)
      for (unsigned count=0;count<CHAIN_COUNTS;++count) {
        (void)chain_functions[variant][count](32);
        chain_directed[test][variant][count]=output_checksum(counts[count]);
      }
  }
  }
  uint32_t state=20261106;
  for (unsigned i=0;i<MAX_K;++i) { input_a[i]=(int8_t)random_word(&state); input_b[i]=(int8_t)random_word(&state); }
  for (unsigned variant=0;variant<LONG_VARIANTS;++variant)
    for (unsigned size=0;size<SIZES;++size) {
      if (!SELECT_GROUP(variant*SIZES+size)) continue;
      expected_result=golden(sizes[size]);
      (void)long_functions[variant](sizes[size]);
      for (unsigned repeat=0;repeat<REPEATS;++repeat) long_samples[variant][size][repeat]=long_functions[variant](sizes[size]);
      long_results[variant][size]=(int32_t)output[0];
      long_count+=REPEATS;
    }
  chain_seed=0x7ffffff0u;chain_dot=(uint32_t)golden(8);
  for (unsigned variant=0;variant<CHAIN_VARIANTS;++variant)
    for (unsigned count=0;count<CHAIN_COUNTS;++count)
      for (unsigned size=0;size<SIZES;++size) {
        if (!SELECT_GROUP(12+variant*CHAIN_COUNTS*SIZES+count*SIZES+size)) continue;
        (void)chain_functions[variant][count](sizes[size]);
        for (unsigned repeat=0;repeat<REPEATS;++repeat)
          chain_samples[variant][count][size][repeat]=chain_functions[variant][count](sizes[size]);
        for (unsigned i=0;i<counts[count];++i)
          for (unsigned j=0;j<4;++j) chain_results[variant][count][size][i][j]=chain_output[i][j];
        chain_count+=REPEATS;
      }
  if (ACC_BENCH_SHARD==0) {
  puts_uart("ACC_LONG_DIRECTED_PASS cases=12 variants=4 executions=48\n");
  for (unsigned size=0;size<2;++size)
    for (unsigned test=0;test<6;++test) {
      unsigned k=directed_sizes[size];
      puts_uart("ACC_LONG_DIR,");print_uint(k);putch(',');print_uint(test);putch(',');
      print_signed((int32_t)((int64_t)k*edges[test][0]*edges[test][1]));
      for (unsigned variant=0;variant<LONG_VARIANTS;++variant) { putch(',');print_signed(long_directed[size][test][variant]); }
      putch('\n');
    }
  puts_uart("ACC_CHAIN_DIRECTED_PASS cases=6 chain_counts=4 variants=2 executions=48\n");
  for (unsigned test=0;test<6;++test)
    for (unsigned variant=0;variant<CHAIN_VARIANTS;++variant)
      for (unsigned count=0;count<CHAIN_COUNTS;++count) {
        puts_uart("ACC_CHAIN_DIR,");print_uint(test);putch(',');print_uint(variant);putch(',');
        print_uint(counts[count]);putch(',');print_uint(chain_directed[test][variant][count]);putch('\n');
      }
  }
  puts_uart("ACC_LONG_HEADER,variant,k,c0,c1,c2,c3,c4,result\n");
  for (unsigned variant=0;variant<LONG_VARIANTS;++variant)
    for (unsigned size=0;size<SIZES;++size) {
      if (!SELECT_GROUP(variant*SIZES+size)) continue;
      puts_uart("ACC_LONG,");print_uint(variant);putch(',');print_uint(sizes[size]);
      for (unsigned repeat=0;repeat<REPEATS;++repeat) { putch(',');print_uint(long_samples[variant][size][repeat]); }
      putch(',');print_signed(long_results[variant][size]);putch('\n');
    }
  puts_uart("ACC_CHAIN_HEADER,variant,chains,rounds,c0,c1,c2,c3,c4\n");
  for (unsigned variant=0;variant<CHAIN_VARIANTS;++variant)
    for (unsigned count=0;count<CHAIN_COUNTS;++count)
      for (unsigned size=0;size<SIZES;++size) {
        if (!SELECT_GROUP(12+variant*CHAIN_COUNTS*SIZES+count*SIZES+size)) continue;
        puts_uart("ACC_CHAIN,");print_uint(variant);putch(',');print_uint(counts[count]);putch(',');print_uint(sizes[size]);
        for (unsigned repeat=0;repeat<REPEATS;++repeat) { putch(',');print_uint(chain_samples[variant][count][size][repeat]); }
        putch('\n');
        for (unsigned i=0;i<counts[count];++i) {
          puts_uart("ACC_CHAIN_RESULT,");print_uint(variant);putch(',');print_uint(counts[count]);putch(',');print_uint(sizes[size]);putch(',');print_uint(i);
          for (unsigned j=0;j<4;++j) { putch(',');print_uint(chain_results[variant][count][size][i][j]); }
          putch('\n');
        }
      }
  puts_uart("ACC_BENCH_PASS long_samples=");print_uint(long_count);
  puts_uart(" chain_samples=");print_uint(chain_count);puts_uart(" full_128bit_results=1\n");
  return 0;
}
