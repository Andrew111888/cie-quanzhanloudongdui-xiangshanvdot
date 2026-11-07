#include "VIsolationCompare.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <cstdio>
#include <deque>
#include <random>
#include <stdexcept>
#include <string>
struct Item { uint32_t tag; bool dot; std::array<uint32_t,4> result; };
struct Count { uint64_t products=0,stage1=0,result=0; };
static void require(bool x,const char *m) { if(!x) throw std::runtime_error(m); }
static uint64_t bits(uint32_t a,uint32_t b) { return __builtin_popcount(a^b); }
int main(int argc,char **argv) {
 Verilated::commandArgs(argc,argv);
 try {
 for(unsigned mode=0;mode<4;++mode) {
  VIsolationCompare d;std::mt19937 rng(20261107+mode);std::deque<Item> queue;
  Count counts[2];std::array<uint32_t,4> prevp[2]{};std::array<uint32_t,6> prevs[2]{};uint32_t prevr[2]{};
  uint64_t accepted=0,checked=0,dots=0,killed=0,stall=0,flushes=0,issued=0;
  bool held=false;
  uint64_t enable_patterns[4]{};
  d.clock=0;d.reset=1;d.flush=0;d.in_valid=0;d.out_ready=0;d.eval();d.clock=1;d.eval();d.clock=0;d.reset=0;d.eval();
  auto sample=[&]() {
    for(unsigned j=0;j<2;++j) {
      auto &p=j?d.isolated_products:d.baseline_products;auto &s=j?d.isolated_stage1:d.baseline_stage1;
      uint32_t r=j?d.isolated_dot_result:d.baseline_dot_result;
      for(unsigned k=0;k<4;++k) {counts[j].products+=bits(prevp[j][k],p[k]);prevp[j][k]=p[k];}
      for(unsigned k=0;k<6;++k) {counts[j].stage1+=bits(prevs[j][k],s[k]);prevs[j][k]=s[k];}
      counts[j].result+=bits(prevr[j],r);prevr[j]=r;
    }
  };
  for(unsigned cycle=0;cycle<12008;++cycle) {
    bool drain=cycle>=12000;
    d.out_ready=drain || mode==0 || (cycle%47>=7 && rng()%5!=0);
    d.flush=mode!=0 && !drain && cycle>0 && cycle%997==0;
    if (!held) {
      d.in_valid=!drain && (mode==0 || rng()%5!=0);
      d.in_dot=mode<=1 ? 1 : mode==2 ? (rng()%4==0) : (cycle%256<16);
      d.in_acc=rng()&1;d.acc=rng();d.in_tag=++issued;
      for(unsigned k=0;k<4;++k) {d.vs1[k]=rng();d.vs2[k]=rng();}
      // Directed initial transactions: 0, +1, -1, min/min, min/max, max/max.
      if (issued<=12 && d.in_valid) {
        const uint32_t words[]={0,0x01010101u,0xffffffffu,0x80808080u,0x80808080u,0x7f7f7f7fu};
        const uint32_t rhs[]={0,0x01010101u,0x01010101u,0x80808080u,0x7f7f7f7fu,0x7f7f7f7fu};
        unsigned n=(issued-1)%6;
        for(unsigned k=0;k<4;++k) {d.vs1[k]=words[n];d.vs2[k]=rhs[n];}
        d.in_dot=1;d.in_acc=issued>6;d.acc=0x7fffffffu;
      }
    }
    std::array<uint8_t,16>a{},b{};
    for(unsigned k=0;k<4;++k) for(unsigned j=0;j<4;++j) {a[k*4+j]=d.vs1[k]>>(j*8);b[k*4+j]=d.vs2[k]>>(j*8);}
    d.eval();sample();
    if(d.flush) {killed+=queue.size();queue.clear();++flushes;}
    else {
      if(d.out_valid) {
        require(!queue.empty(),"unexpected output");const auto &want=queue.front();
        require(d.out_tag==want.tag && bool(d.out_dot)==want.dot,"tag/order mismatch");
        for(unsigned k=0;k<4;++k) require(d.baseline_result[k]==want.result[k] && d.isolated_result[k]==want.result[k],"golden/result mismatch");
        if(d.out_ready) {queue.pop_front();++checked;} else ++stall;
      }
      if(d.in_valid&&d.in_ready) {
        Item item{};item.tag=d.in_tag;item.dot=d.in_dot;
        if(item.dot) {int32_t total=0;for(unsigned k=0;k<8;++k)total+=int32_t(int8_t(a[k]))*int32_t(int8_t(b[k]));item.result[0]=uint32_t(total)+(d.in_acc?uint32_t(d.acc):0u);++dots;}
        else for(unsigned k=0;k<16;++k)item.result[k/4]|=uint32_t(uint8_t(unsigned(a[k])*unsigned(b[k])))<<((k%4)*8);
        queue.push_back(item);++accepted;
      }
    }
    unsigned enable_pattern=(d.isolated_enable1?1:0)|(d.isolated_enable2?2:0);
    ++enable_patterns[enable_pattern];
    std::array<uint32_t,6> before_stage1{};
    for(unsigned k=0;k<6;++k)before_stage1[k]=d.isolated_stage1[k];
    uint32_t before_result=d.isolated_dot_result;
    held=d.in_valid && !d.in_ready && !d.flush;
    d.clock=1;d.eval();sample();
    if(!(enable_pattern&1))for(unsigned k=0;k<6;++k)require(d.isolated_stage1[k]==before_stage1[k],"stage1 hold violation");
    if(!(enable_pattern&2))require(d.isolated_dot_result==before_result,"stage2 hold violation");
    d.clock=0;d.eval();
  }
  require(queue.empty(),"failed to drain");require(accepted==checked+killed,"accepted conservation");if(mode!=0) require(stall>0 && killed>0,"missing stall/flush coverage");
  if(mode==0) require(accepted==12000 && checked==12000 && killed==0,"continuous-dot throughput");
  for(unsigned p=0;p<4;++p) require(enable_patterns[p]>0,"missing independent enable pattern");
  printf("ISOLATION_PASS mode=%u accepted=%llu dots=%llu checked=%llu killed=%llu stall_cycles=%llu flushes=%llu baseline_products=%llu isolated_products=%llu baseline_stage1=%llu isolated_stage1=%llu baseline_result=%llu isolated_result=%llu enable00=%llu enable10=%llu enable01=%llu enable11=%llu\n",mode,(unsigned long long)accepted,(unsigned long long)dots,(unsigned long long)checked,(unsigned long long)killed,(unsigned long long)stall,(unsigned long long)flushes,(unsigned long long)counts[0].products,(unsigned long long)counts[1].products,(unsigned long long)counts[0].stage1,(unsigned long long)counts[1].stage1,(unsigned long long)counts[0].result,(unsigned long long)counts[1].result,(unsigned long long)enable_patterns[0],(unsigned long long)enable_patterns[1],(unsigned long long)enable_patterns[2],(unsigned long long)enable_patterns[3]);
  d.final();
 }
 }catch(const std::exception &e){fprintf(stderr,"ISOLATION_FAIL %s\n",e.what());return 1;}
 return 0;
}
