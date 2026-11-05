#include <stdint.h>
#include "console.h"

volatile uint32_t expected_illegal;
#define STR1(x) #x
#define STR(x) STR1(x)
#define DOT(d,a,b) ".word (0x0200000b | (" STR(b) " << 20) | (" STR(a) " << 15) | (" STR(d) " << 7))\n"
#define RUN(d,a,b) __asm__ volatile( \
  "vsetivli zero,16,e8,m1,tu,mu\n" \
  "vle8.v v0,(%0)\n vle8.v v31,(%1)\n vmv.v.i v30,-1\n" \
  "vsetivli zero,8,e8,m1,tu,mu\n" DOT(d,a,b) \
  "vs1r.v v" STR(d) ",(%2)\n vs1r.v v0,(%3)\n vs1r.v v31,(%4)\n" \
  : : "r"(a_input), "r"(b_input), "r"(out), "r"(seen0), "r"(seen31) \
  : "memory", "v0", "v30", "v31")

int main(void) {
  const int8_t a_input[16] __attribute__((aligned(16))) =
    {-128,-127,-2,-1,0,1,126,127,23,-45,67,-89,12,-34,56,-78};
  const int8_t b_input[16] __attribute__((aligned(16))) =
    {-128,127,-1,2,3,-4,5,-6,-99,88,-77,66,-55,44,-33,22};
  uint32_t out[4] __attribute__((aligned(16)));
  uint8_t seen0[16] __attribute__((aligned(16)));
  uint8_t seen31[16] __attribute__((aligned(16)));
  for (unsigned mode = 0; mode < 8; ++mode) {
    const int8_t *left = mode == 4 ? b_input : a_input;
    const int8_t *right = mode == 3 || mode == 7 ? a_input : b_input;
    int32_t sum = 0;
    for (unsigned i = 0; i < 8; ++i) sum += (int32_t)left[i] * right[i];
    unsigned destination;
    switch (mode) {
      case 0: RUN(30,0,31); destination = 30; break;
      case 1: RUN(0,0,31); destination = 0; break;
      case 2: RUN(31,0,31); destination = 31; break;
      case 3: RUN(0,0,0); destination = 0; break;
      case 4: RUN(31,31,31); destination = 31; break;
      case 5: RUN(0,31,0); destination = 0; break;
      case 6: RUN(31,31,0); destination = 31; break;
      default: RUN(31,0,0); destination = 31; break;
    }
    uint32_t expected = (uint32_t)sum;
    if (out[0] != expected || out[1] || out[2] || out[3]) return 80 + mode;
    for (unsigned i = 0; i < 16; ++i) {
      uint8_t packed = i < 4 ? (uint8_t)(expected >> (8 * i)) : 0;
      uint8_t want0 = destination == 0 ? packed : (uint8_t)a_input[i];
      uint8_t want31 = destination == 31 ? packed : (uint8_t)b_input[i];
      if (seen0[i] != want0 || seen31[i] != want31) return 90 + mode;
    }
  }
  puts_uart("REGISTER_PASS cases=8 boundary_registers=v0,v31 overlap_and_preservation=checked\n");
  return 0;
}
