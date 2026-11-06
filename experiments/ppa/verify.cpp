#include "VPpaVerify.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <deque>
#include <iostream>
#include <random>
#include <stdexcept>

static uint32_t low(const VlWide<4>& value) {
  if (value[1] || value[2] || value[3]) throw std::runtime_error("upper 96 bits");
  return value[0];
}
int main(int argc,char** argv) {
  Verilated::commandArgs(argc,argv);
  VPpaVerify dut;
  std::mt19937 random(20261106);
  std::deque<uint32_t> expected;
  unsigned accepted=0, stalls=0, checked2=0, checked4=0;
  uint32_t last2=0,last4=0;
  bool initialized2=false,initialized4=false;
  const std::array<std::array<int,2>,6> edges={{{1,1},{-1,1},{-128,-128},{-128,127},{127,127},{0,-128}}};
  try {
    for (unsigned tick=0;tick<2048;++tick) {
      dut.clock=0;
      for (unsigned word=0;word<4;++word) { dut.vs1[word]=random();dut.vs2[word]=random(); }
      int32_t golden=0;
      for (unsigned lane=0;lane<8;++lane) {
        int8_t a=(int8_t)random(),b=(int8_t)random();
        if (accepted<edges.size()) { a=edges[accepted][0];b=edges[accepted][1]; }
        unsigned word=lane/4,shift=(lane%4)*8;
        dut.vs1[word]=(dut.vs1[word]&~(uint32_t(255)<<shift))|(uint32_t(uint8_t(a))<<shift);
        dut.vs2[word]=(dut.vs2[word]&~(uint32_t(255)<<shift))|(uint32_t(uint8_t(b))<<shift);
        golden+=int32_t(a)*int32_t(b);
      }
      dut.enable=tick<16 || random()%5!=0;
      dut.eval();
      dut.clock=1;dut.eval();
      if (dut.enable) {
        expected.push_back(uint32_t(golden));++accepted;
        if (accepted>=2) {
          uint32_t want=expected[expected.size()-2];
          if (low(dut.result2)!=want) throw std::runtime_error("two-stage arithmetic");
          initialized2=true;last2=want;++checked2;
        }
        if (accepted>=4) {
          uint32_t want=expected[expected.size()-4];
          if (low(dut.result4)!=want) throw std::runtime_error("four-stage arithmetic");
          initialized4=true;last4=want;++checked4;
        }
      } else {
        ++stalls;
        if (initialized2 && low(dut.result2)!=last2) throw std::runtime_error("two-stage stall");
        if (initialized4 && low(dut.result4)!=last4) throw std::runtime_error("four-stage stall");
      }
    }
  } catch(const std::exception& e) {
    std::cerr<<"PPA_ARITHMETIC_FAIL "<<e.what()<<" accepted="<<accepted<<"\n";return 1;
  }
  if (accepted<1000 || stalls<100) return 2;
  std::cout<<"PPA_ARITHMETIC_PASS accepted="<<accepted<<" stalls="<<stalls
           <<" checked_two_stage="<<checked2<<" checked_four_stage="<<checked4
           <<" latency2=2 latency4=4 initiation_interval_both=1 seed=20261106\n";
  dut.final();return 0;
}
