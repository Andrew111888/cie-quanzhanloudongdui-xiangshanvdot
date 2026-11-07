#include <stdint.h>
#include "console.h"
volatile uint32_t expected_illegal;
static uint32_t rng=0x1a2b3c4d;
static uint32_t next_random(void){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
static int equals(const uint32_t *v,uint32_t want){return v[0]==want&&!v[1]&&!v[2]&&!v[3];}
#define DOT(d,a,b) ".word (0x0200000b | (" #b " << 20) | (" #a " << 15) | (" #d " << 7))\n"
#define ACC(d,a,b) ".word (0x0600000b | (" #b " << 20) | (" #a " << 15) | (" #d " << 7))\n"
int main(void){
 int8_t a[16] __attribute__((aligned(16))),b[16] __attribute__((aligned(16)));
 const uint32_t zeros[4] __attribute__((aligned(16)))={0},seed[4] __attribute__((aligned(16)))={37,0,0,0};
 const uint32_t sentinel[4] __attribute__((aligned(16)))={0x89abcdef,0x12345678,0x76543210,0xfedcba98};
 uint32_t out[8][4] __attribute__((aligned(16))); unsigned odd=0;uint32_t checksum=0;
 for(unsigned round=0;round<40;++round){
  int32_t dot=0,mixed=0;
  for(unsigned i=0;i<16;++i){a[i]=(int8_t)next_random();b[i]=(int8_t)next_random();if(i<8){dot+=(int32_t)a[i]*b[i];mixed+=(int32_t)(int8_t)(a[i]*b[i])*b[i];}}
  __asm__ volatile(
   "vsetivli zero,8,e8,m1,tu,mu\n vl1re8.v v8,(%0)\n vl1re8.v v9,(%1)\n"
   "vl1re32.v v10,(%2)\n vl1re32.v v13,(%3)\n vl1re32.v v16,(%2)\n"
   ".global control_vmul\n control_vmul:\n vmul.vv v10,v8,v9\n"
   ".global control_dot\n control_dot:\n" DOT(12,10,9)
   ".global control_vwmacc\n control_vwmacc:\n vwmacc.vv v16,v8,v9\n"
   ".global control_acc\n control_acc:\n" ACC(13,8,9)
   ".global control_alias\n control_alias:\n" ACC(12,12,9)
   "vs1r.v v10,(%4)\n vs1r.v v12,(%5)\n vs1r.v v13,(%6)\n vs1r.v v16,(%7)\n"
   ::"r"(a),"r"(b),"r"(zeros),"r"(seed),"r"(out[0]),"r"(out[1]),"r"(out[2]),"r"(out[3])
   :"memory","v8","v9","v10","v12","v13","v16","v17");
  int32_t alias_dot=0;for(unsigned i=0;i<4;++i)alias_dot+=(int32_t)(int8_t)((uint32_t)mixed>>(8*i))*b[i];
  if(!equals(out[1],(uint32_t)mixed+alias_dot)||!equals(out[2],37u+dot))return 71;
  for(unsigned i=0;i<16;++i)if(((int8_t*)out[0])[i]!=(i<8?(int8_t)(a[i]*b[i]):0))return 72;
  for(unsigned i=0;i<8;++i)if(((int16_t*)out[3])[i]!=(int16_t)(a[i]*b[i]))return 73;
  uint64_t numerator=((uint64_t)next_random()<<32)|next_random(),denominator=(next_random()&65535)|1u,q;
  __asm__ volatile(
   "vl1re32.v v26,(%3)\n vl1re32.v v27,(%3)\n vl1re32.v v28,(%3)\n vl1re32.v v29,(%3)\n"
   ".global control_div\n control_div:\n divu %0,%1,%2\n andi t0,%0,1\n"
   ".global control_branch\n control_branch:\n beqz t0,1f\n"
   ".global control_taken_acc\n control_taken_acc:\n" ACC(26,8,9)
   ".global control_taken_dot\n control_taken_dot:\n" DOT(28,8,9)
   "j 2f\n 1:\n"
   ".global control_other_acc\n control_other_acc:\n" ACC(27,8,9)
   ".global control_other_dot\n control_other_dot:\n" DOT(29,8,9)
   "2:\n vs1r.v v26,(%4)\n vs1r.v v27,(%5)\n vs1r.v v28,(%6)\n vs1r.v v29,(%7)\n"
   :"=&r"(q):"r"(numerator),"r"(denominator),"r"(sentinel),"r"(out[4]),"r"(out[5]),"r"(out[6]),"r"(out[7])
   :"t0","memory","v26","v27","v28","v29");
  unsigned selected=(q&1)?4:5,other=selected==4?5:4;odd+=(q&1);
  if(!equals(out[selected],sentinel[0]+dot)||!equals(out[selected+2],(uint32_t)dot))return 74;
  for(unsigned i=0;i<4;++i)if(out[other][i]!=sentinel[i]||out[other+2][i]!=sentinel[i])return 75;
  for(unsigned i=0;i<8;++i)checksum^=out[i][0]+round*17u+i;
 }
 if(!odd||odd==40)return 76;
 puts_uart("VDOT_CONTROL_PASS rounds=40 custom_committed=200 standard_mac_committed=80 odd=");print_uint(odd);
 puts_uart(" even=");print_uint(40-odd);puts_uart(" checksum=");print_uint(checksum);putch('\n');return 0;
}
