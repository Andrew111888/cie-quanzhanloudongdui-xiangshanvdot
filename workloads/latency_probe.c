#include <stdint.h>
#include "console.h"

volatile uint32_t expected_illegal;

/* Named PCs let a waveform follow the arithmetic operations and the required
 * configuration separately. They do not themselves measure cycle counts. */
int main(void) {
  uint32_t baseline[4] __attribute__((aligned(16)));
  uint32_t accelerated[4] __attribute__((aligned(16)));
  __asm__ volatile(
    "vsetivli zero,16,e8,m1,tu,mu\n"
    "vmv.v.i v8,1\n vmv.v.i v10,1\n"
    "vsetivli zero,8,e8,m1,tu,mu\n"
    ".global baseline_latency_begin\n baseline_latency_begin:\n"
    "vwmul.vv v16,v8,v10\n"
    "vsetivli zero,4,e32,m1,tu,mu\n vmv.v.i v12,0\n"
    "vsetivli zero,8,e16,m1,tu,mu\n"
    ".global baseline_latency_reduce\n baseline_latency_reduce:\n"
    "vwredsum.vs v12,v16,v12\n"
    "vsetivli zero,8,e8,m1,tu,mu\n"
    ".global baseline_latency_end\n baseline_latency_end:\n"
    "vs1r.v v12,(%0)\n"
    "vsetivli zero,16,e8,m1,tu,mu\n vmv.v.i v12,-1\n"
    "vsetivli zero,8,e8,m1,tu,mu\n"
    ".global vdot_latency_begin\n vdot_latency_begin:\n"
    ".word 0x02a4060b\n"
    ".global vdot_latency_end\n vdot_latency_end:\n"
    "vs1r.v v12,(%1)\n"
    : : "r"(baseline), "r"(accelerated)
    : "memory", "v8", "v10", "v12", "v16", "v17");
  for (unsigned i = 0; i < 4; ++i) {
    uint32_t expected = i == 0 ? 8 : 0;
    if (baseline[i] != expected || accelerated[i] != expected) return 81;
  }
  puts_uart("LATENCY_PROBE_PASS\n");
  return 0;
}
