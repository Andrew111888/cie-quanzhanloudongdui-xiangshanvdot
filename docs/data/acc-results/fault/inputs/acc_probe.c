#include <stdint.h>
#include "console.h"
volatile uint32_t expected_illegal;
int main(void) {
 const int8_t a[16] __attribute__((aligned(16)))={1,1,1,1,1,1,1,1,11,12,13,14,15,16,17,18};
 const int8_t b[16] __attribute__((aligned(16)))={1,1,1,1,1,1,1,1,-11,-12,-13,-14,-15,-16,-17,-18};
 const uint32_t seed[4] __attribute__((aligned(16)))={0x12345678,0xdeadbeef,0x76543210,0xabcdef01};
 uint32_t out[4] __attribute__((aligned(16)));
 __asm__ volatile("vl1re8.v v8,(%0)\n vl1re8.v v10,(%1)\n vl1re32.v v12,(%2)\n vsetivli zero,8,e8,m1,ta,ma\n .word 0x06a4060b\n vs1r.v v12,(%3)"::"r"(a),"r"(b),"r"(seed),"r"(out):"memory","v8","v10","v12");
 if(out[0]!=0x12345680||out[1]||out[2]||out[3])return 91;
 puts_uart("ACC_PROBE_PASS nonzero_seed=305419896 result=305419904 high96=0\n");return 0;
}
