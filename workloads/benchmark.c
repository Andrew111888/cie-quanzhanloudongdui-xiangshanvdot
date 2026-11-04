#include <stdint.h>
#include "console.h"
volatile uint32_t expected_illegal;

static inline uint64_t cycle(void) {
  uint64_t value;
  // CSRRS is noSpec/blockBack in the pinned Kunminghu V2 decoder.
  __asm__ volatile("fence rw,rw\n csrr %0,cycle" : "=r"(value) : : "memory");
  return value;
}

static uint64_t measure(unsigned n, unsigned baseline, unsigned dependent) {
  uint32_t out[4] __attribute__((aligned(16)));
  __asm__ volatile(
    "vsetivli zero,16,e8,m1,ta,ma\n vmv.v.i v8,1\n vmv.v.i v10,1\n"
    "vsetivli zero,8,e8,m1,ta,ma\n" ::: "memory", "v8", "v10");
  uint64_t begin = cycle();
  for (unsigned i = 0; i < n; ++i) {
    if (baseline) {
      __asm__ volatile(
        "vwmul.vv v16,v8,v10\n"
        "vsetivli zero,4,e32,m1,tu,mu\n vmv.v.i v24,0\n"
        "vsetivli zero,8,e16,m1,tu,mu\n vwredsum.vs v24,v16,v24\n"
        "vsetivli zero,8,e8,m1,ta,ma\n"
        ::: "memory", "v16", "v17", "v24");
      if (dependent) __asm__ volatile("vmv1r.v v8,v24" ::: "v8");
    } else {
      if (dependent) __asm__ volatile(".word 0x02a4040b" ::: "v8");
      else __asm__ volatile(".word 0x02a4060b" ::: "v12");
    }
  }
  // Force completion and make the result observable before the ending CSR.
  if (baseline) __asm__ volatile("vs1r.v v24,(%0)" : : "r"(out) : "memory");
  else if (dependent) __asm__ volatile("vs1r.v v8,(%0)" : : "r"(out) : "memory");
  else __asm__ volatile("vs1r.v v12,(%0)" : : "r"(out) : "memory");
  uint64_t end = cycle();
  // Inputs stay 1; the recurrence reaches 8 and is then stable.
  if (out[0] != 8 || out[1] || out[2] || out[3]) {
    __asm__ volatile("li a0,80\n .word 0x0000006b" ::: "a0", "memory");
  }
  return end - begin;
}

int main(void) {
  const unsigned lengths[] = {32,128,512};
  puts_uart("BENCH_HEADER,dependent,baseline,iterations,repeat,cycles\n");
  for (unsigned dependent = 0; dependent < 2; ++dependent) {
    for (unsigned size = 0; size < 3; ++size) {
      for (unsigned baseline = 0; baseline < 2; ++baseline) {
        (void)measure(lengths[size], baseline, dependent);
        for (unsigned repeat = 0; repeat < 5; ++repeat) {
          uint64_t elapsed = measure(lengths[size], baseline, dependent);
          puts_uart("BENCH,"); print_uint(dependent); putch(',');
          print_uint(baseline); putch(','); print_uint(lengths[size]); putch(',');
          print_uint(repeat); putch(','); print_uint(elapsed); putch('\n');
        }
      }
    }
  }
  puts_uart("BENCH_PASS\n");
  return 0;
}
