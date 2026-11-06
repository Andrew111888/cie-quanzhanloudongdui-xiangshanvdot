#include <stdint.h>
#include "console.h"
volatile uint32_t expected_illegal;
static uint32_t rng=20261107u;
static uint32_t next_random(void) { rng^=rng<<13; rng^=rng>>17; rng^=rng<<5; return rng; }
static uint32_t dot(const int8_t *a,const int8_t *b) {
  int32_t s=0;for(unsigned i=0;i<8;++i)s+=(int32_t)a[i]*b[i];return (uint32_t)s;
}
static uint32_t first(const int8_t *a) {
  uint32_t v=0;for(unsigned i=0;i<4;++i)v|=(uint32_t)(uint8_t)a[i]<<(8*i);return v;
}
static int equals(const uint32_t *v,uint32_t want) {return v[0]==want&&!v[1]&&!v[2]&&!v[3];}
#define STR1(x) #x
#define STR(x) STR1(x)
#define ACC(d,a,b) ".word (0x0600000b | (" STR(b) " << 20) | (" STR(a) " << 15) | (" STR(d) " << 7))\n"
int main(void) {
  int8_t a[8][16] __attribute__((aligned(16))),b[16] __attribute__((aligned(16)));
  uint32_t seeds[8][4] __attribute__((aligned(16))),out[12][4] __attribute__((aligned(16)));
  const uint32_t sentinel[4] __attribute__((aligned(16)))={0x89abcdef,0x12345678,0x76543210,0xfedcba98};
  unsigned taken=0;uint32_t checksum=0;
  for(unsigned burst=0;burst<64;++burst) {
    for(unsigned j=0;j<8;++j) {
      for(unsigned i=0;i<16;++i)a[j][i]=(int8_t)next_random();
      for(unsigned i=0;i<4;++i)seeds[j][i]=next_random();
    }
    for(unsigned i=0;i<16;++i)b[i]=(int8_t)next_random();
    __asm__ volatile(
      "vsetivli zero,16,e8,m1,tu,mu\n mv t0,%0\n"
      "vle8.v v8,(t0)\n addi t0,t0,16\n vle8.v v9,(t0)\n addi t0,t0,16\n"
      "vle8.v v10,(t0)\n addi t0,t0,16\n vle8.v v11,(t0)\n addi t0,t0,16\n"
      "vle8.v v12,(t0)\n addi t0,t0,16\n vle8.v v13,(t0)\n addi t0,t0,16\n"
      "vle8.v v14,(t0)\n addi t0,t0,16\n vle8.v v15,(t0)\n"
      "vle8.v v24,(%1)\n mv t0,%2\n"
      "vl1re32.v v16,(t0)\n addi t0,t0,16\n vl1re32.v v17,(t0)\n addi t0,t0,16\n"
      "vl1re32.v v18,(t0)\n addi t0,t0,16\n vl1re32.v v19,(t0)\n addi t0,t0,16\n"
      "vl1re32.v v20,(t0)\n addi t0,t0,16\n vl1re32.v v21,(t0)\n addi t0,t0,16\n"
      "vl1re32.v v22,(t0)\n addi t0,t0,16\n vl1re32.v v23,(t0)\n"
      "vl1re32.v v25,(%3)\n vl1re32.v v26,(%3)\n vl1re32.v v27,(%3)\n"
      "vsetivli zero,8,e8,m1,ta,ma\n"
      ACC(16,8,24) ACC(17,9,24) ACC(18,10,24) ACC(19,11,24)
      ACC(20,12,24) ACC(21,13,24) ACC(22,14,24) ACC(23,15,24)
      "mv t0,%4\n"
      "vs1r.v v16,(t0)\n addi t0,t0,16\n vs1r.v v17,(t0)\n addi t0,t0,16\n"
      "vs1r.v v18,(t0)\n addi t0,t0,16\n vs1r.v v19,(t0)\n addi t0,t0,16\n"
      "vs1r.v v20,(t0)\n addi t0,t0,16\n vs1r.v v21,(t0)\n addi t0,t0,16\n"
      "vs1r.v v22,(t0)\n addi t0,t0,16\n vs1r.v v23,(t0)\n addi t0,t0,16\n"
      "vadd.vv v8,v8,v9\n" ACC(25,8,24)
      "vs1r.v v25,(t0)\n addi t0,t0,16\n"
      ".rept 16\n" ACC(8,8,24) ".endr\n vs1r.v v8,(t0)\n"
      : : "r"(a),"r"(b),"r"(seeds),"r"(sentinel),"r"(out)
      : "t0","memory","v8","v9","v10","v11","v12","v13","v14","v15",
        "v16","v17","v18","v19","v20","v21","v22","v23","v24","v25","v26","v27");
    uint64_t numerator=((uint64_t)next_random()<<32)|next_random(),denominator=next_random()|1u,q;
    __asm__ volatile("divu %0,%1,%2":"=r"(q):"r"(numerator),"r"(denominator));
    if(q&1) {++taken;__asm__ volatile(ACC(26,9,24):::"v26");}
    else __asm__ volatile(ACC(27,9,24):::"v27");
    __asm__ volatile("vs1r.v v26,(%0)\n vs1r.v v27,(%1)"::"r"(out[10]),"r"(out[11]):"memory");
    for(unsigned j=0;j<8;++j)if(!equals(out[j],seeds[j][0]+dot(a[j],b)))return 81;
    int8_t mixed[8],packed[8];for(unsigned i=0;i<8;++i)mixed[i]=(int8_t)((uint8_t)a[0][i]+(uint8_t)a[1][i]);
    uint32_t partial=dot(mixed,b),expect=first(mixed)+partial;
    if(!equals(out[8],sentinel[0]+partial))return 82;
    for(unsigned step=1;step<16;++step) {
      for(unsigned i=0;i<8;++i)packed[i]=i<4?(int8_t)(expect>>(8*i)):0;
      expect+=dot(packed,b);
    }
    if(!equals(out[9],expect))return 83;
    unsigned selected=(q&1)?10:11,untouched=selected==10?11:10;
    if(!equals(out[selected],sentinel[0]+dot(a[1],b)))return 84;
    for(unsigned i=0;i<4;++i)if(out[untouched][i]!=sentinel[i])return 85;
    for(unsigned j=0;j<12;++j)checksum^=out[j][0]+burst*17u+j;
  }
  if(!taken||taken==64)return 86;
  puts_uart("ACC_PIPELINE_PASS bursts=64 acc_instructions=1664 taken=");print_uint(taken);
  puts_uart(" not_taken=");print_uint(64-taken);puts_uart(" checksum=");print_uint(checksum);putch('\n');
  return 0;
}
