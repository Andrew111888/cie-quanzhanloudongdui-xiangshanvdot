#include "VAccVerify.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>

struct Input {
  std::array<uint32_t,4> a,b;
  uint32_t acc;
  uint32_t dot;
  uint32_t fused;
};

static void check(const VlWide<4>& value,uint32_t want,const char* label,unsigned tick) {
  if (value[0]!=want || value[1] || value[2] || value[3]) {
    std::cerr<<"ACC_ARITHMETIC_MISMATCH model="<<label<<" tick="<<tick
             <<" expected_low32="<<std::hex<<want<<" actual128="
             <<std::setfill('0')<<std::setw(8)<<value[3]<<std::setw(8)<<value[2]
             <<std::setw(8)<<value[1]<<std::setw(8)<<value[0]<<std::dec<<"\n";
    throw std::runtime_error(label);
  }
}

int main(int argc,char** argv) {
  Verilated::commandArgs(argc,argv);
  VAccVerify dut;
  std::mt19937 random(20261106);
  const std::array<std::array<int32_t,3>,12> directed={{{1,1,0},{-1,1,0},
    {-128,-128,0},{-128,127,0},{127,127,0},{0,-128,0},{1,1,13},
    {-1,1,INT32_MIN},{1,1,INT32_MAX},{-128,-128,-1},{-128,127,1},{0,-128,-1}}};
  std::vector<Input> inputs;
  for (unsigned i=0;i<directed.size()+4096;++i) {
    Input in{};
    for (unsigned j=0;j<4;++j) { in.a[j]=random();in.b[j]=random(); }
    int32_t sum=0;
    for (unsigned lane=0;lane<8;++lane) {
      int8_t a=(int8_t)random(),b=(int8_t)random();
      if (i<directed.size()) { a=directed[i][0];b=directed[i][1]; }
      unsigned word=lane/4,shift=(lane%4)*8;
      in.a[word]=(in.a[word]&~(uint32_t(255)<<shift))|(uint32_t(uint8_t(a))<<shift);
      in.b[word]=(in.b[word]&~(uint32_t(255)<<shift))|(uint32_t(uint8_t(b))<<shift);
      sum+=int32_t(a)*int32_t(b);
    }
    in.acc=i<directed.size()?uint32_t(directed[i][2]):(i%4==0?0:random());
    in.dot=uint32_t(sum);in.fused=in.acc+in.dot;inputs.push_back(in);
  }
  bool stage_valid=false,output_valid=false;
  uint32_t stage_dot=0,stage_fused=0,out_dot=0,out_fused=0;
  unsigned tick=0,checked=0,captures=0,writes=0,hold_first=0,hold_second=0;
  auto step=[&](const Input& in,bool en1,bool en2) {
    dut.clock=0;dut.enable1=en1;dut.enable2=en2;dut.acc=in.acc;
    for (unsigned j=0;j<4;++j) { dut.vs1[j]=in.a[j];dut.vs2[j]=in.b[j]; }
    dut.eval();
    if (en2 && stage_valid) { out_dot=stage_dot;out_fused=stage_fused;output_valid=true;++writes; }
    if (en1) { stage_dot=in.dot;stage_fused=in.fused;stage_valid=true;++captures; } else ++hold_first;
    if (!en2) ++hold_second;
    dut.clock=1;dut.eval();
    if (output_valid) {
      check(dut.result_plain,out_fused,"plain",tick);
      check(dut.result_csa,out_fused,"csa",tick);
      check(dut.result_prefix,out_fused,"prefix",tick);
      check(dut.result_prefix_or,out_fused,"prefix_or",tick);
      check(dut.result_retimed,out_fused,"retimed",tick);
      check(dut.result_chisel_retimed,out_fused,"chisel_retimed",tick);
      check(dut.result_chisel_prefix,out_fused,"chisel_prefix",tick);
      check(dut.result_chisel_plain,out_fused,"chisel_plain",tick);
      check(dut.result_chisel_csa,out_fused,"chisel_csa",tick);
      check(dut.result_original,out_dot,"original",tick);++checked;
    }
    ++tick;
  };
  try {
    // A continuous stream checks two-edge latency and one accepted group per edge.
    for (const auto& in:inputs) step(in,true,true);
    step(inputs.back(),false,true);
    unsigned continuous_checked=checked;
    if (continuous_checked!=inputs.size()) throw std::runtime_error("continuous check count");
    // Independent enables model stage holding, overwriting and repeated output capture.
    for (const auto& in:inputs) step(in,random()%3!=0,random()%5!=0);
    step(inputs.back(),false,true);
    if (hold_first<100 || hold_second<100) throw std::runtime_error("stall coverage");
    std::cout<<"ACC_ARITHMETIC_PASS directed="<<directed.size()<<" random=4096"
             <<" continuous_checked_each="<<continuous_checked<<" total_checked_each="<<checked
             <<" first_stage_captures="<<captures<<" result_captures="<<writes
             <<" enable1_hold_cycles="<<hold_first<<" enable2_hold_cycles="<<hold_second
             <<" result_bits=128 latency=2 initiation_interval=1 seed=20261106\n";
  } catch(const std::exception& error) {
    std::cerr<<"ACC_ARITHMETIC_FAIL "<<error.what()<<"\n";return 42;
  }
  dut.final();return 0;
}
