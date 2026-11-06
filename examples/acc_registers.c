#include <stdint.h>
#include "console.h"
volatile uint32_t expected_illegal;
static uint32_t dot(const uint32_t *a,const uint32_t *b) {
 const uint8_t *x=(const uint8_t*)a,*y=(const uint8_t*)b;int32_t s=0;
 for(unsigned i=0;i<8;++i)s+=(int32_t)(int8_t)x[i]*(int8_t)y[i];return (uint32_t)s;
}
int main(void) {
 const uint32_t a[4] __attribute__((aligned(16)))={0x7f80ff01,0xff037f80,0x12345678,0xabcdef01};
 const uint32_t b[4] __attribute__((aligned(16)))={0x80ff027f,0x037f80ff,0x87654321,0x10fedcba};
 const uint32_t old[4] __attribute__((aligned(16)))={0x80000004,0xff7f0180,0xdeadbeef,0x76543210};
 uint32_t out[4] __attribute__((aligned(16)));
 for(unsigned policy=0;policy<2;++policy)for(unsigned mode=0;mode<6;++mode) {
  __asm__ volatile("vl1re32.v v1,(%0)\n vl1re32.v v2,(%1)\n vl1re32.v v0,(%2)\n vl1re32.v v31,(%2)"::"r"(a),"r"(b),"r"(old):"memory","v0","v1","v2","v31");
  if(policy)__asm__ volatile("vsetivli zero,8,e8,m1,ta,ma");else __asm__ volatile("vsetivli zero,8,e8,m1,tu,mu");
  uint32_t want;
  switch(mode) {
   case 0:want=old[0]+dot(a,b);__asm__ volatile(".word 0x0620800b\n vmv1r.v v3,v0":::"v0","v3");break;
   case 1:want=old[0]+dot(a,b);__asm__ volatile(".word 0x06208f8b\n vmv1r.v v3,v31":::"v31","v3");break;
   case 2:want=old[0]+dot(old,b);__asm__ volatile(".word 0x062f8f8b\n vmv1r.v v3,v31":::"v31","v3");break;
   case 3:want=old[0]+dot(a,old);__asm__ volatile(".word 0x07f08f8b\n vmv1r.v v3,v31":::"v31","v3");break;
   case 4:want=old[0]+dot(old,b);__asm__ volatile(".word 0x0620000b\n vmv1r.v v3,v0":::"v0","v3");break;
   default:want=old[0]+dot(old,old);__asm__ volatile(".word 0x07ff8f8b\n vmv1r.v v3,v31":::"v31","v3");break;
  }
  __asm__ volatile("vs1r.v v3,(%0)"::"r"(out):"memory");
  if(out[0]!=want||out[1]||out[2]||out[3])return 90+mode;
 }
 puts_uart("ACC_REGISTERS_PASS forms=6 policies=2 v0_v31_and_aliases=1\n");return 0;
}
